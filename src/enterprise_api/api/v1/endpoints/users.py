"""User management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from enterprise_api.api.deps import (
    get_current_user,
    get_user_service,
    require_admin,
)
from enterprise_api.models.user import User
from enterprise_api.schemas.common import PageMetadata, PaginatedResponse, PaginationParams
from enterprise_api.schemas.user import UserRead, UserUpdate
from enterprise_api.services.user_service import UserService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[UserRead],
    dependencies=[Depends(require_admin)],
    summary="List all users (Admin only)",
)
async def list_users(
    pagination: Annotated[PaginationParams, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> PaginatedResponse[UserRead]:
    users, total = await user_service.list_users(
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    total_pages = (
        (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0
    )
    return PaginatedResponse(
        items=[UserRead.model_validate(u) for u in users],
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
    "/{user_id}",
    response_model=UserRead,
    summary="Get user profile by ID",
)
async def get_user(
    user_id: int,
    user_service: Annotated[UserService, Depends(get_user_service)],
    _: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    user = await user_service.get_by_id(user_id)
    return UserRead.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update user profile",
)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    updated = await user_service.update_user(user_id, payload, current_user)
    return UserRead.model_validate(updated)
