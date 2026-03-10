"""Model-related exceptions for validation errors."""


class ModelValidationError(Exception):
    """Base exception for model validation errors."""

    pass


class InvalidModelError(ModelValidationError):
    """Raised when a model ID is not recognized."""

    def __init__(self, model_id: str):
        self.model_id = model_id
        super().__init__(f"Unknown model: {model_id}")


class ModelNotAvailableForProviderError(ModelValidationError):
    """Raised when a model is not available for the specified provider."""

    def __init__(self, model_id: str, provider: str):
        self.model_id = model_id
        self.provider = provider
        super().__init__(f"Model {model_id} is not available for provider {provider}")


class ModelNotAvailableInRegionError(ModelValidationError):
    """Raised when a model is not available in the specified AWS region for Bedrock."""

    def __init__(self, model_id: str, region: str, available_regions: list[str]):
        self.model_id = model_id
        self.region = region
        self.available_regions = available_regions
        super().__init__(
            f"Model {model_id} is not available in region {region}. "
            f"Available regions: {', '.join(available_regions)}"
        )
