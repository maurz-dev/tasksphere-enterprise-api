"""Project database entity."""

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enterprise_api.models.base import Base, TimestampMixin
from enterprise_api.models.enums import ProjectStatus

if TYPE_CHECKING:
    from enterprise_api.models.task import Task
    from enterprise_api.models.user import User


class Project(Base, TimestampMixin):
    """Project entity grouping tasks under an organizational scope."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, native_enum=False, length=20),
        default=ProjectStatus.ACTIVE,
        nullable=False,
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="owned_projects")
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} slug='{self.slug}' status='{self.status.value}'>"
