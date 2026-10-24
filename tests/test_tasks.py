"""Test suite for task workflow state machine and filtering."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_task_workflow_and_state_machine(client: AsyncClient, admin_token: str):
    """Test task creation and validate finite state machine transitions."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Setup Project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"title": "DevOps Pipeline Automation"},
        headers=headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Create Task (Initial status: TODO)
    task_payload = {
        "title": "Configure Prometheus Monitoring",
        "description": "Deploy Node Exporter and Grafana dashboards",
        "priority": "high",
        "project_id": project_id,
    }
    task_resp = await client.post("/api/v1/tasks", json=task_payload, headers=headers)
    assert task_resp.status_code == 201
    task = task_resp.json()
    task_id = task["id"]
    assert task["status"] == "todo"

    # 3. Invalid transition: TODO directly to COMPLETED should fail (422)
    invalid_resp = await client.post(
        f"/api/v1/tasks/{task_id}/transition",
        json={"status": "completed"},
        headers=headers,
    )
    assert invalid_resp.status_code == 422
    assert invalid_resp.json()["code"] == "DOMAIN_VALIDATION_ERROR"
    assert "Cannot transition from 'todo' to 'completed'" in invalid_resp.json()["message"]

    # 4. Valid transition 1: TODO -> IN_PROGRESS
    valid_step1 = await client.post(
        f"/api/v1/tasks/{task_id}/transition",
        json={"status": "in_progress"},
        headers=headers,
    )
    assert valid_step1.status_code == 200
    assert valid_step1.json()["status"] == "in_progress"

    # 5. Valid transition 2: IN_PROGRESS -> IN_REVIEW
    valid_step2 = await client.post(
        f"/api/v1/tasks/{task_id}/transition",
        json={"status": "in_review"},
        headers=headers,
    )
    assert valid_step2.status_code == 200
    assert valid_step2.json()["status"] == "in_review"

    # 6. Valid transition 3: IN_REVIEW -> COMPLETED
    valid_step3 = await client.post(
        f"/api/v1/tasks/{task_id}/transition",
        json={"status": "completed"},
        headers=headers,
    )
    assert valid_step3.status_code == 200
    assert valid_step3.json()["status"] == "completed"

    # 7. Query project metrics: completed tasks must now equal 1
    detail_resp = await client.get(f"/api/v1/projects/{project_id}/detail", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["total_tasks"] == 1
    assert detail_resp.json()["completed_tasks"] == 1


@pytest.mark.asyncio
async def test_tasks_filtered_query(client: AsyncClient, admin_token: str):
    """Test filtering tasks by priority, status and search keyword."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Setup Project
    p_resp = await client.post(
        "/api/v1/projects", json={"title": "Security Hardening"}, headers=headers
    )
    p_id = p_resp.json()["id"]

    # Create 2 tasks with distinct priorities
    await client.post(
        "/api/v1/tasks",
        json={"title": "Audit SSL/TLS Ciphers", "priority": "critical", "project_id": p_id},
        headers=headers,
    )
    await client.post(
        "/api/v1/tasks",
        json={"title": "Update README docs", "priority": "low", "project_id": p_id},
        headers=headers,
    )

    # Filter by priority=critical
    filter_resp = await client.get(
        f"/api/v1/tasks?project_id={p_id}&priority=critical", headers=headers
    )
    assert filter_resp.status_code == 200
    items = filter_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Audit SSL/TLS Ciphers"

    # Search keyword
    search_resp = await client.get(
        f"/api/v1/tasks?project_id={p_id}&search=Ciphers", headers=headers
    )
    assert search_resp.status_code == 200
    assert len(search_resp.json()["items"]) == 1


@pytest.mark.asyncio
async def test_task_update_and_delete(
    client: AsyncClient,
    admin_token: str,
    test_member,
):
    """Test updating task details, assigning users, and deletion."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    proj = (
        await client.post(
            "/api/v1/projects", json={"title": "Refactoring Engine"}, headers=headers
        )
    ).json()

    task = (
        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Migrate Database Queries",
                "project_id": proj["id"],
                "assignee_id": test_member.id,
            },
            headers=headers,
        )
    ).json()

    # Get single task detail
    detail = (await client.get(f"/api/v1/tasks/{task['id']}", headers=headers)).json()
    assert detail["assignee"]["email"] == test_member.email

    # Update task title and priority
    update_res = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"title": "Migrate Database Queries to Async", "priority": "critical"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Migrate Database Queries to Async"
    assert update_res.json()["priority"] == "critical"

    # Delete task
    del_res = await client.delete(f"/api/v1/tasks/{task['id']}", headers=headers)
    assert del_res.status_code == 204

    # Verify 404
    not_found = await client.get(f"/api/v1/tasks/{task['id']}", headers=headers)
    assert not_found.status_code == 404
