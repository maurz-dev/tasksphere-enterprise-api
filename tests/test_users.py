"""Test suite for user management endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_can_list_users(client: AsyncClient, admin_token: str):
    """Ensure administrator can query paginated users list."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/api/v1/users", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "meta" in data
    assert data["meta"]["total_items"] >= 1


@pytest.mark.asyncio
async def test_member_forbidden_to_list_users(client: AsyncClient, member_token: str):
    """Ensure standard member cannot access admin user list (403 Forbidden)."""
    headers = {"Authorization": f"Bearer {member_token}"}
    response = await client.get("/api/v1/users", headers=headers)
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN_ACCESS"


@pytest.mark.asyncio
async def test_user_can_update_own_profile(
    client: AsyncClient,
    member_token: str,
    test_member,
):
    """Ensure member can update their own display name."""
    headers = {"Authorization": f"Bearer {member_token}"}
    payload = {"full_name": "Updated Member Name"}
    response = await client.patch(
        f"/api/v1/users/{test_member.id}", json=payload, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Member Name"
