from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.cargo_loader import CargoLoaderService, DatabasePersistenceError
from src.database import get_async_session
from src.models import CargoLoadRequest, CargoLoadResponse


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
    try:
        return await service.load_cargo(request)
    except DatabasePersistenceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e.message),
        ) from e

@router.get(
    "/cargo/{cargo_id}/tracking",
    status_code=status.HTTP_200_OK,
    summary="Get cargo tracking",
    description="Returns tracking information for a specific cargo by ID."
)
def get_cargo(cargo_id: str):
    # Implement your logic here
    return {"status": "success", "message": f"Tracking information for cargo {cargo_id}"}

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Returns the health status of the API."
)
def health_check():
    return {"status": "ok"}
