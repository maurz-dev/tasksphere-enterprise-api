"""User management business service."""

from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_api.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from enterprise_api.core.security import hash_password
from enterprise_api.models.enums import UserRole
from enterprise_api.models.user import User
from enterprise_api.repositories.user_repository import UserRepository
from enterprise_api.schemas.user import UserUpdate


class UserService:
    """Manages user profiles, role assignments and account status."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def get_by_id(self, user_id: int) -> User:
        """Fetch user by ID or raise NotFoundError."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return user

    async def list_users(self, offset: int = 0, limit: int = 20) -> tuple[list[User], int]:
        """List paginated users and total count."""
        users = await self.user_repo.list(offset=offset, limit=limit)
        total = await self.user_repo.count()
        return users, total

    async def update_user(
        self,
        target_user_id: int,
        payload: UserUpdate,
        actor: User,
    ) -> User:
        """Update user attributes with role-based permission checks."""
        # Only admins can update other users or change roles
        if actor.id != target_user_id and actor.role != UserRole.ADMIN:
            raise ForbiddenError("You cannot modify other users' profiles.")

        target_user = await self.get_by_id(target_user_id)
        updates = payload.model_dump(exclude_unset=True)

        if "role" in updates and actor.role != UserRole.ADMIN:
            raise ForbiddenError("Only administrators can reassign user roles.")

        if updates.get("email"):
            new_email = updates["email"].lower().strip()
            existing = await self.user_repo.get_by_email(new_email)
            if existing and existing.id != target_user_id:
                raise ConflictError(f"Email '{new_email}' is already taken.")
            updates["email"] = new_email

        if updates.get("password"):
            updates["hashed_password"] = hash_password(updates.pop("password"))

        updated_user = await self.user_repo.update(target_user, updates)
        await self.session.commit()
        return updated_user
