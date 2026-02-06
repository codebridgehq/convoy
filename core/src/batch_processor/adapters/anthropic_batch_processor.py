"""Anthropic batch processor adapter."""

import logging
from datetime import datetime, timezone
from typing import Any

import anthropic

from ..exceptions import (
    BatchJobCancelledError,
    BatchJobNotFoundError,
    ProviderAPIError,
)
from ..models import BatchJob, BatchJobStatus, BatchProvider, BatchRequest, BatchResult
from .base_batch_processor import BaseBatchProcessor

logger = logging.getLogger(__name__)


class AnthropicBatchProcessor(BaseBatchProcessor):
    """Batch processor implementation for Anthropic API."""

    def __init__(self, api_key: str):
        """Initialize the Anthropic batch processor.

        Args:
            api_key: Anthropic API key.
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self._provider = BatchProvider.ANTHROPIC

    def _map_status(self, anthropic_status: str) -> BatchJobStatus:
        """Map Anthropic batch status to BatchJobStatus.

        Args:
            anthropic_status: Status string from Anthropic API.

        Returns:
            Corresponding BatchJobStatus enum value.
        """
        mapping = {
            "in_progress": BatchJobStatus.PROCESSING,
            "ended": BatchJobStatus.COMPLETED,
            "canceling": BatchJobStatus.PROCESSING,
            "canceled": BatchJobStatus.CANCELLED,
        }
        return mapping.get(anthropic_status, BatchJobStatus.PENDING)

    def _build_batch_request(self, request: BatchRequest) -> dict[str, Any]:
        """Build Anthropic batch request format.

        Args:
            request: BatchRequest to convert.

        Returns:
            Dictionary in Anthropic batch request format.
        """
        params: dict[str, Any] = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "messages": request.messages,
        }

        if request.system:
            params["system"] = request.system
        if request.temperature is not None:
            params["temperature"] = request.temperature
        if request.top_p is not None:
            params["top_p"] = request.top_p

        return {
            "custom_id": request.custom_id,
            "params": params,
        }

    def _batch_to_job(self, batch: Any) -> BatchJob:
        """Convert Anthropic batch response to BatchJob.

        Args:
            batch: Anthropic batch object.

        Returns:
            BatchJob model instance.
        """
        status = self._map_status(batch.processing_status)

        # Parse timestamps
        created_at = datetime.fromisoformat(batch.created_at.replace("Z", "+00:00"))
        completed_at = None
        if hasattr(batch, "ended_at") and batch.ended_at:
            completed_at = datetime.fromisoformat(batch.ended_at.replace("Z", "+00:00"))

        return BatchJob(
            job_id=batch.id,
            provider=self._provider,
            status=status,
            created_at=created_at,
            completed_at=completed_at,
            request_count=batch.request_counts.total if hasattr(batch, "request_counts") else 0,
            metadata=None,
        )

    async def create_batch(
        self,
        requests: list[BatchRequest],
        metadata: dict | None = None,
    ) -> BatchJob:
        """Create a new batch job using Anthropic API.

        Args:
            requests: List of batch requests to process.
            metadata: Optional metadata (not used by Anthropic).

        Returns:
            BatchJob with job_id and initial status.

        Raises:
            ProviderAPIError: If the Anthropic API call fails.
        """
        try:
            logger.info(f"Creating Anthropic batch with {len(requests)} requests")

            batch_requests = [self._build_batch_request(req) for req in requests]

            batch = self.client.beta.messages.batches.create(requests=batch_requests)

            job = self._batch_to_job(batch)
            logger.info(f"Created Anthropic batch job: {job.job_id}")
            return job

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error during batch creation: {e}")
            raise ProviderAPIError(
                provider="anthropic",
                operation="create_batch",
                original_error=e,
            ) from e

    async def get_batch_status(self, job_id: str) -> BatchJob:
        """Get the current status of a batch job.

        Args:
            job_id: The Anthropic batch ID.

        Returns:
            BatchJob with current status.

        Raises:
            BatchJobNotFoundError: If the batch does not exist.
            ProviderAPIError: If the Anthropic API call fails.
        """
        try:
            logger.debug(f"Getting status for Anthropic batch: {job_id}")

            batch = self.client.beta.messages.batches.retrieve(job_id)
            return self._batch_to_job(batch)

        except anthropic.NotFoundError as e:
            logger.warning(f"Anthropic batch not found: {job_id}")
            raise BatchJobNotFoundError(job_id) from e
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error during status retrieval: {e}")
            raise ProviderAPIError(
                provider="anthropic",
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
            job_id: The Anthropic batch ID.
            limit: Optional maximum number of results to return.

        Returns:
            List of BatchResult objects.

        Raises:
            BatchJobNotFoundError: If the batch does not exist.
            BatchJobCancelledError: If the batch was cancelled.
            ProviderAPIError: If the Anthropic API call fails.
        """
        try:
            logger.debug(f"Getting results for Anthropic batch: {job_id}")

            # First check the batch status
            batch = self.client.beta.messages.batches.retrieve(job_id)
            status = self._map_status(batch.processing_status)

            if status == BatchJobStatus.CANCELLED:
                raise BatchJobCancelledError(job_id)

            results: list[BatchResult] = []
            count = 0

            for result in self.client.beta.messages.batches.results(job_id):
                if limit and count >= limit:
                    break

                if result.result.type == "succeeded":
                    # Extract response content
                    response_data = {
                        "id": result.result.message.id,
                        "type": result.result.message.type,
                        "role": result.result.message.role,
                        "content": [
                            {"type": block.type, "text": block.text}
                            for block in result.result.message.content
                            if hasattr(block, "text")
                        ],
                        "model": result.result.message.model,
                        "stop_reason": result.result.message.stop_reason,
                        "usage": {
                            "input_tokens": result.result.message.usage.input_tokens,
                            "output_tokens": result.result.message.usage.output_tokens,
                        },
                    }
                    results.append(
                        BatchResult(
                            custom_id=result.custom_id,
                            success=True,
                            response=response_data,
                            error=None,
                        )
                    )
                else:
                    # Handle error result
                    error_msg = str(result.result.error) if hasattr(result.result, "error") else "Unknown error"
                    results.append(
                        BatchResult(
                            custom_id=result.custom_id,
                            success=False,
                            response=None,
                            error=error_msg,
                        )
                    )

                count += 1

            logger.info(f"Retrieved {len(results)} results from Anthropic batch: {job_id}")
            return results

        except anthropic.NotFoundError as e:
            logger.warning(f"Anthropic batch not found: {job_id}")
            raise BatchJobNotFoundError(job_id) from e
        except BatchJobCancelledError:
            raise
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error during results retrieval: {e}")
            raise ProviderAPIError(
                provider="anthropic",
                operation="get_batch_results",
                original_error=e,
            ) from e

    async def cancel_batch(self, job_id: str) -> bool:
        """Cancel a running batch job.

        Args:
            job_id: The Anthropic batch ID.

        Returns:
            True if cancellation was successful.

        Raises:
            BatchJobNotFoundError: If the batch does not exist.
            ProviderAPIError: If the Anthropic API call fails.
        """
        try:
            logger.info(f"Cancelling Anthropic batch: {job_id}")

            self.client.beta.messages.batches.cancel(job_id)
            logger.info(f"Successfully cancelled Anthropic batch: {job_id}")
            return True

        except anthropic.NotFoundError as e:
            logger.warning(f"Anthropic batch not found: {job_id}")
            raise BatchJobNotFoundError(job_id) from e
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error during batch cancellation: {e}")
            raise ProviderAPIError(
                provider="anthropic",
                operation="cancel_batch",
                original_error=e,
            ) from e

    async def list_batches(
        self,
        status: BatchJobStatus | None = None,
        limit: int = 100,
    ) -> list[BatchJob]:
        """List batch jobs with optional status filter.

        Args:
            status: Optional status to filter by.
            limit: Maximum number of jobs to return.

        Returns:
            List of BatchJob objects.

        Raises:
            ProviderAPIError: If the Anthropic API call fails.
        """
        try:
            logger.debug(f"Listing Anthropic batches (limit={limit}, status={status})")

            jobs: list[BatchJob] = []
            count = 0

            for batch in self.client.beta.messages.batches.list(limit=limit):
                if count >= limit:
                    break

                job = self._batch_to_job(batch)

                # Filter by status if specified
                if status is None or job.status == status:
                    jobs.append(job)
                    count += 1

            logger.info(f"Listed {len(jobs)} Anthropic batches")
            return jobs

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error during batch listing: {e}")
            raise ProviderAPIError(
                provider="anthropic",
                operation="list_batches",
                original_error=e,
            ) from e
