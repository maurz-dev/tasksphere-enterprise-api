"""Pydantic V2 schemas for Task entity."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from enterprise_api.models.enums import TaskPriority, TaskStatus
from enterprise_api.schemas.user import UserRead


class TaskBase(BaseModel):
    """Shared task attributes."""

    title: str = Field(..., min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    status: TaskStatus = Field(default=TaskStatus.TODO)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    due_date: datetime | None = None


class TaskCreate(BaseModel):
    """Payload to create a task."""

    title: str = Field(..., min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    priority: TaskPriority | None = TaskPriority.MEDIUM
    status: TaskStatus | None = TaskStatus.TODO
    project_id: int = Field(..., ge=1, description="ID of parent project")
    assignee_id: int | None = Field(default=None, ge=1, description="Assigned user ID")
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    """Payload to update task fields."""

    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: int | None = None
    due_date: datetime | None = None


class TaskStatusUpdate(BaseModel):
    """Specific payload for explicit workflow state transition."""

    status: TaskStatus = Field(..., description="Target status in workflow")


class TaskRead(TaskBase):
    """Task representation returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    creator_id: int
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime


class TaskDetail(TaskRead):
    """Enriched task representation including assigned and creator user details."""

    creator: UserRead
    assignee: UserRead | None = None


class TaskFilterParams(BaseModel):
    """Filtering options for tasks listing."""

    project_id: int | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: int | None = None
    search: str | None = Field(default=None, max_length=100)
