"""Unit tests for services edge cases and domain exceptions."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_api.core.exceptions import (
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from enterprise_api.core.security import hash_password
from enterprise_api.models.enums import UserRole
from enterprise_api.models.user import User
from enterprise_api.schemas.user import UserLogin, UserUpdate
from enterprise_api.services.auth_service import AuthService
from enterprise_api.services.project_service import ProjectService
from enterprise_api.services.user_service import UserService


@pytest.mark.asyncio
async def test_auth_service_inactive_user(db_session: AsyncSession):
    """Ensure inactive user cannot authenticate."""
    inactive_user = User(
        email="inactive@tasksphere.io",
        full_name="Disabled Account",
        hashed_password=hash_password("Password123!"),
        role=UserRole.MEMBER,
        is_active=False,
    )
    db_session.add(inactive_user)
    await db_session.commit()

    service = AuthService(db_session)
    with pytest.raises(UnauthorizedError, match="disabled"):
        await service.authenticate(
            UserLogin(username="inactive@tasksphere.io", password="Password123!")
        )


@pytest.mark.asyncio
async def test_user_service_not_found(db_session: AsyncSession):
    """Ensure querying nonexistent user raises NotFoundError."""
    service = UserService(db_session)
    with pytest.raises(NotFoundError):
        await service.get_by_id(99999)


@pytest.mark.asyncio
async def test_user_service_forbidden_role_change(db_session: AsyncSession, test_member: User):
    """Ensure non-admin cannot elevate own role to admin."""
    service = UserService(db_session)
    with pytest.raises(ForbiddenError):
        await service.update_user(
            test_member.id,
            UserUpdate(role=UserRole.ADMIN),
            actor=test_member,
        )


@pytest.mark.asyncio
async def test_project_service_not_found(db_session: AsyncSession, test_member: User):
    """Ensure querying nonexistent project detail raises NotFoundError."""
    service = ProjectService(db_session)
    with pytest.raises(NotFoundError):
        await service.get_project_detail(99999)


@pytest.mark.asyncio
async def test_task_service_invalid_project_and_not_found(
    db_session: AsyncSession,
    test_member: User,
):
    """Ensure task service raises NotFoundError for invalid project or task."""
    from enterprise_api.schemas.task import TaskCreate
    from enterprise_api.services.task_service import TaskService

    service = TaskService(db_session)
    with pytest.raises(NotFoundError):
        await service.create_task(
            TaskCreate(title="Orphan Task", project_id=99999),
            creator=test_member,
        )

    with pytest.raises(NotFoundError):
        await service.get_by_id(99999)
