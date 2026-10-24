"""Test suite for authentication and registration endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_registration(client: AsyncClient):
    """Test successful user registration flow."""
    payload = {
        "email": "newuser@tasksphere.io",
        "full_name": "New Developer",
        "password": "SecurePassword123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == "newuser@tasksphere.io"
    assert data["full_name"] == "New Developer"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_duplicate_registration_fails(client: AsyncClient):
    """Test registering the same email twice returns 409 Conflict."""
    payload = {
        "email": "unique@tasksphere.io",
        "full_name": "Unique Person",
        "password": "Password123!",
    }
    resp1 = await client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409
    assert resp2.json()["code"] == "RESOURCE_CONFLICT"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Test login with wrong password returns 401 Unauthorized."""
    resp = await client.post(
        "/api/v1/auth/login/json",
        json={"username": "testadmin@tasksphere.io", "password": "WrongPassword!"},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_get_current_user_profile(client: AsyncClient, admin_token: str):
    """Test /auth/me returns profile of authenticated user."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testadmin@tasksphere.io"
    assert data["role"] == "admin"
