"""Abstract base class for batch processors."""

from abc import ABC, abstractmethod

from ..models import BatchJob, BatchJobStatus, BatchRequest, BatchResult


class BaseBatchProcessor(ABC):
    """Abstract base class defining the interface for batch processors."""

    @abstractmethod
    async def create_batch(
        self,
        requests: list[BatchRequest],
        metadata: dict | None = None,
    ) -> BatchJob:
        """Create a new batch job.

        Args:
            requests: List of batch requests to process.
            metadata: Optional metadata to attach to the job.

        Returns:
            BatchJob with job_id and initial status.

        Raises:
            ProviderAPIError: If the provider API call fails.
        """
        pass

    @abstractmethod
    async def get_batch_status(self, job_id: str) -> BatchJob:
        """Get the current status of a batch job.

        Args:
            job_id: The provider-specific job identifier.

        Returns:
            BatchJob with current status.

        Raises:
            BatchJobNotFoundError: If the job does not exist.
            ProviderAPIError: If the provider API call fails.
        """
        pass

    @abstractmethod
    async def get_batch_results(
        self,
        job_id: str,
        limit: int | None = None,
    ) -> list[BatchResult]:
        """Retrieve results from a completed batch job.

        Args:
            job_id: The provider-specific job identifier.
            limit: Optional maximum number of results to return.

        Returns:
            List of BatchResult objects.

        Raises:
            BatchJobNotFoundError: If the job does not exist.
            BatchJobCancelledError: If the job was cancelled.
            ProviderAPIError: If the provider API call fails.
        """
        pass

    @abstractmethod
    async def cancel_batch(self, job_id: str) -> bool:
        """Cancel a running batch job.

        Args:
            job_id: The provider-specific job identifier.

        Returns:
            True if cancellation was successful.

        Raises:
            BatchJobNotFoundError: If the job does not exist.
            ProviderAPIError: If the provider API call fails.
        """
        pass

    @abstractmethod
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
            ProviderAPIError: If the provider API call fails.
        """
        pass
