"""Batch processing activities for Temporal workflows."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from temporalio import activity

from src.batch_processor import BatchProcessingService
from src.batch_processor.adapters.bedrock_batch_processor import BedrockBatchProcessor
from src.batch_processor.models import BatchProvider, BatchRequest
from src.database import (
    BatchJob,
    BatchStatus,
    CallbackDelivery,
    CallbackStatus,
    CargoRequest,
    CargoResult,
    CargoStatus,
    ProviderType,
    get_async_session,
)
from src.worker.config import BatchConfig, BedrockConfig

logger = logging.getLogger(__name__)


@dataclass
class PendingRequestsResult:
    """Result of checking pending requests."""

    should_batch: bool
    pending_count: int
    oldest_age_seconds: int | None
    # For Bedrock: list of models that have >= threshold pending requests
    models_ready: list[str] | None = None


@dataclass
class BatchStatusResult:
    """Result of polling batch status."""

    completed: bool
    status: str
    error_message: str | None = None


def _get_provider_type(provider: str) -> ProviderType:
    """Convert string provider to ProviderType enum."""
    return ProviderType(provider.lower())


def _get_batch_provider(provider: str) -> BatchProvider:
    """Convert string provider to BatchProvider enum."""
    return BatchProvider(provider.lower())


def _create_bedrock_adapter() -> BedrockBatchProcessor:
    """Create a BedrockBatchProcessor with configuration from BedrockConfig.

    Returns:
        Configured BedrockBatchProcessor instance.

    Raises:
        ValueError: If required environment variables are not set.
    """
    config = BedrockConfig()

    missing_vars = []
    if not config.region:
        missing_vars.append("AWS_REGION")
    if not config.s3_bucket:
        missing_vars.append("BEDROCK_S3_BUCKET")
    if not config.role_arn:
        missing_vars.append("BEDROCK_ROLE_ARN")

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables for Bedrock batch processor: {', '.join(missing_vars)}"
        )

    return BedrockBatchProcessor(
        region=config.region,
        s3_bucket=config.s3_bucket,
        role_arn=config.role_arn,
        s3_input_prefix=config.s3_input_prefix,
        s3_output_prefix=config.s3_output_prefix,
    )


@activity.defn
async def check_pending_requests(provider: str) -> dict:
    """Check if a batch should be created for the given provider.

    For Bedrock, requests are grouped by model since Bedrock requires a single
    model per batch job. For Anthropic, all requests can be batched together
    since each request specifies its own model.

    Args:
        provider: Provider name (bedrock or anthropic).

    Returns:
        Dictionary with:
        - should_batch: Whether a batch should be created
        - pending_count: Number of pending requests
        - oldest_age_seconds: Age of oldest request in seconds
        - models_ready: (Bedrock only) List of models with >= threshold requests
    """
    config = BatchConfig()
    provider_type = _get_provider_type(provider)

    async for session in get_async_session():
        if provider_type == ProviderType.BEDROCK:
            # For Bedrock: Group by model since each batch requires a single model
            count_stmt = (
                select(CargoRequest.model, func.count().label("count"))
                .where(
                    CargoRequest.provider == provider_type,
                    CargoRequest.status == CargoStatus.PENDING,
                )
                .group_by(CargoRequest.model)
            )
            result = await session.execute(count_stmt)
            model_counts = {row.model: row.count for row in result}

            # Find models that meet the threshold
            models_ready = [
                model
                for model, count in model_counts.items()
                if count >= config.size_threshold
            ]

            total_pending = sum(model_counts.values())
            should_batch = len(models_ready) > 0

            # Get oldest pending request age
            oldest_stmt = select(func.min(CargoRequest.created_at)).where(
                CargoRequest.provider == provider_type,
                CargoRequest.status == CargoStatus.PENDING,
            )
            result = await session.execute(oldest_stmt)
            oldest_time = result.scalar()

            oldest_age_seconds = None
            if oldest_time:
                age = datetime.now(timezone.utc) - oldest_time
                oldest_age_seconds = int(age.total_seconds())

            if models_ready:
                logger.info(
                    f"Bedrock batch threshold met for models: {models_ready} "
                    f"(threshold: {config.size_threshold})"
                )

            return {
                "should_batch": should_batch,
                "pending_count": total_pending,
                "oldest_age_seconds": oldest_age_seconds,
                "models_ready": models_ready,
            }
        else:
            # For Anthropic: No model grouping needed, each request has its own model
            count_stmt = (
                select(func.count())
                .select_from(CargoRequest)
                .where(
                    CargoRequest.provider == provider_type,
                    CargoRequest.status == CargoStatus.PENDING,
                )
            )
            result = await session.execute(count_stmt)
            pending_count = result.scalar() or 0

            # Get oldest pending request age
            oldest_stmt = select(func.min(CargoRequest.created_at)).where(
                CargoRequest.provider == provider_type,
                CargoRequest.status == CargoStatus.PENDING,
            )
            result = await session.execute(oldest_stmt)
            oldest_time = result.scalar()

            oldest_age_seconds = None
            if oldest_time:
                age = datetime.now(timezone.utc) - oldest_time
                oldest_age_seconds = int(age.total_seconds())

            # Determine if we should create a batch
            should_batch = False
            if pending_count >= config.size_threshold:
                logger.info(
                    f"Batch threshold met for {provider}: {pending_count} >= {config.size_threshold}"
                )
                should_batch = True

            return {
                "should_batch": should_batch,
                "pending_count": pending_count,
                "oldest_age_seconds": oldest_age_seconds,
                "models_ready": None,
            }


@activity.defn
async def create_batch_job(provider: str, model: str | None = None) -> str:
    """Create a batch job and assign pending requests to it.

    For Bedrock, a model parameter is required to ensure all requests in the
    batch use the same model. For Anthropic, model is ignored since each
    request specifies its own model.

    Args:
        provider: Provider name (bedrock or anthropic).
        model: (Bedrock only) Model ID to filter requests by.

    Returns:
        The batch job ID as a string.
    """
    config = BatchConfig()
    provider_type = _get_provider_type(provider)

    async for session in get_async_session():
        # Create the batch job
        batch_job = BatchJob(
            provider=provider_type,
            status=BatchStatus.READY,
        )
        session.add(batch_job)
        await session.flush()

        if provider_type == ProviderType.BEDROCK and model:
            logger.info(
                f"Created Bedrock batch job {batch_job.id} for model: {model}"
            )
        else:
            logger.info(f"Created batch job {batch_job.id} for provider {provider}")

        # Build query for pending requests
        pending_stmt = select(CargoRequest).where(
            CargoRequest.provider == provider_type,
            CargoRequest.status == CargoStatus.PENDING,
        )

        # For Bedrock, filter by model to ensure all requests use the same model
        if provider_type == ProviderType.BEDROCK and model:
            pending_stmt = pending_stmt.where(CargoRequest.model == model)

        pending_stmt = (
            pending_stmt.order_by(CargoRequest.created_at).limit(config.size_threshold)
        )

        result = await session.execute(pending_stmt)
        pending_requests = result.scalars().all()

        # Assign requests to the batch
        request_ids = [req.id for req in pending_requests]
        if request_ids:
            update_stmt = (
                update(CargoRequest)
                .where(CargoRequest.id.in_(request_ids))
                .values(
                    batch_job_id=batch_job.id,
                    status=CargoStatus.BATCHED,
                )
            )
            await session.execute(update_stmt)

        batch_job.request_count = len(request_ids)
        await session.commit()

        logger.info(
            f"Assigned {len(request_ids)} requests to batch job {batch_job.id}"
        )

        return str(batch_job.id)


@activity.defn
async def submit_batch_to_provider(batch_job_id: str) -> str:
    """Submit a batch job to the provider.

    Args:
        batch_job_id: The batch job ID.

    Returns:
        The provider job ID.
    """
    from uuid import UUID

    batch_uuid = UUID(batch_job_id)

    async for session in get_async_session():
        # Get the batch job
        stmt = select(BatchJob).where(BatchJob.id == batch_uuid)
        result = await session.execute(stmt)
        batch_job = result.scalar_one()

        # Get all cargo requests for this batch
        requests_stmt = select(CargoRequest).where(CargoRequest.batch_job_id == batch_uuid)
        result = await session.execute(requests_stmt)
        cargo_requests = result.scalars().all()

        # Convert to BatchRequest objects
        batch_requests = []
        for cargo_req in cargo_requests:
            batch_request = BatchRequest(
                custom_id=cargo_req.cargo_id,
                model=cargo_req.model,
                messages=cargo_req.params.get("messages", []),
                max_tokens=cargo_req.params.get("max_tokens", 1024),
                system=cargo_req.params.get("system"),
                temperature=cargo_req.params.get("temperature"),
                top_p=cargo_req.params.get("top_p"),
                top_k=cargo_req.params.get("top_k"),
                stop_sequences=cargo_req.params.get("stop_sequences"),
                metadata=cargo_req.params.get("metadata"),
            )
            batch_requests.append(batch_request)

        # Create the batch processing service and submit
        batch_provider = _get_batch_provider(batch_job.provider.value)
        service = BatchProcessingService(default_provider=batch_provider)

        # Register the appropriate adapter
        if batch_provider == BatchProvider.BEDROCK:
            adapter = _create_bedrock_adapter()
            service.register_adapter(BatchProvider.BEDROCK, adapter)
        # TODO: Add Anthropic adapter when implemented

        provider_batch = await service.create_batch(batch_requests, provider=batch_provider)

        # Update batch job with provider job ID
        batch_job.provider_job_id = provider_batch.job_id
        batch_job.status = BatchStatus.SUBMITTED
        batch_job.submitted_at = datetime.now(timezone.utc)
        await session.commit()

        logger.info(
            f"Submitted batch job {batch_job_id} to {batch_job.provider.value}, "
            f"provider job ID: {provider_batch.job_id}"
        )

        return provider_batch.job_id


@activity.defn
async def poll_batch_status(batch_job_id: str, provider_job_id: str) -> dict:
    """Poll the provider for batch job status.

    Args:
        batch_job_id: The internal batch job ID.
        provider_job_id: The provider's job ID.

    Returns:
        Dictionary with:
        - completed: Whether the batch is complete
        - status: Current status string
        - error_message: Error message if failed
    """
    from uuid import UUID

    batch_uuid = UUID(batch_job_id)

    async for session in get_async_session():
        # Get the batch job
        stmt = select(BatchJob).where(BatchJob.id == batch_uuid)
        result = await session.execute(stmt)
        batch_job = result.scalar_one()

        # Create service and check status
        batch_provider = _get_batch_provider(batch_job.provider.value)
        service = BatchProcessingService(default_provider=batch_provider)

        if batch_provider == BatchProvider.BEDROCK:
            adapter = _create_bedrock_adapter()
            service.register_adapter(BatchProvider.BEDROCK, adapter)

        provider_status = await service.get_batch_status(provider_job_id, provider=batch_provider)

        # Map provider status to our status
        completed = False
        error_message = None

        if provider_status.status.value in ("completed", "ended"):
            completed = True
            batch_job.status = BatchStatus.COMPLETED
            batch_job.completed_at = datetime.now(timezone.utc)
        elif provider_status.status.value == "failed":
            completed = True
            batch_job.status = BatchStatus.FAILED
            batch_job.completed_at = datetime.now(timezone.utc)
            error_message = provider_status.error_message
            batch_job.error_message = error_message
        elif provider_status.status.value in ("in_progress", "processing", "validating"):
            batch_job.status = BatchStatus.PROCESSING

        await session.commit()

        logger.info(
            f"Batch job {batch_job_id} status: {provider_status.status.value} "
            f"(completed: {completed})"
        )

        return {
            "completed": completed,
            "status": provider_status.status.value,
            "error_message": error_message,
        }


@activity.defn
async def process_batch_results(batch_job_id: str) -> list[str]:
    """Process results from a completed batch and create CargoResult records.

    Args:
        batch_job_id: The batch job ID.

    Returns:
        List of cargo_request_ids ready for callback delivery.
    """
    from uuid import UUID

    batch_uuid = UUID(batch_job_id)
    cargo_request_ids = []

    async for session in get_async_session():
        # Get the batch job
        stmt = select(BatchJob).where(BatchJob.id == batch_uuid)
        result = await session.execute(stmt)
        batch_job = result.scalar_one()

        if not batch_job.provider_job_id:
            logger.error(f"Batch job {batch_job_id} has no provider job ID")
            return []

        # Create service and get results
        batch_provider = _get_batch_provider(batch_job.provider.value)
        service = BatchProcessingService(default_provider=batch_provider)

        if batch_provider == BatchProvider.BEDROCK:
            adapter = _create_bedrock_adapter()
            service.register_adapter(BatchProvider.BEDROCK, adapter)

        batch_results = await service.get_batch_results(
            batch_job.provider_job_id, provider=batch_provider
        )

        # Get cargo requests for this batch
        requests_stmt = select(CargoRequest).where(CargoRequest.batch_job_id == batch_uuid)
        result = await session.execute(requests_stmt)
        cargo_requests = {req.cargo_id: req for req in result.scalars().all()}

        # Process each result
        for batch_result in batch_results:
            cargo_request = cargo_requests.get(batch_result.custom_id)
            if not cargo_request:
                logger.warning(f"No cargo request found for custom_id: {batch_result.custom_id}")
                continue

            # Create CargoResult
            cargo_result = CargoResult(
                cargo_request_id=cargo_request.id,
                success=batch_result.success,
                response=batch_result.response if batch_result.success else None,
                error_message=batch_result.error if not batch_result.success else None,
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            )
            session.add(cargo_result)

            # Create CallbackDelivery record
            callback_delivery = CallbackDelivery(
                cargo_request_id=cargo_request.id,
                status=CallbackStatus.PENDING,
            )
            session.add(callback_delivery)

            # Update cargo request status
            cargo_request.status = CargoStatus.CALLBACK_PENDING

            cargo_request_ids.append(str(cargo_request.id))

        await session.commit()

        logger.info(
            f"Processed {len(cargo_request_ids)} results for batch job {batch_job_id}"
        )

        return cargo_request_ids


@activity.defn
async def mark_batch_failed(batch_job_id: str, error_message: str) -> int:
    """Mark a batch job as failed and reset its cargo_requests to pending.

    This activity is called when a batch fails to submit to the provider,
    allowing the cargo_requests to be picked up by a future batch.

    Args:
        batch_job_id: The batch job ID.
        error_message: The error message describing why the batch failed.

    Returns:
        Number of cargo_requests that were reset to pending.
    """
    from uuid import UUID

    batch_uuid = UUID(batch_job_id)
    reset_count = 0

    async for session in get_async_session():
        # Get the batch job
        stmt = select(BatchJob).where(BatchJob.id == batch_uuid)
        result = await session.execute(stmt)
        batch_job = result.scalar_one_or_none()

        if not batch_job:
            logger.warning(f"Batch job {batch_job_id} not found")
            return 0

        # Only process if batch is in READY status (not yet submitted)
        if batch_job.status not in (BatchStatus.READY, BatchStatus.PENDING):
            logger.info(
                f"Batch job {batch_job_id} is in status {batch_job.status}, "
                f"not resetting cargo_requests"
            )
            # Still mark as failed if not already
            if batch_job.status not in (BatchStatus.FAILED, BatchStatus.COMPLETED, BatchStatus.CANCELLED):
                batch_job.status = BatchStatus.FAILED
                batch_job.error_message = error_message
                await session.commit()
            return 0

        # Reset cargo_requests back to pending so they can be reprocessed
        reset_stmt = (
            update(CargoRequest)
            .where(CargoRequest.batch_job_id == batch_uuid)
            .values(
                status=CargoStatus.PENDING,
                batch_job_id=None,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(CargoRequest.id)
        )
        result = await session.execute(reset_stmt)
        reset_ids = result.scalars().all()
        reset_count = len(reset_ids)

        # Mark batch as failed with the error message
        batch_job.status = BatchStatus.FAILED
        batch_job.error_message = error_message
        batch_job.completed_at = datetime.now(timezone.utc)

        await session.commit()

        logger.info(
            f"Marked batch job {batch_job_id} as failed: {error_message}. "
            f"Reset {reset_count} cargo_requests to pending."
        )

        return reset_count
