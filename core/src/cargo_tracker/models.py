"""Service-specific models for cargo tracker."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CargoTrackingInfo:
    """Tracking information for a cargo.
    
    This is the service-layer representation of cargo tracking data,
    decoupled from the API layer DTOs.
    """
    cargo_id: str
    status: str
    status_description: str
    created_at: datetime
    updated_at: datetime
