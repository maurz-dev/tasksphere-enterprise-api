"""Pydantic V2 schemas for Project entity."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from enterprise_api.models.enums import ProjectStatus
from enterprise_api.schemas.user import UserRead


class ProjectBase(BaseModel):
    """Shared project attributes."""

    title: str = Field(..., min_length=3, max_length=200, description="Project name")
    description: str | None = Field(default=None, max_length=5000)
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE)


class ProjectCreate(BaseModel):
    """Payload to create a new project."""

    title: str = Field(..., min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: ProjectStatus | None = ProjectStatus.ACTIVE


class ProjectUpdate(BaseModel):
    """Payload to update an existing project."""

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: ProjectStatus | None = None


class ProjectRead(ProjectBase):
    """Project representation returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    owner_id: int
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectRead):
    """Detailed project representation including owner profile."""

    owner: UserRead
    total_tasks: int = 0
    completed_tasks: int = 0
