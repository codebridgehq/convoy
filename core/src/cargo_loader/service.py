"""Cargo loader service for persisting cargo requests to the database."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import CargoRequest, CargoStatus, ProviderType
from src.models import CargoLoadRequest, CargoLoadResponse

from .exceptions import DatabasePersistenceError

logger = logging.getLogger(__name__)


def generate_cargo_id() -> str:
    """Generate a unique cargo ID with 'cargo_' prefix."""
    return f"cargo_{uuid.uuid4().hex}"


class CargoLoaderService:
    """Service for loading cargo requests into the database.

    This service handles the persistence of incoming cargo requests,
    generating unique cargo IDs and storing them with BEDROCK as the
    default provider.
    """

    def __init__(self, session: AsyncSession):
        """Initialize the cargo loader service.

        Args:
            session: Async database session for persistence operations.
        """
        self.session = session

    async def load_cargo(self, request: CargoLoadRequest) -> CargoLoadResponse:
        """Load a cargo request into the database.

        Args:
            request: The cargo load request containing params and callback URL.

        Returns:
            CargoLoadResponse with the generated cargo_id and status.

        Raises:
            DatabasePersistenceError: If the cargo cannot be persisted to the database.
        """
        cargo_id = generate_cargo_id()
        logger.info(f"Loading cargo with ID: {cargo_id}")

        try:
            cargo_request = CargoRequest(
                cargo_id=cargo_id,
                provider=ProviderType.BEDROCK,
                model=request.params.model,
                params=request.params.model_dump(),
                callback_url=request.callback_url,
                status=CargoStatus.PENDING,
            )

            self.session.add(cargo_request)
            await self.session.flush()

            logger.info(f"Cargo {cargo_id} loaded successfully")

            return CargoLoadResponse(
                cargo_id=cargo_id,
                status="success",
                message="Cargo loaded successfully",
            )

        except Exception as e:
            logger.error(f"Failed to persist cargo {cargo_id}: {e}")
            raise DatabasePersistenceError(
                message=f"Failed to persist cargo {cargo_id} to database",
                original_error=e,
            ) from e
