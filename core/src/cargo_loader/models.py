"""Service-specific models for cargo loader."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class CargoLoadInput:
    """Input for loading cargo into the system.
    
    This is the service-layer representation of a cargo load request,
    decoupled from the API layer DTOs.
    
    Attributes:
        convoy_model_id: Provider-agnostic model ID (e.g., "claude-3-haiku").
        provider_model_id: Provider-specific model ID (translated from convoy_model_id).
        params: Request parameters including messages, max_tokens, etc.
        callback_url: URL to receive results when processing completes.
        project_id: UUID of the project this cargo belongs to.
    """
    convoy_model_id: str  # Provider-agnostic model ID
    provider_model_id: str  # Provider-specific model ID (translated)
    params: dict[str, Any]
    callback_url: str
    project_id: UUID  # Required - all cargo must belong to a project

    @property
    def model(self) -> str:
        """Alias for provider_model_id for backward compatibility."""
        return self.provider_model_id


@dataclass
class CargoLoadResult:
    """Result of a cargo load operation.
    
    This is the service-layer representation of a cargo load result,
    decoupled from the API layer DTOs.
    """
    cargo_id: str
    success: bool
    message: str
