import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "TestPassword123!",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Test registration fails with weak password."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "short",  # Too short, no uppercase, no digit
        },
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_register_password_without_special_char(client: AsyncClient):
    """Test registration fails without special character in password."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "nospecial@example.com",
            "password": "TestPassword1234",  # Meets length, upper, lower, digit, but no special char
        },
    )
    assert response.status_code == 422
    # Verify the error message mentions special character
    assert "special character" in response.json()["detail"][0]["msg"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration fails with duplicate email."""
    # First registration
    await client.post(
        "/api/v1/auth/register",
        json={"email": "dupe@example.com", "password": "TestPassword123!"},
    )

    # Duplicate registration
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dupe@example.com", "password": "AnotherPassword456!"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    """Test successful login."""
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "TestPassword123!"},
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "TestPassword123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login fails with invalid credentials."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    """Test token refresh."""
    # Register and login
    await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@example.com", "password": "TestPassword123!"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "TestPassword123!"},
    )
    refresh_token = login_response.json()["refresh_token"]

    # Refresh
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    """Test logout revokes refresh token."""
    # Register and login
    await client.post(
        "/api/v1/auth/register",
        json={"email": "logout@example.com", "password": "TestPassword123!"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "logout@example.com", "password": "TestPassword123!"},
    )
    refresh_token = login_response.json()["refresh_token"]

    # Logout
    response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers: dict):
    """Test get current user."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "id" in data


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Test get current user without auth fails."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, db_session: AsyncSession):
    """Test that inactive users cannot login via /auth/login."""
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("TestPassword123!"),
        full_name="Inactive User",
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "TestPassword123!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_form_inactive_user(client: AsyncClient, db_session: AsyncSession):
    """Test that inactive users cannot login via /auth/login/form."""
    user = User(
        email="inactive_form@example.com",
        hashed_password=hash_password("TestPassword123!"),
        full_name="Inactive User Form",
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login/form",
        data={"username": "inactive_form@example.com", "password": "TestPassword123!"},
    )
    assert response.status_code == 401
