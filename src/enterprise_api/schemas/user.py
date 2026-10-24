"""Pydantic V2 schemas for User entity and authentication."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from enterprise_api.models.enums import UserRole


class UserBase(BaseModel):
    """Shared user properties."""

    email: EmailStr = Field(..., description="Unique email address for authentication")
    full_name: str = Field(
        ..., min_length=2, max_length=100, description="Full legal or display name"
    )
    role: UserRole = Field(default=UserRole.MEMBER, description="System permission role")
    is_active: bool = Field(default=True, description="Account active state")


class UserCreate(BaseModel):
    """Payload for user registration / creation."""

    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Strong password containing at least 8 characters",
    )
    role: UserRole | None = UserRole.MEMBER


class UserUpdate(BaseModel):
    """Payload for updating user profile."""

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserRead(UserBase):
    """User representation returned to clients (safe, no password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    """Payload for username/password authentication."""

    username: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Plaintext password")


class Token(BaseModel):
    """JWT bearer token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead


class TokenPayload(BaseModel):
    """Contents decoded from a valid JWT."""

    sub: str
    exp: int
    iat: int
    iss: str
    role: str | None = None
