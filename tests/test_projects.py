"""Test suite for project management and metric aggregation."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_project_crud_lifecycle(client: AsyncClient, admin_token: str):
    """Test full project CRUD lifecycle with automatic slugification."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create Project
    create_payload = {
        "title": "Quantum Computing Platform",
        "description": "Enterprise SDK for qubit simulation",
        "status": "active",
    }
    create_resp = await client.post("/api/v1/projects", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    project = create_resp.json()
    assert project["title"] == "Quantum Computing Platform"
    assert project["slug"] == "quantum-computing-platform"
    project_id = project["id"]

    # 2. Get Project Detail
    detail_resp = await client.get(f"/api/v1/projects/{project_id}/detail", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == project_id
    assert detail["total_tasks"] == 0
    assert detail["completed_tasks"] == 0

    # 3. Update Project
    update_payload = {"title": "Quantum Computing Platform V2"}
    update_resp = await client.patch(
        f"/api/v1/projects/{project_id}", json=update_payload, headers=headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Quantum Computing Platform V2"
    assert update_resp.json()["slug"] == "quantum-computing-platform-v2"

    # 4. Delete Project
    del_resp = await client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert del_resp.status_code == 204

    # 5. Verify Not Found
    get_resp = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_list_projects_paginated(client: AsyncClient, admin_token: str):
    """Test listing projects with pagination metadata."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    for i in range(3):
        await client.post(
            "/api/v1/projects", json={"title": f"Batch Project {i}"}, headers=headers
        )

    res = await client.get("/api/v1/projects?page=1&page_size=2", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 2
    assert data["meta"]["page"] == 1
    assert data["meta"]["page_size"] == 2
    assert data["meta"]["has_next"] is True
