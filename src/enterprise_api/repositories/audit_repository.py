"""Audit log persistence repository."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_api.models.audit import AuditLog
from enterprise_api.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    """Repository for storing and querying system audit trails."""

    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)

    async def record(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Create and flush an audit log entry."""
        log_entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            user_id=user_id,
            details=details or {},
        )
        self.session.add(log_entry)
        await self.session.flush()
        return log_entry
