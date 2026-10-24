"""Authentication and token issuance endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from enterprise_api.api.deps import get_auth_service, get_current_user
from enterprise_api.models.user import User
from enterprise_api.schemas.user import Token, UserCreate, UserLogin, UserRead
from enterprise_api.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user account",
)
async def register(
    payload: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserRead:
    user = await auth_service.register_user(payload)
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=Token,
    summary="Login to obtain Bearer access token (Swagger UI & Form compatible)",
)
async def login_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    credentials = UserLogin(username=form_data.username, password=form_data.password)
    return await auth_service.authenticate(credentials)


@router.post(
    "/login/json",
    response_model=Token,
    summary="Login via JSON body",
)
async def login_json(
    credentials: UserLogin,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    return await auth_service.authenticate(credentials)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Retrieve current authenticated user profile",
)
async def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    return UserRead.model_validate(current_user)
