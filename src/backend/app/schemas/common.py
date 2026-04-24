from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard success response envelope for API endpoints."""

    code: str
    message: str
    data: T | None = None


class ApiErrorResponse(BaseModel):
    """Standard error response envelope for API endpoints."""

    code: str
    message: str
    data: None = None


class HealthData(BaseModel):
    """Health check payload returned by the service."""

    status: str
    service: str


class ListResponse(BaseModel, Generic[T]):
    """Standard list payload for collection-style responses."""

    items: list[T]
