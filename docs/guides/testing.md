# Testing Guide

This guide covers how to write and run tests for the FastAPI Starter template.

## Overview

The test suite uses:

| Package | Purpose |
|---------|---------|
| `pytest` | Test framework |
| `pytest-asyncio` | Async test support |
| `pytest-cov` | Code coverage |
| `aiosqlite` | In-memory SQLite for tests |
| `httpx` | Async HTTP client for API tests |

## Running Tests

### Quick Commands

```bash
# Run all tests
make test

# Run with pytest directly
pytest -v

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_auth.py::test_login -v

# Run tests matching a pattern
pytest -k "login" -v
```

### Running in Docker

```bash
# Run tests in the API container
docker compose exec api pytest -v

# Run with coverage
docker compose exec api pytest --cov=app --cov-report=term-missing

# Run specific file
docker compose exec api pytest tests/test_users.py -v
```

### Coverage Reports

```bash
# Terminal coverage report
pytest --cov=app --cov-report=term-missing

# HTML coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# XML report (for CI)
pytest --cov=app --cov-report=xml
```

## Test Architecture

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py      # Fixtures and configuration
├── test_auth.py     # Authentication tests
├── test_health.py   # Health endpoint tests
└── test_users.py    # User management tests
```

### Configuration

Pytest is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

The `asyncio_mode = "auto"` setting means you don't need to add `@pytest.mark.asyncio` to every test (though it's included for clarity).

## Fixtures

Fixtures are defined in `tests/conftest.py`. They handle database setup, authentication, and test data.

### Database Fixtures

#### `setup_database` (autouse)

Automatically creates and drops tables for each test:

```python
@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

This ensures test isolation—each test starts with a clean database.

#### `db_session`

Provides a database session for direct database operations:

```python
@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session
```

### HTTP Client Fixture

#### `client`

Provides an async HTTP client with dependency overrides:

```python
@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

Usage:

```python
async def test_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
```

### Authentication Fixtures

#### `test_user`

Creates a standard test user:

```python
@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    service = UserService(db_session)
    user_data = UserCreate(
        email="testuser@example.com",
        password="TestPassword123!",
        full_name="Test User",
    )
    user = await service.create(user_data)
    await db_session.commit()
    return user
```

#### `auth_headers`

Returns authorization headers for a regular user:

```python
@pytest.fixture
async def auth_headers(test_user: User) -> dict:
    token, _ = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {token}"}
```

Usage:

```python
async def test_protected_route(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
```

#### `superuser` and `superuser_headers`

For testing admin-only functionality:

```python
async def test_admin_route(client: AsyncClient, superuser_headers: dict):
    response = await client.get("/api/v1/users/", headers=superuser_headers)
    assert response.status_code == 200
```

## Writing Tests

### Basic Test Structure

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_example(client: AsyncClient):
    """Test description."""
    response = await client.get("/api/v1/endpoint")
    assert response.status_code == 200
    assert response.json()["key"] == "expected_value"
```

### Testing POST Requests

```python
@pytest.mark.asyncio
async def test_create_resource(client: AsyncClient, auth_headers: dict):
    """Test creating a resource."""
    response = await client.post(
        "/api/v1/resources",
        headers=auth_headers,
        json={
            "name": "Test Resource",
            "description": "A test",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Resource"
    assert "id" in data
```

### Testing Authentication

```python
@pytest.mark.asyncio
async def test_requires_auth(client: AsyncClient):
    """Test endpoint requires authentication."""
    response = await client.get("/api/v1/protected")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_with_auth(client: AsyncClient, auth_headers: dict):
    """Test authenticated request succeeds."""
    response = await client.get("/api/v1/protected", headers=auth_headers)
    assert response.status_code == 200
```

### Testing Authorization (RBAC)

```python
@pytest.mark.asyncio
async def test_regular_user_forbidden(client: AsyncClient, auth_headers: dict):
    """Test regular user cannot access admin endpoint."""
    response = await client.get("/api/v1/admin/users", headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_allowed(client: AsyncClient, superuser_headers: dict):
    """Test admin can access admin endpoint."""
    response = await client.get("/api/v1/admin/users", headers=superuser_headers)
    assert response.status_code == 200
```

### Testing Validation Errors

```python
@pytest.mark.asyncio
async def test_invalid_input(client: AsyncClient):
    """Test validation error response."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "short",
        },
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("email" in str(e).lower() for e in errors)
```

### Testing Error Cases

```python
@pytest.mark.asyncio
async def test_not_found(client: AsyncClient, auth_headers: dict):
    """Test 404 response for missing resource."""
    response = await client.get("/api/v1/users/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_email(client: AsyncClient):
    """Test conflict error for duplicate email."""
    user_data = {"email": "test@example.com", "password": "TestPassword123!"}

    # First registration succeeds
    await client.post("/api/v1/auth/register", json=user_data)

    # Second registration fails
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 409
```

## Test Patterns

### Setup Within Test

For one-off setups, do it inline:

```python
@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    # Setup: create user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "TestPassword123!"},
    )

    # Test: login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "TestPassword123!"},
    )
    assert response.status_code == 200
```

### Using Fixtures for Common Setup

For reusable setup, use fixtures:

```python
# In conftest.py
@pytest.fixture
async def verified_user(db_session: AsyncSession) -> User:
    """User with email verified."""
    user = User(
        email="verified@example.com",
        hashed_password=hash_password("TestPassword123!"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user
```

### Testing Multiple Scenarios

Use parametrize for similar tests with different inputs:

```python
@pytest.mark.parametrize("password,expected_status", [
    ("short", 422),           # Too short
    ("nouppercase123!", 422), # No uppercase
    ("NOLOWERCASE123!", 422), # No lowercase
    ("NoDigitsHere!", 422),   # No digit
    ("ValidPassword123!", 201), # Valid
])
@pytest.mark.asyncio
async def test_password_policy(client: AsyncClient, password: str, expected_status: int):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": f"test-{password[:5]}@example.com", "password": password},
    )
    assert response.status_code == expected_status
```

## Mocking

### Redis Mocking

Redis is mocked at the module level in `conftest.py`:

```python
_fake_redis_client = MagicMock()
_fake_redis_client.setex = AsyncMock(return_value=True)
_fake_redis_client.get = AsyncMock(return_value=None)
_fake_redis_client.exists = AsyncMock(return_value=True)
_fake_redis_client.delete = AsyncMock(return_value=1)
```

### Mocking External Services

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mock(client: AsyncClient):
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        response = await client.post("/api/v1/auth/forgot-password", json={...})

        mock_send.assert_called_once()
```

## Database Testing

### Direct Database Operations

```python
@pytest.mark.asyncio
async def test_service_layer(db_session: AsyncSession):
    """Test service directly without HTTP."""
    service = UserService(db_session)

    user = await service.create(UserCreate(
        email="direct@example.com",
        password="TestPassword123!",
    ))

    assert user.id is not None
    assert user.email == "direct@example.com"
```

### Testing Transactions

```python
@pytest.mark.asyncio
async def test_rollback_on_error(db_session: AsyncSession):
    """Test that errors roll back transactions."""
    service = UserService(db_session)

    # Create first user
    await service.create(UserCreate(email="first@example.com", password="TestPassword123!"))
    await db_session.commit()

    # Try to create duplicate (should fail)
    with pytest.raises(SomeException):
        await service.create(UserCreate(email="first@example.com", password="TestPassword123!"))
```

## Debugging Tests

### Verbose Output

```bash
# Show print statements
pytest -v -s

# Show local variables on failure
pytest --tb=long

# Drop into debugger on failure
pytest --pdb
```

### Running Single Test

```bash
# By name
pytest -k "test_login"

# By path
pytest tests/test_auth.py::test_login

# First failure only
pytest -x
```

### Checking Test Discovery

```bash
# List tests without running
pytest --collect-only
```

## CI Integration

### GitHub Actions Example

```yaml
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: coverage.xml
```

## Best Practices

1. **One assertion focus per test** — Test one behavior, even if multiple asserts are needed to verify it

2. **Descriptive test names** — `test_login_with_invalid_password_returns_401` over `test_login_fail`

3. **Test isolation** — Each test should work independently; don't rely on test order

4. **Use fixtures for reusable setup** — But keep simple setup inline

5. **Test edge cases** — Empty inputs, boundary values, error conditions

6. **Don't test framework code** — Focus on your business logic, not FastAPI internals

7. **Keep tests fast** — Use in-memory SQLite, mock external services

8. **Match production patterns** — If you use async in prod, test async

## Adding New Test Files

1. Create `tests/test_<feature>.py`
2. Import pytest and AsyncClient
3. Use existing fixtures from conftest.py
4. Add `@pytest.mark.asyncio` decorator to async tests

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_new_feature(client: AsyncClient, auth_headers: dict):
    """Test the new feature."""
    response = await client.get("/api/v1/new-feature", headers=auth_headers)
    assert response.status_code == 200
```
