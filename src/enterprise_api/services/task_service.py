"""Task lifecycle and state machine business service."""

from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_api.core.exceptions import (
    ForbiddenError,
    InvalidStateTransitionError,
    NotFoundError,
    ValidationError,
)
from enterprise_api.models.enums import TaskPriority, TaskStatus, UserRole
from enterprise_api.models.task import Task
from enterprise_api.models.user import User
from enterprise_api.repositories.audit_repository import AuditRepository
from enterprise_api.repositories.project_repository import ProjectRepository
from enterprise_api.repositories.task_repository import TaskRepository
from enterprise_api.repositories.user_repository import UserRepository
from enterprise_api.schemas.task import TaskCreate, TaskFilterParams, TaskUpdate

# Explicit enterprise workflow state transition matrix
ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.TODO: {TaskStatus.IN_PROGRESS, TaskStatus.ARCHIVED},
    TaskStatus.IN_PROGRESS: {TaskStatus.IN_REVIEW, TaskStatus.TODO, TaskStatus.ARCHIVED},
    TaskStatus.IN_REVIEW: {TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS, TaskStatus.ARCHIVED},
    TaskStatus.COMPLETED: {TaskStatus.ARCHIVED, TaskStatus.IN_PROGRESS},
    TaskStatus.ARCHIVED: {TaskStatus.TODO},
}


class TaskService:
    """Manages task lifecycle, assignment, and state machine validation."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_repo = TaskRepository(session)
        self.project_repo = ProjectRepository(session)
        self.user_repo = UserRepository(session)
        self.audit_repo = AuditRepository(session)

    async def create_task(self, payload: TaskCreate, creator: User) -> Task:
        """Create a new task, ensuring project and assignee validity."""
        project = await self.project_repo.get_by_id(payload.project_id)
        if not project:
            raise NotFoundError("Project", payload.project_id)

        if payload.assignee_id:
            assignee = await self.user_repo.get_by_id(payload.assignee_id)
            if not assignee or not assignee.is_active:
                raise ValidationError("Assigned user does not exist or is inactive.")

        task_data = {
            "title": payload.title.strip(),
            "description": payload.description,
            "status": payload.status or TaskStatus.TODO,
            "priority": payload.priority or TaskPriority.MEDIUM,
            "due_date": payload.due_date,
            "project_id": payload.project_id,
            "creator_id": creator.id,
            "assignee_id": payload.assignee_id,
        }
        task = await self.task_repo.create(task_data)
        await self.audit_repo.record(
            action="TASK_CREATED",
            entity_type="task",
            entity_id=str(task.id),
            user_id=creator.id,
            details={"title": task.title, "project_id": task.project_id},
        )
        await self.session.commit()
        return task

    async def get_by_id(self, task_id: int) -> Task:
        """Fetch task with relations or raise NotFoundError."""
        task = await self.task_repo.get_with_relations(task_id)
        if not task:
            raise NotFoundError("Task", task_id)
        return task

    async def list_tasks(
        self,
        filters: TaskFilterParams,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Task], int]:
        """List tasks according to filters."""
        return await self.task_repo.list_filtered(
            offset=offset,
            limit=limit,
            project_id=filters.project_id,
            status=filters.status,
            priority=filters.priority,
            assignee_id=filters.assignee_id,
            search=filters.search,
        )

    async def update_task(
        self,
        task_id: int,
        payload: TaskUpdate,
        actor: User,
    ) -> Task:
        """Update task properties with transition checks if status is modified."""
        task = await self.get_by_id(task_id)

        # Permission check: Creator, Assignee, Project Owner, Manager, or Admin
        is_owner = task.project.owner_id == actor.id
        is_creator = task.creator_id == actor.id
        is_assignee = task.assignee_id == actor.id
        is_staff = actor.role in (UserRole.ADMIN, UserRole.MANAGER)

        if not (is_owner or is_creator or is_assignee or is_staff):
            raise ForbiddenError("You do not have permission to modify this task.")

        updates = payload.model_dump(exclude_unset=True)

        # Validate status change if present
        if "status" in updates and updates["status"] is not None:
            new_status = updates["status"]
            self._validate_transition(task.status, new_status)

        # Validate assignee if updated
        if "assignee_id" in updates and updates["assignee_id"] is not None:
            assignee = await self.user_repo.get_by_id(updates["assignee_id"])
            if not assignee or not assignee.is_active:
                raise ValidationError("Assigned user does not exist or is inactive.")

        updated = await self.task_repo.update(task, updates)
        await self.audit_repo.record(
            action="TASK_UPDATED",
            entity_type="task",
            entity_id=str(task.id),
            user_id=actor.id,
            details=updates,
        )
        await self.session.commit()
        return updated

    async def transition_status(
        self,
        task_id: int,
        target_status: TaskStatus,
        actor: User,
    ) -> Task:
        """Explicitly transition task status validating state machine rules."""
        task = await self.get_by_id(task_id)
        self._validate_transition(task.status, target_status)

        old_status = task.status
        updated = await self.task_repo.update(task, {"status": target_status})

        await self.audit_repo.record(
            action="TASK_STATUS_TRANSITIONED",
            entity_type="task",
            entity_id=str(task.id),
            user_id=actor.id,
            details={"from": old_status.value, "to": target_status.value},
        )
        await self.session.commit()
        return updated

    async def delete_task(self, task_id: int, actor: User) -> None:
        """Delete task verifying author or management permission."""
        task = await self.get_by_id(task_id)
        is_owner = task.project.owner_id == actor.id
        is_creator = task.creator_id == actor.id
        is_staff = actor.role in (UserRole.ADMIN, UserRole.MANAGER)

        if not (is_owner or is_creator or is_staff):
            raise ForbiddenError(
                "Only task creator, project owner, or admin can delete this task."
            )

        await self.task_repo.delete(task)
        await self.audit_repo.record(
            action="TASK_DELETED",
            entity_type="task",
            entity_id=str(task_id),
            user_id=actor.id,
        )
        await self.session.commit()

    def _validate_transition(self, current: TaskStatus, target: TaskStatus) -> None:
        """Ensure state machine transition is allowed."""
        if current == target:
            return

        valid_targets = ALLOWED_TRANSITIONS.get(current, set())
        if target not in valid_targets:
            allowed_names = ", ".join(s.value for s in valid_targets)
            raise InvalidStateTransitionError(
                current_state=current.value,
                target_state=target.value,
                reason=f"Valid next states are: [{allowed_names}]",
            )
