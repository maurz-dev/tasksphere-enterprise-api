"""Project management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from enterprise_api.api.deps import (
    get_current_user,
    get_project_service,
)
from enterprise_api.models.user import User
from enterprise_api.schemas.common import PageMetadata, PaginatedResponse, PaginationParams
from enterprise_api.schemas.project import (
    ProjectCreate,
    ProjectDetail,
    ProjectRead,
    ProjectUpdate,
)
from enterprise_api.services.project_service import ProjectService

router = APIRouter()


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_project(
    payload: ProjectCreate,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProjectRead:
    project = await project_service.create_project(payload, current_user)
    return ProjectRead.model_validate(project)


@router.get(
    "",
    response_model=PaginatedResponse[ProjectRead],
    summary="List projects (Paginated)",
)
async def list_projects(
    pagination: Annotated[PaginationParams, Depends()],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> PaginatedResponse[ProjectRead]:
    projects, total = await project_service.list_projects(
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    total_pages = (
        (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0
    )
    return PaginatedResponse(
        items=[ProjectRead.model_validate(p) for p in projects],
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
    "/{project_id}",
    response_model=ProjectRead,
    summary="Get project by ID",
)
async def get_project(
    project_id: int,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> ProjectRead:
    project = await project_service.get_by_id(project_id)
    return ProjectRead.model_validate(project)


@router.get(
    "/{project_id}/detail",
    response_model=ProjectDetail,
    summary="Get detailed project with progress metrics",
)
async def get_project_detail(
    project_id: int,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> ProjectDetail:
    return await project_service.get_project_detail(project_id)


@router.patch(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Update project attributes",
)
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProjectRead:
    updated = await project_service.update_project(project_id, payload, current_user)
    return ProjectRead.model_validate(updated)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
)
async def delete_project(
    project_id: int,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    await project_service.delete_project(project_id, current_user)
