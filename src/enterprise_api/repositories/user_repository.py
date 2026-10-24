"""User entity persistence repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_api.models.user import User
from enterprise_api.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Specialized repository for User entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """Lookup a user by unique lowercase email."""
        stmt = select(User).where(User.email == email.lower().strip())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
