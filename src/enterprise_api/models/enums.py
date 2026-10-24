"""Domain enumerations for roles, statuses, and priorities."""

from enum import Enum


class UserRole(str, Enum):
    """User access hierarchy."""

    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"


class ProjectStatus(str, Enum):
    """Lifecycle status of a project."""

    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskStatus(str, Enum):
    """Workflow state of a task."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskPriority(str, Enum):
    """Execution priority of a task."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
