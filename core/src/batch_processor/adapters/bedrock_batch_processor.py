"""Bedrock batch processor adapter using aioboto3."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import aioboto3

from ..exceptions import (
    BatchJobCancelledError,
    BatchJobNotFoundError,
    ProviderAPIError,
)
from ..models import BatchJob, BatchJobStatus, BatchProvider, BatchRequest, BatchResult
from .base_batch_processor import BaseBatchProcessor

logger = logging.getLogger(__name__)


class BedrockBatchProcessor(BaseBatchProcessor):
    """Batch processor implementation for AWS Bedrock."""

    def __init__(
        self,
        region: str,
        s3_bucket: str,
        role_arn: str,
        s3_input_prefix: str = "batch-inputs",
        s3_output_prefix: str = "batch-outputs",
    ):
        """Initialize the Bedrock batch processor.

        Args:
            region: AWS region for Bedrock and S3.
            s3_bucket: S3 bucket for input/output files.
            role_arn: IAM role ARN for Bedrock batch inference.
            s3_input_prefix: S3 prefix for input files.
            s3_output_prefix: S3 prefix for output files.
        """
        self.region = region
        self.s3_bucket = s3_bucket
        self.role_arn = role_arn
        self.s3_input_prefix = s3_input_prefix
        self.s3_output_prefix = s3_output_prefix
        self._provider = BatchProvider.BEDROCK
        self._session = aioboto3.Session()

    def _map_status(self, bedrock_status: str) -> BatchJobStatus:
        """Map Bedrock job status to BatchJobStatus.

        Args:
            bedrock_status: Status string from Bedrock API.

        Returns:
            Corresponding BatchJobStatus enum value.
        """
        mapping = {
            "Submitted": BatchJobStatus.PENDING,
            "InProgress": BatchJobStatus.PROCESSING,
            "Completed": BatchJobStatus.COMPLETED,
            "Failed": BatchJobStatus.FAILED,
            "Stopping": BatchJobStatus.PROCESSING,
            "Stopped": BatchJobStatus.CANCELLED,
            "PartiallyCompleted": BatchJobStatus.COMPLETED,
            "Expired": BatchJobStatus.FAILED,
            "Validating": BatchJobStatus.PENDING,
            "Scheduled": BatchJobStatus.PENDING,
        }
        return mapping.get(bedrock_status, BatchJobStatus.PENDING)

    def _get_inference_profile_id(self, model_id: str) -> str:
        """Convert a model ID to an inference profile ID if required.

        Many newer Bedrock models require using inference profiles for batch
        inference instead of direct model IDs. This includes newer models from
        Anthropic, Meta, Amazon, and other providers.

        Args:
            model_id: The original model ID (e.g., 'anthropic.claude-3-5-haiku-20241022-v1:0').

        Returns:
            The inference profile ID (e.g., 'us.anthropic.claude-3-5-haiku-20241022-v1:0')
            or the original model_id if no conversion is needed.
        """
        # If already an inference profile ID (starts with 'us.' or 'global.'), return as-is
        if model_id.startswith("us.") or model_id.startswith("global."):
            return model_id

        # Model prefixes that require inference profiles for batch inference
        # These models don't support on-demand throughput for batch jobs
        # Based on AWS Bedrock inference profiles list
        inference_profile_models = [
            # Anthropic Claude models (3.5+, 3.7, 4.x)
            "anthropic.claude-3-5-haiku",
            "anthropic.claude-3-5-sonnet",
            "anthropic.claude-3-7-sonnet",
            "anthropic.claude-sonnet-4",
            "anthropic.claude-opus-4",
            "anthropic.claude-haiku-4",
            # Meta Llama models (3.1+, 3.2, 3.3, 4.x)
            "meta.llama3-1",
            "meta.llama3-2",
            "meta.llama3-3",
            "meta.llama4",
            # Amazon Nova models
            "amazon.nova-micro",
            "amazon.nova-lite",
            "amazon.nova-pro",
            "amazon.nova-premier",
            "amazon.nova-2",
            # DeepSeek
            "deepseek.r1",
            # Mistral
            "mistral.pixtral",
            # Cohere
            "cohere.embed-v4",
            # Writer
            "writer.palmyra-x4",
            "writer.palmyra-x5",
        ]

        # Check if this model requires an inference profile
        for prefix in inference_profile_models:
            if model_id.startswith(prefix):
                # Convert to US regional inference profile
                inference_profile_id = f"us.{model_id}"
                return inference_profile_id

        # Return original model_id for models that support direct invocation
        # (e.g., older Claude 3 models like claude-3-haiku-20240307-v1:0)
        return model_id

    def _parse_s3_uri(self, uri: str) -> tuple[str, str]:
        """Parse S3 URI into bucket and key.

        Args:
            uri: S3 URI in format s3://bucket/key.

        Returns:
            Tuple of (bucket, key).
        """
        if not uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI: {uri}")
        path = uri[5:]  # Remove 's3://'
        parts = path.split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        return bucket, key

    async def _upload_to_s3(self, content: str, key: str) -> str:
        """Upload content to S3.

        Args:
            content: Content to upload.
            key: S3 key for the object.

        Returns:
            S3 URI of the uploaded object.
        """
        async with self._session.client("s3", region_name=self.region) as s3:
            await s3.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=content.encode("utf-8"),
                ContentType="application/jsonl",
            )
        return f"s3://{self.s3_bucket}/{key}"

    async def _download_from_s3(self, bucket: str, key: str) -> str:
        """Download content from S3.

        Args:
            bucket: S3 bucket name.
            key: S3 object key.

        Returns:
            Content as string.
        """
        async with self._session.client("s3", region_name=self.region) as s3:
            response = await s3.get_object(Bucket=bucket, Key=key)
            async with response["Body"] as stream:
                content = await stream.read()
                return content.decode("utf-8")

    async def _list_s3_objects(self, bucket: str, prefix: str) -> list[str]:
        """List objects in S3 with given prefix.

        Args:
            bucket: S3 bucket name.
            prefix: S3 prefix to filter objects.

        Returns:
            List of object keys.
        """
        keys: list[str] = []
        async with self._session.client("s3", region_name=self.region) as s3:
            paginator = s3.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    keys.append(obj["Key"])
        return keys

    def _build_bedrock_request(self, request: BatchRequest) -> dict[str, Any]:
        """Build Bedrock batch request format.

        Args:
            request: BatchRequest to convert.

        Returns:
            Dictionary in Bedrock JSONL format.
        """
        model_input: dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": request.max_tokens,
            "messages": request.messages,
        }

        if request.system:
            model_input["system"] = request.system
        if request.temperature is not None:
            model_input["temperature"] = request.temperature
        if request.top_p is not None:
            model_input["top_p"] = request.top_p

        return {
            "recordId": request.custom_id,
            "modelInput": model_input,
        }

    def _job_response_to_batch_job(self, response: dict[str, Any]) -> BatchJob:
        """Convert Bedrock job response to BatchJob.

        Args:
            response: Bedrock API response.

        Returns:
            BatchJob model instance.
        """
        status = self._map_status(response.get("status", "Unknown"))

        # Parse timestamps
        created_at = response.get("submitTime", datetime.now(timezone.utc))
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        completed_at = None
        if "endTime" in response and response["endTime"]:
            end_time = response["endTime"]
            if isinstance(end_time, str):
                completed_at = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            else:
                completed_at = end_time

        # Extract job ID from ARN
        job_arn = response.get("jobArn", "")
        job_id = job_arn.split("/")[-1] if "/" in job_arn else job_arn

        return BatchJob(
            job_id=job_arn,  # Use full ARN as job_id for Bedrock
            provider=self._provider,
            status=status,
            created_at=created_at,
            completed_at=completed_at,
            request_count=response.get("inputDataConfig", {}).get("s3InputDataConfig", {}).get("s3InputFormat", 0),
            metadata={
                "model_id": response.get("modelId"),
                "output_uri": response.get("outputDataConfig", {}).get("s3OutputDataConfig", {}).get("s3Uri"),
            },
            error_message=response.get("message") if status == BatchJobStatus.FAILED else None,
        )

    async def create_batch(
        self,
        requests: list[BatchRequest],
        metadata: dict | None = None,
    ) -> BatchJob:
        """Create a new batch job using Bedrock API.

        Args:
            requests: List of batch requests to process.
            metadata: Optional metadata containing 'model_id' for the batch.

        Returns:
            BatchJob with job_id and initial status.

        Raises:
            ProviderAPIError: If the Bedrock API call fails.
        """
        try:
            logger.info(f"Creating Bedrock batch with {len(requests)} requests")

            # Get model_id from metadata or first request
            model_id = None
            if metadata and "model_id" in metadata:
                model_id = metadata["model_id"]
            elif requests:
                model_id = requests[0].model

            if not model_id:
                raise ValueError("model_id must be provided in metadata or requests")

            # Convert model ID to inference profile ID for models that require it
            # Claude 3.5+ models require using inference profiles for batch inference
            model_id = self._get_inference_profile_id(model_id)

            # Generate unique job name and timestamp
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            job_name = f"batch-{timestamp}-{uuid.uuid4().hex[:8]}"

            # Convert requests to JSONL format
            jsonl_lines = [json.dumps(self._build_bedrock_request(req)) for req in requests]
            jsonl_content = "\n".join(jsonl_lines)

            # Upload input file to S3
            input_key = f"{self.s3_input_prefix}/{job_name}.jsonl"
            input_uri = await self._upload_to_s3(jsonl_content, input_key)
            logger.debug(f"Uploaded input file to {input_uri}")

            # Create output location
            output_uri = f"s3://{self.s3_bucket}/{self.s3_output_prefix}/{job_name}/"

            # Create batch inference job
            async with self._session.client("bedrock", region_name=self.region) as bedrock:
                response = await bedrock.create_model_invocation_job(
                    jobName=job_name,
                    modelId=model_id,
                    roleArn=self.role_arn,
                    inputDataConfig={
                        "s3InputDataConfig": {
                            "s3Uri": input_uri,
                            "s3InputFormat": "JSONL",
                        }
                    },
                    outputDataConfig={
                        "s3OutputDataConfig": {
                            "s3Uri": output_uri,
                        }
                    },
                )

            job = BatchJob(
                job_id=response["jobArn"],
                provider=self._provider,
                status=BatchJobStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                completed_at=None,
                request_count=len(requests),
                metadata={
                    "model_id": model_id,
                    "input_uri": input_uri,
                    "output_uri": output_uri,
                },
            )

            logger.info(f"Created Bedrock batch job: {job.job_id}")
            return job

        except Exception as e:
            logger.error(f"Bedrock API error during batch creation: {e}")
            raise ProviderAPIError(
                provider="bedrock",
                operation="create_batch",
                original_error=e,
            ) from e

    async def get_batch_status(self, job_id: str) -> BatchJob:
        """Get the current status of a batch job.

        Args:
            job_id: The Bedrock job ARN.

        Returns:
            BatchJob with current status.

        Raises:
            BatchJobNotFoundError: If the job does not exist.
            ProviderAPIError: If the Bedrock API call fails.
        """
        try:
            logger.debug(f"Getting status for Bedrock batch: {job_id}")

            async with self._session.client("bedrock", region_name=self.region) as bedrock:
                response = await bedrock.get_model_invocation_job(jobIdentifier=job_id)

            return self._job_response_to_batch_job(response)

        except Exception as e:
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                logger.warning(f"Bedrock batch not found: {job_id}")
                raise BatchJobNotFoundError(job_id) from e
            logger.error(f"Bedrock API error during status retrieval: {e}")
            raise ProviderAPIError(
                provider="bedrock",
                operation="get_batch_status",
                original_error=e,
            ) from e

    async def get_batch_results(
        self,
        job_id: str,
        limit: int | None = None,
    ) -> list[BatchResult]:
        """Retrieve results from a completed batch job.

        Args:
            job_id: The Bedrock job ARN.
            limit: Optional maximum number of results to return.

        Returns:
            List of BatchResult objects.

        Raises:
            BatchJobNotFoundError: If the job does not exist.
            BatchJobCancelledError: If the job was cancelled.
            ProviderAPIError: If the Bedrock API call fails.
        """
        try:
            logger.debug(f"Getting results for Bedrock batch: {job_id}")

            # Get job details to find output location
            async with self._session.client("bedrock", region_name=self.region) as bedrock:
                response = await bedrock.get_model_invocation_job(jobIdentifier=job_id)

            status = self._map_status(response.get("status", "Unknown"))

            if status == BatchJobStatus.CANCELLED:
                raise BatchJobCancelledError(job_id)

            # Get output URI
            output_uri = response.get("outputDataConfig", {}).get("s3OutputDataConfig", {}).get("s3Uri", "")
            if not output_uri:
                logger.warning(f"No output URI found for job: {job_id}")
                return []

            # Parse output location
            bucket, prefix = self._parse_s3_uri(output_uri)

            # List output files
            output_keys = await self._list_s3_objects(bucket, prefix)

            results: list[BatchResult] = []
            count = 0

            for key in output_keys:
                if limit and count >= limit:
                    break

                # Skip non-JSONL files
                if not key.endswith(".jsonl.out"):
                    continue

                # Download and parse output file
                content = await self._download_from_s3(bucket, key)

                for line in content.strip().split("\n"):
                    if limit and count >= limit:
                        break

                    if not line:
                        continue

                    try:
                        record = json.loads(line)
                        record_id = record.get("recordId", "")
                        model_output = record.get("modelOutput", {})
                        error = record.get("error")

                        if error:
                            results.append(
                                BatchResult(
                                    custom_id=record_id,
                                    success=False,
                                    response=None,
                                    error=str(error),
                                )
                            )
                        else:
                            # Parse model output (Anthropic format in Bedrock)
                            if isinstance(model_output, str):
                                model_output = json.loads(model_output)

                            results.append(
                                BatchResult(
                                    custom_id=record_id,
                                    success=True,
                                    response=model_output,
                                    error=None,
                                )
                            )
                        count += 1

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse result line: {e}")
                        continue

            logger.info(f"Retrieved {len(results)} results from Bedrock batch: {job_id}")
            return results

        except BatchJobCancelledError:
            raise
        except Exception as e:
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                logger.warning(f"Bedrock batch not found: {job_id}")
                raise BatchJobNotFoundError(job_id) from e
            logger.error(f"Bedrock API error during results retrieval: {e}")
            raise ProviderAPIError(
                provider="bedrock",
                operation="get_batch_results",
                original_error=e,
            ) from e

    async def cancel_batch(self, job_id: str) -> bool:
        """Cancel a running batch job.

        Args:
            job_id: The Bedrock job ARN.

        Returns:
            True if cancellation was successful.

        Raises:
            BatchJobNotFoundError: If the job does not exist.
            ProviderAPIError: If the Bedrock API call fails.
        """
        try:
            logger.info(f"Cancelling Bedrock batch: {job_id}")

            async with self._session.client("bedrock", region_name=self.region) as bedrock:
                await bedrock.stop_model_invocation_job(jobIdentifier=job_id)

            logger.info(f"Successfully cancelled Bedrock batch: {job_id}")
            return True

        except Exception as e:
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                logger.warning(f"Bedrock batch not found: {job_id}")
                raise BatchJobNotFoundError(job_id) from e
            logger.error(f"Bedrock API error during batch cancellation: {e}")
            raise ProviderAPIError(
                provider="bedrock",
                operation="cancel_batch",
                original_error=e,
            ) from e

    async def list_batches(
        self,
        status: BatchJobStatus | None = None,
        limit: int = 100,
    ) -> list[BatchJob]:
        """List batch jobs with optional status filter.

        Note: Bedrock API supports listing jobs via list_model_invocation_jobs.

        Args:
            status: Optional status to filter by.
            limit: Maximum number of jobs to return.

        Returns:
            List of BatchJob objects.

        Raises:
            ProviderAPIError: If the Bedrock API call fails.
        """
        try:
            logger.debug(f"Listing Bedrock batches (limit={limit}, status={status})")

            jobs: list[BatchJob] = []

            # Map BatchJobStatus to Bedrock status filter
            status_filter = None
            if status:
                reverse_mapping = {
                    BatchJobStatus.PENDING: "Submitted",
                    BatchJobStatus.PROCESSING: "InProgress",
                    BatchJobStatus.COMPLETED: "Completed",
                    BatchJobStatus.FAILED: "Failed",
                    BatchJobStatus.CANCELLED: "Stopped",
                }
                status_filter = reverse_mapping.get(status)

            async with self._session.client("bedrock", region_name=self.region) as bedrock:
                params: dict[str, Any] = {"maxResults": min(limit, 100)}
                if status_filter:
                    params["statusEquals"] = status_filter

                response = await bedrock.list_model_invocation_jobs(**params)

                for job_summary in response.get("invocationJobSummaries", []):
                    if len(jobs) >= limit:
                        break

                    # Get full job details
                    job_arn = job_summary.get("jobArn", "")
                    try:
                        job_details = await bedrock.get_model_invocation_job(jobIdentifier=job_arn)
                        jobs.append(self._job_response_to_batch_job(job_details))
                    except Exception as e:
                        logger.warning(f"Failed to get details for job {job_arn}: {e}")
                        continue

            logger.info(f"Listed {len(jobs)} Bedrock batches")
            return jobs

        except Exception as e:
            logger.error(f"Bedrock API error during batch listing: {e}")
            raise ProviderAPIError(
                provider="bedrock",
                operation="list_batches",
                original_error=e,
            ) from e
