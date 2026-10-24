"""Task management and workflow state machine endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from enterprise_api.api.deps import (
    get_current_user,
    get_task_service,
)
from enterprise_api.models.user import User
from enterprise_api.schemas.common import PageMetadata, PaginatedResponse, PaginationParams
from enterprise_api.schemas.task import (
    TaskCreate,
    TaskDetail,
    TaskFilterParams,
    TaskRead,
    TaskStatusUpdate,
    TaskUpdate,
)
from enterprise_api.services.task_service import TaskService

router = APIRouter()


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
async def create_task(
    payload: TaskCreate,
    task_service: Annotated[TaskService, Depends(get_task_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TaskRead:
    task = await task_service.create_task(payload, current_user)
    return TaskRead.model_validate(task)


@router.get(
    "",
    response_model=PaginatedResponse[TaskRead],
    summary="List tasks with dynamic filters and pagination",
)
async def list_tasks(
    pagination: Annotated[PaginationParams, Depends()],
    filters: Annotated[TaskFilterParams, Depends()],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> PaginatedResponse[TaskRead]:
    tasks, total = await task_service.list_tasks(
        filters=filters,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    total_pages = (
        (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0
    )
    return PaginatedResponse(
        items=[TaskRead.model_validate(t) for t in tasks],
        meta=PageMetadata(
            total_items=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_previous=pagination.page > 1,
        ),
    )


@router.get(
    "/{task_id}",
    response_model=TaskDetail,
    summary="Get task details with assignee and creator information",
)
async def get_task(
    task_id: int,
    task_service: Annotated[TaskService, Depends(get_task_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> TaskDetail:
    task = await task_service.get_by_id(task_id)
    return TaskDetail.model_validate(task)


@router.patch(
    "/{task_id}",
    response_model=TaskRead,
    summary="Update task attributes",
)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    task_service: Annotated[TaskService, Depends(get_task_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TaskRead:
    updated = await task_service.update_task(task_id, payload, current_user)
    return TaskRead.model_validate(updated)


@router.post(
    "/{task_id}/transition",
    response_model=TaskRead,
    summary="Explicitly transition task status (State Machine)",
)
async def transition_task_status(
    task_id: int,
    payload: TaskStatusUpdate,
    task_service: Annotated[TaskService, Depends(get_task_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TaskRead:
    updated = await task_service.transition_status(task_id, payload.status, current_user)
    return TaskRead.model_validate(updated)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
async def delete_task(
    task_id: int,
    task_service: Annotated[TaskService, Depends(get_task_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    await task_service.delete_task(task_id, current_user)
