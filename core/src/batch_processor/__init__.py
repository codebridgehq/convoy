"""Batch processor module for handling batch AI inference jobs."""

from .adapters.anthropic_batch_processor import AnthropicBatchProcessor
from .adapters.base_batch_processor import BaseBatchProcessor
from .adapters.bedrock_batch_processor import BedrockBatchProcessor
from .exceptions import (
    AdapterNotFoundError,
    BatchJobCancelledError,
    BatchJobNotFoundError,
    BatchProcessorError,
    ProviderAPIError,
)
from .models import (
    BatchJob,
    BatchJobStatus,
    BatchProvider,
    BatchRequest,
    BatchResult,
)
from .service import BatchProcessingService

__all__ = [
    # Exceptions
    "BatchProcessorError",
    "AdapterNotFoundError",
    "BatchJobNotFoundError",
    "BatchJobCancelledError",
    "ProviderAPIError",
    # Models
    "BatchProvider",
    "BatchJobStatus",
    "BatchRequest",
    "BatchJob",
    "BatchResult",
    # Service
    "BatchProcessingService",
    # Adapters
    "BaseBatchProcessor",
    "AnthropicBatchProcessor",
    "BedrockBatchProcessor",
]
