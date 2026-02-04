"""Custom exceptions for the batch processor module."""


class BatchProcessorError(Exception):
    """Base exception for batch processor errors."""

    def __init__(self, message: str = "An error occurred in the batch processor"):
        self.message = message
        super().__init__(self.message)


class AdapterNotFoundError(BatchProcessorError):
    """Raised when a provider adapter is not registered."""

    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(f"Adapter not found for provider: {provider}")


class BatchJobNotFoundError(BatchProcessorError):
    """Raised when a batch job does not exist."""

    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Batch job not found: {job_id}")


class BatchJobCancelledError(BatchProcessorError):
    """Raised when trying to get results from a cancelled job."""

    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Cannot get results from cancelled batch job: {job_id}")


class ProviderAPIError(BatchProcessorError):
    """Raised when a provider API call fails."""

    def __init__(self, provider: str, operation: str, original_error: Exception | None = None):
        self.provider = provider
        self.operation = operation
        self.original_error = original_error
        message = f"Provider API error ({provider}) during {operation}"
        if original_error:
            message += f": {original_error}"
        super().__init__(message)
