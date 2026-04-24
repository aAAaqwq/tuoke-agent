from fastapi import APIRouter

from app.schemas.common import ApiResponse, HealthData

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse[HealthData])
def get_health() -> ApiResponse[HealthData]:
    """Return the current health status for the backend service."""

    return ApiResponse(
        code="OK",
        message="service is healthy",
        data=HealthData(status="healthy", service="tuoke-agent-backend"),
    )
