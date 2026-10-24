"""Authentication and authorization service."""

from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_api.core.exceptions import ConflictError, UnauthorizedError
from enterprise_api.core.security import create_access_token, hash_password, verify_password
from enterprise_api.models.user import User
from enterprise_api.repositories.audit_repository import AuditRepository
from enterprise_api.repositories.user_repository import UserRepository
from enterprise_api.schemas.user import Token, UserCreate, UserLogin, UserRead


class AuthService:
    """Orchestrates authentication, user registration, and credential validation."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.audit_repo = AuditRepository(session)

    async def register_user(self, payload: UserCreate) -> User:
        """Register a new user after verifying email uniqueness."""
        existing = await self.user_repo.get_by_email(payload.email)
        if existing:
            raise ConflictError(f"A user with email '{payload.email}' already exists.")

        hashed_pwd = hash_password(payload.password)
        user_data = {
            "email": payload.email.lower().strip(),
            "full_name": payload.full_name.strip(),
            "hashed_password": hashed_pwd,
            "role": payload.role,
            "is_active": True,
        }
        user = await self.user_repo.create(user_data)
        await self.audit_repo.record(
            action="USER_REGISTERED",
            entity_type="user",
            entity_id=str(user.id),
            user_id=user.id,
            details={"email": user.email, "role": user.role.value},
        )
        await self.session.commit()
        return user

    async def authenticate(self, credentials: UserLogin) -> Token:
        """Verify user credentials and produce a signed JWT."""
        user = await self.user_repo.get_by_email(credentials.username)
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise UnauthorizedError("Incorrect email or password.")

        if not user.is_active:
            raise UnauthorizedError("User account is disabled.")

        claims = {
            "email": user.email,
            "role": user.role.value,
            "name": user.full_name,
        }
        token_str = create_access_token(subject=user.id, claims=claims)

        await self.audit_repo.record(
            action="USER_LOGIN",
            entity_type="user",
            entity_id=str(user.id),
            user_id=user.id,
        )
        await self.session.commit()

        return Token(
            access_token=token_str,
            token_type="bearer",
            expires_in=1440 * 60,
            user=UserRead.model_validate(user),
        )
