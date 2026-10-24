"""Task entity persistence repository."""

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from enterprise_api.models.enums import TaskPriority, TaskStatus
from enterprise_api.models.task import Task
from enterprise_api.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Specialized repository for Task entity operations and filtering."""

    def __init__(self, session: AsyncSession):
        super().__init__(Task, session)

    async def get_with_relations(self, task_id: int) -> Task | None:
        """Fetch task by ID with creator, assignee and project relations loaded."""
        stmt = (
            select(Task)
            .where(Task.id == task_id)
            .options(
                selectinload(Task.creator),
                selectinload(Task.assignee),
                selectinload(Task.project),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        offset: int = 0,
        limit: int = 20,
        project_id: int | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        assignee_id: int | None = None,
        search: str | None = None,
    ) -> tuple[list[Task], int]:
        """Search and filter tasks with total matching count in a single transaction."""
        conditions: list[Any] = []
        if project_id is not None:
            conditions.append(Task.project_id == project_id)
        if status is not None:
            conditions.append(Task.status == status)
        if priority is not None:
            conditions.append(Task.priority == priority)
        if assignee_id is not None:
            conditions.append(Task.assignee_id == assignee_id)
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(or_(Task.title.ilike(pattern), Task.description.ilike(pattern)))

        # Count total
        count_stmt = select(func.count()).select_from(Task)
        if conditions:
            for cond in conditions:
                count_stmt = count_stmt.where(cond)
        count_res = await self.session.execute(count_stmt)
        total = int(count_res.scalar_one() or 0)

        # Fetch records
        query = (
            select(Task)
            .options(selectinload(Task.creator), selectinload(Task.assignee))
            .order_by(Task.created_at.desc())
        )
        if conditions:
            for cond in conditions:
                query = query.where(cond)
        query = query.offset(offset).limit(limit)

        items_res = await self.session.execute(query)
        items = list(items_res.scalars().all())

        return items, total
