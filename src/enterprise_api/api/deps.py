"""FastAPI dependencies for authentication, role enforcement, and service injection."""

from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_api.core.config import settings
from enterprise_api.core.database import get_db
from enterprise_api.core.exceptions import ForbiddenError, UnauthorizedError
from enterprise_api.core.security import decode_access_token
from enterprise_api.models.enums import UserRole
from enterprise_api.models.user import User
from enterprise_api.repositories.user_repository import UserRepository
from enterprise_api.services.auth_service import AuthService
from enterprise_api.services.project_service import ProjectService
from enterprise_api.services.task_service import TaskService
from enterprise_api.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Validate Bearer JWT and retrieve authenticated user."""
    if not token:
        raise UnauthorizedError("Missing authentication token.")

    try:
        payload = decode_access_token(token)
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise UnauthorizedError("Invalid token payload: missing subject.")
        user_id = int(str(user_id_raw))
    except (jwt.PyJWTError, ValueError):
        raise UnauthorizedError("Token is invalid or expired.") from None

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedError("User associated with this token no longer exists.")

    if not user.is_active:
        raise UnauthorizedError("User account is inactive.")

    return user


def require_roles(*allowed_roles: UserRole) -> Callable[..., User]:
    """Dependency factory restricting route access to specified roles."""

    def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in allowed_roles:
            role_names = ", ".join(r.value for r in allowed_roles)
            raise ForbiddenError(f"Action requires one of the following roles: [{role_names}]")
        return current_user

    return role_checker


# Pre-defined convenience role dependencies
require_admin = require_roles(UserRole.ADMIN)
require_manager_or_admin = require_roles(UserRole.ADMIN, UserRole.MANAGER)


# Service injection factories
def get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    return AuthService(db)


def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    return UserService(db)


def get_project_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ProjectService:
    return ProjectService(db)


def get_task_service(db: Annotated[AsyncSession, Depends(get_db)]) -> TaskService:
    return TaskService(db)
