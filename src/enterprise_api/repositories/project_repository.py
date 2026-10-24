"""Project entity persistence repository."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from enterprise_api.models.enums import TaskStatus
from enterprise_api.models.project import Project
from enterprise_api.models.task import Task
from enterprise_api.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Specialized repository for Project entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Project, session)

    async def get_by_slug(self, slug: str) -> Project | None:
        """Fetch project by slug with owner preloaded."""
        stmt = select(Project).where(Project.slug == slug).options(selectinload(Project.owner))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_details(self, project_id: int) -> Project | None:
        """Fetch project with owner and task relations loaded."""
        stmt = (
            select(Project)
            .where(Project.id == project_id)
            .options(selectinload(Project.owner), selectinload(Project.tasks))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_tasks_by_status(self, project_id: int) -> dict[str, int]:
        """Aggregate counts of tasks per status for a given project."""
        stmt = (
            select(Task.status, func.count(Task.id))
            .where(Task.project_id == project_id)
            .group_by(Task.status)
        )
        result = await self.session.execute(stmt)
        counts: dict[str, int] = {s.value: 0 for s in TaskStatus}
        for status_val, count_val in result.all():
            key = status_val.value if hasattr(status_val, "value") else str(status_val)
            counts[key] = count_val
        return counts
