from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import AuthenticatedProject, get_current_project
from src.cargo_loader import CargoLoaderService, CargoLoadInput, DatabasePersistenceError
from src.cargo_tracker import CargoTrackerService, CargoNotFoundError
from src.database import ProviderType, get_async_session
from src.api.models import (
    CargoLoadRequest,
    CargoLoadResponse,
    CargoTrackingResponse,
    SupportedModelsResponse,
    ModelInfo,
)
from src.models import (
    MODEL_REGISTRY,
    Provider,
    get_supported_models,
    validate_model,
    InvalidModelError,
    ModelNotAvailableForProviderError,
    ModelNotAvailableInRegionError,
)
from src.worker.config import BedrockConfig, ProviderConfig


router = APIRouter(tags=["Cargo Operations"])


def _get_provider_config() -> tuple[Provider, ProviderType, str | None]:
    """Get the current provider configuration.

    Returns:
        Tuple of (models.Provider, database.ProviderType, region or None).
    """
    provider_config = ProviderConfig()
    provider_str = provider_config.default_provider.lower()

    if provider_str == "anthropic":
        return Provider.ANTHROPIC, ProviderType.ANTHROPIC, None
    else:
        # Default to Bedrock
        bedrock_config = BedrockConfig()
        return Provider.BEDROCK, ProviderType.BEDROCK, bedrock_config.region or None


@router.post(
    "/cargo/load",
    response_model=CargoLoadResponse,
    status_code=status.HTTP_200_OK,
    summary="Load prompt for batch processing",
    description="Submits a prompt to the batch processing queue. The prompt will be processed asynchronously and results can be retrieved once processing is complete.",
    responses={
        400: {"description": "Invalid model ID or model not available"},
        401: {"description": "Invalid or missing API key"},
        403: {"description": "Project is inactive"},
    },
)
async def load_cargo(
    request: CargoLoadRequest,
    auth: AuthenticatedProject = Depends(get_current_project),
    session: AsyncSession = Depends(get_async_session),
):
    """Load cargo into the database for batch processing.

    The model ID should be a provider-agnostic identifier (e.g., "claude-3-haiku").
    The system will validate the model and translate it to the appropriate
    provider-specific identifier based on the configured provider.
    """
    # Get provider configuration
    provider, provider_type, region = _get_provider_config()

    # Validate model ID and get provider-specific identifier
    convoy_model_id = request.params.model
    try:
        provider_model_id = validate_model(
            model_id=convoy_model_id,
            provider=provider,
            region=region,
        )
    except InvalidModelError:
        supported = get_supported_models(provider=provider, region=region)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_model",
                "message": f"Unknown model: {convoy_model_id}",
                "supported_models": supported,
            },
        )
    except ModelNotAvailableForProviderError:
        supported = get_supported_models(provider=provider)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "model_not_available",
                "message": f"Model {convoy_model_id} is not available for {provider.value}",
                "supported_models": supported,
            },
        )
    except ModelNotAvailableInRegionError as e:
        supported = get_supported_models(provider=provider, region=region)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "model_not_in_region",
                "message": f"Model {convoy_model_id} is not available in region {region}",
                "available_regions": e.available_regions,
                "supported_models": supported,
            },
        )

    # Create service with the configured provider
    service = CargoLoaderService(session, provider=provider_type)

    # Map API DTO to service input with project context
    service_input = CargoLoadInput(
        convoy_model_id=convoy_model_id,
        provider_model_id=provider_model_id,
        params=request.params.model_dump(),
        callback_url=request.callback_url,
        project_id=auth.project_id,
    )

    try:
        result = await service.load_cargo(service_input)

        # Map service result to API response
        return CargoLoadResponse(
            cargo_id=result.cargo_id,
            status="success" if result.success else "error",
            message=result.message,
        )
    except DatabasePersistenceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e.message),
        ) from e


@router.get(
    "/cargo/{cargo_id}/tracking",
    response_model=CargoTrackingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get cargo tracking",
    description="Returns tracking information for a specific cargo by ID. Only returns cargo owned by the authenticated project.",
    responses={
        401: {"description": "Invalid or missing API key"},
        403: {"description": "Project is inactive"},
        404: {"description": "Cargo not found or not owned by project"},
    },
)
async def get_cargo_tracking(
    cargo_id: str,
    auth: AuthenticatedProject = Depends(get_current_project),
    session: AsyncSession = Depends(get_async_session),
):
    """Get tracking information for a cargo owned by the authenticated project."""
    service = CargoTrackerService(session)
    try:
        # Pass project_id to scope query to authenticated project
        tracking_info = await service.get_tracking(
            cargo_id=cargo_id,
            project_id=auth.project_id,
        )
        
        # Map service result to API response
        return CargoTrackingResponse(
            cargo_id=tracking_info.cargo_id,
            status=tracking_info.status,
            status_description=tracking_info.status_description,
            created_at=tracking_info.created_at,
            updated_at=tracking_info.updated_at,
        )
    except CargoNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.message),
        ) from e


@router.get(
    "/models",
    response_model=SupportedModelsResponse,
    status_code=status.HTTP_200_OK,
    summary="List supported models",
    description="Returns a list of all supported models and their availability for the current provider configuration.",
)
def list_supported_models():
    """List all supported models and their availability.

    This endpoint returns information about all models supported by Convoy,
    including which providers they're available for and regional availability
    for Bedrock. No authentication required.
    """
    # Get current provider configuration
    provider, _, region = _get_provider_config()

    # Build model info list
    models_info = []
    for model_id, mapping in MODEL_REGISTRY.items():
        models_info.append(
            ModelInfo(
                model_id=model_id,
                description=mapping.description,
                model_family=mapping.model_family,
                available_for_anthropic=mapping.anthropic_id is not None,
                available_for_bedrock=mapping.bedrock_id is not None,
                bedrock_regions=mapping.bedrock_regions,
                deprecated=mapping.deprecated,
            )
        )

    # Get models available for current configuration
    available = get_supported_models(provider=provider, region=region)

    return SupportedModelsResponse(
        models=models_info,
        current_provider=provider.value,
        current_region=region,
        available_models=available,
    )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Returns the health status of the API.",
)
def health_check():
    """Health check endpoint - no authentication required."""
    return {"status": "ok"}
