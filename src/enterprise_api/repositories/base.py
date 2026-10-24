"""Generic async repository interface and implementation."""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_api.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async repository encapsulating common database interactions."""

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id_val: Any) -> ModelType | None:
        """Fetch a single record by primary key."""
        return await self.session.get(self.model, id_val)

    async def list(
        self,
        offset: int = 0,
        limit: int = 20,
        filters: Sequence[Any] | None = None,
        order_by: Any | None = None,
    ) -> list[ModelType]:
        """Retrieve a paginated slice of records with optional filtering."""
        query = select(self.model)
        if filters:
            for condition in filters:
                query = query.where(condition)
        if order_by is not None:
            query = query.order_by(order_by)
        else:
            # Default order by created_at if present or id
            if hasattr(self.model, "id"):
                query = query.order_by(self.model.id.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, filters: Sequence[Any] | None = None) -> int:
        """Count total matching records."""
        query = select(func.count()).select_from(self.model)
        if filters:
            for condition in filters:
                query = query.where(condition)
        result = await self.session.execute(query)
        return int(result.scalar_one() or 0)

    async def create(self, attributes: dict[str, Any]) -> ModelType:
        """Create and persist a new record."""
        instance = self.model(**attributes)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelType, updates: dict[str, Any]) -> ModelType:
        """Apply updates to an existing attached entity."""
        for field, value in updates.items():
            if hasattr(instance, field) and value is not None:
                setattr(instance, field, value)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Delete an existing entity."""
        await self.session.delete(instance)
        await self.session.flush()
