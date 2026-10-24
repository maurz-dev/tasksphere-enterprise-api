"""Test health probe endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Ensure /health returns healthy status with active database connectivity."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert "TaskSphere" in data["app_name"]
