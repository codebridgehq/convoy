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

    def __init__(self, session: AsyncSession, provider: ProviderType = ProviderType.BEDROCK):
        """Initialize the cargo loader service.

        Args:
            session: Async database session for persistence operations.
            provider: The provider to use for batch processing (default: BEDROCK).
        """
        self.session = session
        self.provider = provider

    async def load_cargo(self, input: CargoLoadInput) -> CargoLoadResult:
        """Load a cargo request into the database.

        Args:
            input: The cargo load input containing model IDs, params, and callback URL.
                   - convoy_model_id: Provider-agnostic model ID
                   - provider_model_id: Provider-specific model ID (translated)

        Returns:
            CargoLoadResult with the generated cargo_id and status.

        Raises:
            DatabasePersistenceError: If the cargo cannot be persisted to the database.
        """
        cargo_id = generate_cargo_id()
        logger.info(f"Loading cargo with ID: {cargo_id}, model: {input.convoy_model_id}")

        try:
            # Store provider-specific model ID in the model field
            # Store convoy model ID in params for reference
            params_with_convoy_model = {
                **input.params,
                "convoy_model_id": input.convoy_model_id,
            }

            cargo_request = CargoRequest(
                cargo_id=cargo_id,
                provider=self.provider,
                model=input.provider_model_id,  # Provider-specific model ID
                params=params_with_convoy_model,
                callback_url=input.callback_url,
                status=CargoStatus.PENDING,
                project_id=input.project_id,  # Associate cargo with project
            )

            self.session.add(cargo_request)
            await self.session.flush()

            logger.info(f"Cargo {cargo_id} loaded successfully (provider: {self.provider.value})")

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
