"""Cargo tracker service for retrieving cargo status and tracking information."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import CargoRequest
from src.models import CargoTrackingResponse

from .exceptions import CargoNotFoundError

logger = logging.getLogger(__name__)


class CargoTrackerService:
    """Service for tracking cargo status.

    This service handles retrieval of cargo tracking information,
    including status and timestamps.
    """

    def __init__(self, session: AsyncSession):
        """Initialize the cargo tracker service.

        Args:
            session: Async database session for query operations.
        """
        self.session = session

    async def get_tracking(self, cargo_id: str) -> CargoTrackingResponse:
        """Get tracking information for a cargo.

        Args:
            cargo_id: The unique cargo identifier.

        Returns:
            CargoTrackingResponse with status and timestamps.

        Raises:
            CargoNotFoundError: If the cargo does not exist.
        """
        logger.info(f"Getting tracking info for cargo: {cargo_id}")

        stmt = select(CargoRequest).where(CargoRequest.cargo_id == cargo_id)
        result = await self.session.execute(stmt)
        cargo = result.scalar_one_or_none()

        if cargo is None:
            logger.warning(f"Cargo not found: {cargo_id}")
            raise CargoNotFoundError(cargo_id)

        logger.info(f"Found cargo {cargo_id} with status: {cargo.status.value}")

        return CargoTrackingResponse(
            cargo_id=cargo.cargo_id,
            status=cargo.status.value,
            status_description=cargo.status.description,
            created_at=cargo.created_at,
            updated_at=cargo.updated_at,
        )
