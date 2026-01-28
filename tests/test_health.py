import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test basic health check endpoint."""
    response = await client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"message": "healthy"}


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """Test readiness check endpoint (verifies database connection)."""
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"message": "ready"}
