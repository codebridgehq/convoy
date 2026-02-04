"""Batch processing service for managing batch jobs across providers."""

import logging
from typing import Any

from .adapters.base_batch_processor import BaseBatchProcessor
from .exceptions import AdapterNotFoundError
from .models import BatchJob, BatchJobStatus, BatchProvider, BatchRequest, BatchResult

logger = logging.getLogger(__name__)


class BatchProcessingService:
    """Service for managing batch processing across multiple providers.

    This service provides a unified interface for creating and managing
    batch jobs across different AI providers (Bedrock, Anthropic, etc.).
    """

    def __init__(self, default_provider: BatchProvider):
        """Initialize the batch processing service.

        Args:
            default_provider: Default provider to use when none is specified.
        """
        self.default_provider = default_provider
        self.adapters: dict[BatchProvider, BaseBatchProcessor] = {}
        logger.info(f"BatchProcessingService initialized with default provider: {default_provider.value}")

    def register_adapter(self, provider: BatchProvider, adapter: BaseBatchProcessor) -> None:
        """Register an adapter for a provider.

        Args:
            provider: The provider enum value.
            adapter: The adapter instance to register.
        """
        self.adapters[provider] = adapter
        logger.info(f"Registered adapter for provider: {provider.value}")

    def get_adapter(self, provider: BatchProvider | None = None) -> BaseBatchProcessor:
        """Get the adapter for a provider.

        Args:
            provider: The provider to get adapter for. Uses default if None.

        Returns:
            The registered adapter for the provider.

        Raises:
            AdapterNotFoundError: If no adapter is registered for the provider.
        """
        target_provider = provider or self.default_provider

        if target_provider not in self.adapters:
            logger.error(f"No adapter registered for provider: {target_provider.value}")
            raise AdapterNotFoundError(target_provider.value)

        return self.adapters[target_provider]

    async def create_batch(
        self,
        requests: list[BatchRequest],
        provider: BatchProvider | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BatchJob:
        """Create a new batch job.

        Args:
            requests: List of batch requests to process.
            provider: Provider to use. Uses default if None.
            metadata: Optional metadata to attach to the job.

        Returns:
            BatchJob with job_id and initial status.

        Raises:
            AdapterNotFoundError: If no adapter is registered for the provider.
            ProviderAPIError: If the provider API call fails.
        """
        target_provider = provider or self.default_provider
        logger.info(f"Creating batch with {len(requests)} requests using provider: {target_provider.value}")

        adapter = self.get_adapter(target_provider)
        return await adapter.create_batch(requests, metadata)

    async def get_batch_status(
        self,
        job_id: str,
        provider: BatchProvider | None = None,
    ) -> BatchJob:
        """Get the current status of a batch job.

        Args:
            job_id: The provider-specific job identifier.
            provider: Provider to query. Uses default if None.

        Returns:
            BatchJob with current status.

        Raises:
            AdapterNotFoundError: If no adapter is registered for the provider.
            BatchJobNotFoundError: If the job does not exist.
            ProviderAPIError: If the provider API call fails.
        """
        target_provider = provider or self.default_provider
        logger.debug(f"Getting batch status for job {job_id} from provider: {target_provider.value}")

        adapter = self.get_adapter(target_provider)
        return await adapter.get_batch_status(job_id)

    async def get_batch_results(
        self,
        job_id: str,
        provider: BatchProvider | None = None,
        limit: int | None = None,
    ) -> list[BatchResult]:
        """Retrieve results from a completed batch job.

        Args:
            job_id: The provider-specific job identifier.
            provider: Provider to query. Uses default if None.
            limit: Optional maximum number of results to return.

        Returns:
            List of BatchResult objects.

        Raises:
            AdapterNotFoundError: If no adapter is registered for the provider.
            BatchJobNotFoundError: If the job does not exist.
            BatchJobCancelledError: If the job was cancelled.
            ProviderAPIError: If the provider API call fails.
        """
        target_provider = provider or self.default_provider
        logger.debug(f"Getting batch results for job {job_id} from provider: {target_provider.value}")

        adapter = self.get_adapter(target_provider)
        return await adapter.get_batch_results(job_id, limit)

    async def cancel_batch(
        self,
        job_id: str,
        provider: BatchProvider | None = None,
    ) -> bool:
        """Cancel a running batch job.

        Args:
            job_id: The provider-specific job identifier.
            provider: Provider to use. Uses default if None.

        Returns:
            True if cancellation was successful.

        Raises:
            AdapterNotFoundError: If no adapter is registered for the provider.
            BatchJobNotFoundError: If the job does not exist.
            ProviderAPIError: If the provider API call fails.
        """
        target_provider = provider or self.default_provider
        logger.info(f"Cancelling batch job {job_id} on provider: {target_provider.value}")

        adapter = self.get_adapter(target_provider)
        return await adapter.cancel_batch(job_id)

    async def list_batches(
        self,
        provider: BatchProvider | None = None,
        status: BatchJobStatus | None = None,
        limit: int = 100,
    ) -> list[BatchJob]:
        """List batch jobs with optional status filter.

        Args:
            provider: Provider to query. Uses default if None.
            status: Optional status to filter by.
            limit: Maximum number of jobs to return.

        Returns:
            List of BatchJob objects.

        Raises:
            AdapterNotFoundError: If no adapter is registered for the provider.
            ProviderAPIError: If the provider API call fails.
        """
        target_provider = provider or self.default_provider
        logger.debug(f"Listing batches from provider: {target_provider.value} (status={status}, limit={limit})")

        adapter = self.get_adapter(target_provider)
        return await adapter.list_batches(status, limit)
