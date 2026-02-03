from fastapi import APIRouter, status
from pydantic import BaseModel, Field

class CargoLoadRequest(BaseModel):
    """Request model for loading a prompt into the batch processing queue."""
    prompt: str = Field(..., description="The prompt text to be processed")
    callback_url: str = Field(..., description="URL to receive notification when processing is complete")
    
class CargoLoadResponse(BaseModel):
    """Response model for the cargo load operation."""
    cargo_id: str = Field(..., description="Unique identifier for the loaded cargo")
    status: str = Field(..., description="Status of the operation (e.g., 'success', 'error')")
    message: str = Field(..., description="Detailed message about the operation result")


router = APIRouter()

@router.post(
    "/cargo/load",
    response_model=CargoLoadResponse,
    status_code=status.HTTP_200_OK,
    summary="Load prompt for batch processing",
    description="Submits a prompt to the batch processing queue. The prompt will be processed asynchronously and results can be retrieved once processing is complete."
)
def load_cargo(request: CargoLoadRequest):
    # Implement your logic here
    return CargoLoadResponse(cargo_id="unique_cargo_id", status="success", message="Cargo loaded successfully")

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
