from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.cargo_loader import CargoLoaderService, CargoLoadInput, DatabasePersistenceError
from src.cargo_tracker import CargoTrackerService, CargoNotFoundError
from src.database import get_async_session
from src.api.models import CargoLoadRequest, CargoLoadResponse, CargoTrackingResponse


router = APIRouter(tags=["Cargo Operations"])


@router.post(
    "/cargo/load",
    response_model=CargoLoadResponse,
    status_code=status.HTTP_200_OK,
    summary="Load prompt for batch processing",
    description="Submits a prompt to the batch processing queue. The prompt will be processed asynchronously and results can be retrieved once processing is complete.",
)
async def load_cargo(
    request: CargoLoadRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Load cargo into the database for batch processing."""
    service = CargoLoaderService(session)
    
    # Map API DTO to service input
    service_input = CargoLoadInput(
        model=request.params.model,
        params=request.params.model_dump(),
        callback_url=request.callback_url,
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
    description="Returns tracking information for a specific cargo by ID."
)
async def get_cargo_tracking(
    cargo_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """Get tracking information for a cargo."""
    service = CargoTrackerService(session)
    try:
        tracking_info = await service.get_tracking(cargo_id)
        
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
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Returns the health status of the API."
)
def health_check():
    return {"status": "ok"}
