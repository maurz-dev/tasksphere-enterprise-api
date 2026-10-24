"""Project lifecycle business service."""

import re
import unicodedata

from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_api.core.exceptions import ForbiddenError, NotFoundError
from enterprise_api.models.enums import TaskStatus, UserRole
from enterprise_api.models.project import Project
from enterprise_api.models.user import User
from enterprise_api.repositories.audit_repository import AuditRepository
from enterprise_api.repositories.project_repository import ProjectRepository
from enterprise_api.schemas.project import ProjectCreate, ProjectDetail, ProjectUpdate


def slugify(text: str) -> str:
    """Normalize string into a URL-safe lowercase slug."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", text)


class ProjectService:
    """Orchestrates project operations, slug generation, and access control."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.project_repo = ProjectRepository(session)
        self.audit_repo = AuditRepository(session)

    async def _generate_unique_slug(self, title: str) -> str:
        """Create a unique slug, appending a counter if collisions occur."""
        base_slug = slugify(title) or "project"
        slug = base_slug
        counter = 1
        while await self.project_repo.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    async def create_project(self, payload: ProjectCreate, creator: User) -> Project:
        """Create and persist a new project owned by creator."""
        slug = await self._generate_unique_slug(payload.title)
        project_data = {
            "title": payload.title.strip(),
            "slug": slug,
            "description": payload.description,
            "status": payload.status,
            "owner_id": creator.id,
        }
        project = await self.project_repo.create(project_data)
        await self.audit_repo.record(
            action="PROJECT_CREATED",
            entity_type="project",
            entity_id=str(project.id),
            user_id=creator.id,
            details={"title": project.title, "slug": project.slug},
        )
        await self.session.commit()
        return project

    async def get_by_id(self, project_id: int) -> Project:
        """Retrieve project by ID or raise NotFoundError."""
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        return project

    async def get_project_detail(self, project_id: int) -> ProjectDetail:
        """Fetch project details along with task progress metrics."""
        project = await self.project_repo.get_with_details(project_id)
        if not project:
            raise NotFoundError("Project", project_id)

        task_counts = await self.project_repo.count_tasks_by_status(project_id)
        total_tasks = sum(task_counts.values())
        completed_tasks = task_counts.get(TaskStatus.COMPLETED.value, 0)

        detail = ProjectDetail.model_validate(project)
        detail.total_tasks = total_tasks
        detail.completed_tasks = completed_tasks
        return detail

    async def list_projects(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Project], int]:
        """List paginated projects."""
        projects = await self.project_repo.list(offset=offset, limit=limit)
        total = await self.project_repo.count()
        return projects, total

    async def update_project(
        self,
        project_id: int,
        payload: ProjectUpdate,
        actor: User,
    ) -> Project:
        """Update an existing project verifying ownership or admin status."""
        project = await self.get_by_id(project_id)
        if project.owner_id != actor.id and actor.role not in (
            UserRole.ADMIN,
            UserRole.MANAGER,
        ):
            raise ForbiddenError(
                "Only project owner, manager, or admin can edit this project."
            )

        updates = payload.model_dump(exclude_unset=True)
        if "title" in updates and updates["title"] != project.title:
            updates["slug"] = await self._generate_unique_slug(updates["title"])

        updated = await self.project_repo.update(project, updates)
        await self.audit_repo.record(
            action="PROJECT_UPDATED",
            entity_type="project",
            entity_id=str(project.id),
            user_id=actor.id,
            details=updates,
        )
        await self.session.commit()
        return updated

    async def delete_project(self, project_id: int, actor: User) -> None:
        """Delete project verifying ownership or admin status."""
        project = await self.get_by_id(project_id)
        if project.owner_id != actor.id and actor.role != UserRole.ADMIN:
            raise ForbiddenError("Only project owner or admin can delete this project.")

        await self.project_repo.delete(project)
        await self.audit_repo.record(
            action="PROJECT_DELETED",
            entity_type="project",
            entity_id=str(project_id),
            user_id=actor.id,
        )
        await self.session.commit()
