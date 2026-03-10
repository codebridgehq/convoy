"""Model validation logic for provider-agnostic model IDs.

This module provides functions to validate model IDs and translate them
to provider-specific identifiers.
"""

from .exceptions import (
    InvalidModelError,
    ModelNotAvailableForProviderError,
    ModelNotAvailableInRegionError,
)
from .registry import MODEL_REGISTRY, Provider, get_model_mapping, get_supported_models


def validate_model(
    model_id: str,
    provider: Provider,
    region: str | None = None,
) -> str:
    """Validate a model ID and return the provider-specific identifier.

    This is the main validation function that should be called when processing
    incoming requests. It validates that:
    1. The model ID is recognized
    2. The model is available for the specified provider
    3. For Bedrock, the model is available in the specified region

    Args:
        model_id: Provider-agnostic model identifier (e.g., "claude-3-haiku").
        provider: Target provider (BEDROCK or ANTHROPIC).
        region: AWS region (required for Bedrock provider).

    Returns:
        Provider-specific model identifier.

    Raises:
        InvalidModelError: If the model ID is not recognized.
        ModelNotAvailableForProviderError: If the model is not available for the provider.
        ModelNotAvailableInRegionError: If the model is not available in the region (Bedrock).
    """
    mapping = get_model_mapping(model_id)

    if mapping is None:
        raise InvalidModelError(model_id)

    if provider == Provider.ANTHROPIC:
        if not mapping.anthropic_id:
            raise ModelNotAvailableForProviderError(model_id, provider.value)
        return mapping.anthropic_id

    elif provider == Provider.BEDROCK:
        if not mapping.bedrock_id:
            raise ModelNotAvailableForProviderError(model_id, provider.value)

        # Validate regional availability for Bedrock
        if region and region not in mapping.bedrock_regions:
            raise ModelNotAvailableInRegionError(
                model_id=model_id,
                region=region,
                available_regions=mapping.bedrock_regions,
            )

        return mapping.bedrock_id

    else:
        raise ValueError(f"Unknown provider: {provider}")


def validate_model_for_provider(
    model_id: str,
    provider: Provider,
) -> bool:
    """Check if a model is available for a specific provider.

    This is a simpler check that doesn't consider regional availability.

    Args:
        model_id: Provider-agnostic model identifier.
        provider: Target provider.

    Returns:
        True if the model is available for the provider, False otherwise.
    """
    mapping = get_model_mapping(model_id)

    if mapping is None:
        return False

    if provider == Provider.ANTHROPIC:
        return mapping.anthropic_id is not None

    elif provider == Provider.BEDROCK:
        return mapping.bedrock_id is not None

    return False


def get_provider_model_id(
    model_id: str,
    provider: Provider,
) -> str | None:
    """Get the provider-specific model ID without validation.

    This function returns the provider-specific model ID without raising
    exceptions. Useful for cases where you want to handle missing models
    differently.

    Args:
        model_id: Provider-agnostic model identifier.
        provider: Target provider.

    Returns:
        Provider-specific model identifier, or None if not available.
    """
    mapping = get_model_mapping(model_id)

    if mapping is None:
        return None

    if provider == Provider.ANTHROPIC:
        return mapping.anthropic_id

    elif provider == Provider.BEDROCK:
        return mapping.bedrock_id

    return None


def get_validation_error_details(
    model_id: str,
    provider: Provider,
    region: str | None = None,
) -> dict:
    """Get detailed error information for model validation failures.

    This function provides structured error details suitable for API responses.

    Args:
        model_id: Provider-agnostic model identifier.
        provider: Target provider.
        region: AWS region (for Bedrock).

    Returns:
        Dictionary with error details including:
        - error: Error type string
        - message: Human-readable error message
        - supported_models: List of supported models (for invalid model errors)
        - available_regions: List of available regions (for region errors)
    """
    mapping = get_model_mapping(model_id)

    if mapping is None:
        return {
            "error": "invalid_model",
            "message": f"Unknown model: {model_id}",
            "supported_models": get_supported_models(provider=provider, region=region),
        }

    if provider == Provider.ANTHROPIC:
        if not mapping.anthropic_id:
            return {
                "error": "model_not_available",
                "message": f"Model {model_id} is not available for Anthropic API",
                "supported_models": get_supported_models(provider=provider),
            }

    elif provider == Provider.BEDROCK:
        if not mapping.bedrock_id:
            return {
                "error": "model_not_available",
                "message": f"Model {model_id} is not available for AWS Bedrock",
                "supported_models": get_supported_models(provider=provider),
            }

        if region and region not in mapping.bedrock_regions:
            return {
                "error": "model_not_in_region",
                "message": f"Model {model_id} is not available in region {region}",
                "available_regions": mapping.bedrock_regions,
                "supported_models": get_supported_models(provider=provider, region=region),
            }

    return {}
