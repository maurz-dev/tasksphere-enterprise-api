"""Pydantic V2 schemas for Audit Log entity."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    """Audit log entry representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: str
    details: dict[str, Any] | None = None
    timestamp: datetime
