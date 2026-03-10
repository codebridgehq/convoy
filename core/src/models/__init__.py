"""Model registry module for provider-agnostic model IDs.

This module provides a unified model ID system that abstracts away
provider-specific identifiers (Bedrock ARNs, Anthropic model names).
"""

from .exceptions import (
    InvalidModelError,
    ModelNotAvailableForProviderError,
    ModelNotAvailableInRegionError,
    ModelValidationError,
)
from .registry import (
    MODEL_REGISTRY,
    ModelMapping,
    Provider,
    get_model_families,
    get_model_mapping,
    get_models_by_family,
    get_supported_models,
    is_valid_model,
)
from .validation import (
    get_provider_model_id,
    validate_model,
    validate_model_for_provider,
)

__all__ = [
    # Exceptions
    "InvalidModelError",
    "ModelNotAvailableForProviderError",
    "ModelNotAvailableInRegionError",
    "ModelValidationError",
    # Registry
    "MODEL_REGISTRY",
    "ModelMapping",
    "Provider",
    "get_model_families",
    "get_model_mapping",
    "get_models_by_family",
    "get_supported_models",
    "is_valid_model",
    # Validation
    "get_provider_model_id",
    "validate_model",
    "validate_model_for_provider",
]
