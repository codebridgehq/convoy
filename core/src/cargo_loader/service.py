"""Cargo loader service for persisting cargo requests to the database."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import CargoRequest, CargoStatus, ProviderType

from .exceptions import DatabasePersistenceError
from .models import CargoLoadInput, CargoLoadResult

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

    async def load_cargo(self, input: CargoLoadInput) -> CargoLoadResult:
        """Load a cargo request into the database.

        Args:
            input: The cargo load input containing model, params, and callback URL.

        Returns:
            CargoLoadResult with the generated cargo_id and status.

        Raises:
            DatabasePersistenceError: If the cargo cannot be persisted to the database.
        """
        cargo_id = generate_cargo_id()
        logger.info(f"Loading cargo with ID: {cargo_id}")

        try:
            cargo_request = CargoRequest(
                cargo_id=cargo_id,
                provider=ProviderType.BEDROCK,
                model=input.model,
                params=input.params,
                callback_url=input.callback_url,
                status=CargoStatus.PENDING,
            )

            self.session.add(cargo_request)
            await self.session.flush()

            logger.info(f"Cargo {cargo_id} loaded successfully")

            return CargoLoadResult(
                cargo_id=cargo_id,
                success=True,
                message="Cargo loaded successfully",
            )

        except Exception as e:
            logger.error(f"Failed to persist cargo {cargo_id}: {e}")
            raise DatabasePersistenceError(
                message=f"Failed to persist cargo {cargo_id} to database",
                original_error=e,
            ) from e
