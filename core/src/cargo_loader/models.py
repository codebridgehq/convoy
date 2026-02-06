"""Service-specific models for cargo loader."""

from dataclasses import dataclass
from typing import Any


@dataclass
class CargoLoadInput:
    """Input for loading cargo into the system.
    
    This is the service-layer representation of a cargo load request,
    decoupled from the API layer DTOs.
    """
    model: str
    params: dict[str, Any]
    callback_url: str


@dataclass
class CargoLoadResult:
    """Result of a cargo load operation.
    
    This is the service-layer representation of a cargo load result,
    decoupled from the API layer DTOs.
    """
    cargo_id: str
    success: bool
    message: str
