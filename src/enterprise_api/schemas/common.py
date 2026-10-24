"""Common generic Pydantic V2 schemas for pagination, envelopes and metadata."""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for offset-based pagination."""

    model_config = ConfigDict(extra="forbid")

    page: int = Field(default=1, ge=1, description="Page number starting at 1")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PageMetadata(BaseModel):
    """Pagination navigation metadata."""

    total_items: int = Field(..., description="Total count of items matching filter")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Current items per page limit")
    total_pages: int = Field(..., description="Total available pages")
    has_next: bool = Field(..., description="Whether a subsequent page exists")
    has_previous: bool = Field(..., description="Whether a preceding page exists")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized generic container for paginated collections."""

    items: list[T]
    meta: PageMetadata


class HealthResponse(BaseModel):
    """Application health status contract."""

    status: str = Field(default="healthy", example="healthy")
    app_name: str
    version: str
    database_connected: bool
    environment: str
