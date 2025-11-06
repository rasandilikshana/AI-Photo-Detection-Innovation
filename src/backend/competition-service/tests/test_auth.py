"""
Tests for authentication endpoints
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, test_user_data: dict):
    """Test user registration"""
    response = await client.post("/api/v1/auth/register", json=test_user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user_data: dict):
    """Test registration with duplicate email"""
    # Register first user
    await client.post("/api/v1/auth/register", json=test_user_data)

    # Try to register again with same email
    response = await client.post("/api/v1/auth/register", json=test_user_data)

    assert response.status_code == 400
    assert "email already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user_data: dict):
    """Test successful login"""
    # Register user
    await client.post("/api/v1/auth/register", json=test_user_data)

    # Login
    login_data = {"email": test_user_data["email"], "password": test_user_data["password"]}
    response = await client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, test_user_data: dict):
    """Test login with invalid credentials"""
    # Register user
    await client.post("/api/v1/auth/register", json=test_user_data)

    # Try login with wrong password
    login_data = {"email": test_user_data["email"], "password": "wrongpassword"}
    response = await client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user"""
    login_data = {"email": "nonexistent@example.com", "password": "password"}
    response = await client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, authenticated_user: dict):
    """Test getting current user profile"""
    response = await client.get(
        "/api/v1/users/me", headers=authenticated_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == authenticated_user["user"]["email"]
    assert "password" not in data


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test accessing protected endpoint without authentication"""
    response = await client.get("/api/v1/users/me")

    assert response.status_code == 401
