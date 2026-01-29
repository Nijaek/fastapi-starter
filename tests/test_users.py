import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_get_own_user(client: AsyncClient, auth_headers: dict, test_user: User):
    """Test user can get their own profile."""
    response = await client.get(f"/api/v1/users/{test_user.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_get_other_user_forbidden(client: AsyncClient, auth_headers: dict):
    """Test non-superuser cannot access other users' profiles (IDOR protection)."""
    response = await client.get("/api/v1/users/99999", headers=auth_headers)
    assert response.status_code == 404  # Returns 404 to not reveal user existence


@pytest.mark.asyncio
async def test_update_own_user(client: AsyncClient, auth_headers: dict, test_user: User):
    """Test user can update their own profile."""
    response = await client.patch(
        f"/api/v1/users/{test_user.id}",
        headers=auth_headers,
        json={"full_name": "Updated Name"},
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_list_users_requires_superuser(client: AsyncClient, auth_headers: dict):
    """Test listing users requires superuser privileges."""
    response = await client.get("/api/v1/users/", headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_users_as_superuser(client: AsyncClient, superuser_headers: dict):
    """Test superuser can list all users."""
    response = await client.get("/api/v1/users/", headers=superuser_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


@pytest.mark.asyncio
async def test_superuser_can_get_any_user(
    client: AsyncClient, superuser_headers: dict, test_user: User
):
    """Test superuser can access any user's profile."""
    response = await client.get(f"/api/v1/users/{test_user.id}", headers=superuser_headers)
    assert response.status_code == 200
    assert response.json()["email"] == test_user.email


@pytest.mark.asyncio
async def test_delete_user_as_superuser(
    client: AsyncClient, superuser_headers: dict, test_user: User
):
    """Test superuser can delete users."""
    response = await client.delete(f"/api/v1/users/{test_user.id}", headers=superuser_headers)
    assert response.status_code == 204

    # Verify deletion
    response = await client.get(f"/api/v1/users/{test_user.id}", headers=superuser_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_requires_superuser(
    client: AsyncClient, auth_headers: dict, test_user: User
):
    """Test regular user cannot delete users."""
    response = await client.delete(f"/api/v1/users/{test_user.id}", headers=auth_headers)
    assert response.status_code == 403
