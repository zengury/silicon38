# RoboEase API Test Suite

## Overview

This test suite validates the RoboEase backend API behavior through its public HTTP interface. Tests follow TDD principles: one behavior per test, red-green-refactor, and no coupling to implementation details.

## Setup

Tests assume a running instance of the FastAPI backend with a test database. Configuration via environment variables:
- `API_BASE_URL` (default: `http://localhost:8000/api/v1`)
- `TEST_USERNAME` (default: `testadmin`)
- `TEST_PASSWORD` (default: `testpassword123`)

## Test Files

### `test_auth.py`

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app  # Assuming FastAPI app instance

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as ac:
        yield ac

@pytest.fixture
async def auth_token(client):
    response = await client.post("/auth/login", json={"username": "testadmin", "password": "testpassword123"})
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]

@pytest.mark.asyncio
async def test_user_can_login_with_valid_credentials(client):
    response = await client.post("/auth/login", json={"username": "testadmin", "password": "testpassword123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600

@pytest.mark.asyncio
async def test_user_cannot_login_with_invalid_password(client):
    response = await client.post("/auth/login", json={"username": "testadmin", "password": "wrongpassword"})
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "AUTHENTICATION_ERROR"

@pytest.mark.asyncio
async def test_user_cannot_login_with_nonexistent_username(client):
    response = await client.post("/auth/login", json={"username": "nonexistent", "password": "testpassword123"})
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "AUTHENTICATION_ERROR"

@pytest.mark.asyncio
async def test_user_can_refresh_token_with_valid_refresh_token(client, auth_token):
    # First, get a refresh token via login
    login_resp = await client.post("/auth/login", json={"username": "testadmin", "password": "testpassword123"})
    refresh_token = login_resp.json()["refresh_token"]
    response = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

@pytest.mark.asyncio
async def test_user_cannot_refresh_with_invalid_refresh_token(client):
    response = await client.post("/auth/refresh", json={"refresh_token": "invalid_token"})
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "AUTHENTICATION_ERROR"

@pytest.mark.asyncio
async def test_user_can_logout(client, auth_token):
    response = await client.post("/auth/logout", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_user_cannot_access_protected_endpoint_without_token(client):
    response = await client.get("/users")
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "AUTHENTICATION_ERROR"

@pytest.mark.asyncio
async def test_user_can_introspect_valid_token(client, auth_token):
    response = await client.get("/auth/introspect", params={"token": auth_token})
    assert response.status_code == 200
    data = response.json()
    assert data["active"] is True
    assert "user_id" in data
    assert "roles" in data
```

### `test_users.py`

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as ac:
        yield ac

@pytest.fixture
async def admin_token(client):
    response = await client.post("/auth/login", json={"username": "admin", "password": "adminpass123"})
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.mark.asyncio
async def test_admin_can_create_user(client, admin_token):
    response = await client.post(
        "/users",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "display_name": "New User",
            "role": "operator"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["display_name"] == "New User"
    assert data["role"] == "operator"
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data

@pytest.mark.asyncio
async def test_admin_cannot_create_user_with_duplicate_username(client, admin_token):
    # First create
    await client.post(
        "/users",
        json={"username": "duplicate", "email": "dup@example.com", "password": "password123", "display_name": "Dup", "role": "viewer"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    # Second create with same username
    response = await client.post(
        "/users",
        json={"username": "duplicate", "email": "dup2@example.com", "password": "password123", "display_name": "Dup2", "role": "viewer"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 409
    data = response.json()
    assert data["error"] == "CONFLICT"

@pytest.mark.asyncio
async def test_operator_cannot_create_user(client):
    # Login as operator
    login_resp = await client.post("/auth/login", json={"username": "operator", "password": "operatorpass123"})
    token = login_resp.json()["access_token"]
    response = await client.post(
        "/users",
        json={"username": "another", "email": "a@b.com", "password": "password123", "display_name": "A", "role": "viewer"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    data = response.json()
    assert data["error"] == "AUTHORIZATION_ERROR"

@pytest.mark.asyncio
async def test_admin_can_list_users(client, admin_token):
    response = await client.get("/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert data["page"] == 1
    assert data["page_size"] == 20

@pytest.mark.asyncio
async def test_admin_can_get_user_by_id(client, admin_token):
    # Create a user first
    create_resp = await client.post(
        "/users",
        json={"username": "gettest", "email": "get@test.com", "password": "password123", "display_name": "Get Test", "role": "viewer"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    user_id = create_resp.json()["id"]
    response = await client.get(f"/users/{user_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["username"] == "gettest"

@pytest.mark.asyncio
async def test_admin_gets_404_for_nonexistent_user(client, admin_token):
    response = await client.get("/users/00000000-0000-0000-0000-000000000000", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "NOT_FOUND"

@pytest.mark.asyncio
async def test_admin_can_update_user(client, admin_token):
    # Create a user
    create_resp = await client.post(
        "/users",
        json={"username": "updatetest", "email": "update@test.com", "password": "password123", "display_name": "Original", "role": "viewer"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    user_id = create_resp.json()["id"]
    response = await client.patch(
        f"/users/{user_id}",
        json={"display_name": "Updated", "role": "operator"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated"
    assert data["role"] == "operator"

@pytest.mark.asyncio
async def test_admin_can_delete_user(client, admin_token):
    # Create a user
    create_resp = await client.post(
        "/users",
        json={"username": "deletetest", "email": "delete@test.com", "password": "password123", "display_name": "Delete Me", "role": "viewer"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    user_id = create_resp.json()["id"]
    response = await client.delete(f"/users/{user_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 204
    # Verify deletion
    get_resp = await client.get(f"/users/{user_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert get_resp.status_code == 404
```

### `test_robots.py`

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as ac:
        yield ac

@pytest.fixture
async def admin_token(client):
    response = await client.post("/auth/login", json={"username": "admin", "password": "adminpass123"})
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.mark.asyncio
async def test_admin_can_create_robot(client, admin_token):
    response = await client.post(
        "/robots",
        json={
            "name": "Test Robot",
            "robot_type": "star_walker",
            "description": "A test robot",
            "config": {"speed": 1.0}
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Robot"
    assert data["robot_type"] == "star_walker"
    assert data["status"] == "offline"
    assert data["config"] == {"speed": 1.0}
    assert "id" in data
    assert "created_by" in data

@pytest.mark.asyncio
async def test_admin_can_list_robots(client, admin_token):
    response = await client.get("/robots", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data

@pytest.mark.asyncio
async def test_admin_can_get_robot_by_id(client, admin_token):
    # Create a robot
    create_resp = await client.post(
        "/robots",
        json={"name": "Get Robot", "robot_type": "planning"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    robot_id = create_resp.json()["id"]
    response = await client.get(f"/robots/{robot_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == robot_id
    assert data["name"] == "Get Robot"

@pytest.mark.asyncio
async def test_admin_gets_404_for_nonexistent_robot(client, admin_token):
    response = await client.get("/robots/00000000-0000-0000-0000-000000000000", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "NOT_FOUND"

@pytest.mark.asyncio
async def test_admin_can_update_robot(client, admin_token):
    create_resp = await client.post(
        "/robots",
        json={"name": "Update Robot", "robot_type": "custom"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    robot_id = create_resp.json()["id"]
    response = await client.patch(
        f"/robots/{robot_id}",
        json={"name": "Updated Robot", "status": "busy"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Robot"
    assert data["status"] == "busy"

@pytest.mark.asyncio
async def test_admin_can_delete_robot(client, admin_token):
    create_resp = await client.post(
        "/robots",
        json={"name": "Delete Robot", "robot_type": "star_walker"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    robot_id = create_resp.json()["id"]
    response = await client.delete(f"/robots/{robot_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 204
    get_resp = await client.get(f"/robots/{robot_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert get_resp.status_code == 404

@pytest.mark.asyncio
async def test_admin_can_send_command_to_robot(client, admin_token):
    create_resp = await client.post(
        "/robots",
        json={"name": "Command Robot", "robot_type": "star_walker"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    robot_id = create_resp.json()["id"]
    response = await client.post(
        f"/robots/{robot_id}/command",
        json={"command": "move", "parameters": {"x": 10, "y": 5}, "timeout": 30},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "command_id" in data
    assert data["status"] in ["accepted", "queued", "executing", "completed", "failed"]

@pytest.mark.asyncio
async def test_admin_cannot_send_invalid_command(client, admin_token):
    create_resp = await client.post(
        "/robots",
        json={"name": "Invalid Command Robot", "robot_type": "star_walker"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    robot_id = create_resp.json()["id"]
    response = await client.post(
        f"/robots/{robot_id}/command",
        json={"command": "fly", "parameters": {}},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "VALIDATION_ERROR"

@pytest.mark.asyncio
async def test_admin_can_get_robot_telemetry(client, admin_token):
    create_resp = await client.post(
        "/robots",
        json={"name": "Telemetry Robot", "robot_type": "star_walker"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    robot_id = create_resp.json()["id"]
    response = await client.get(f"/robots/{robot_id}/telemetry", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

### `test_health.py`

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health_endpoint_returns_healthy(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "version" in data
    assert "uptime_seconds" in data
    assert "database" in data
```

## Running Tests

```bash
# Install dependencies
pip install pytest httpx pytest-asyncio

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v
```

## Test Coverage Summary

| Endpoint | Behaviors Tested |
|----------|-----------------|
| POST /auth/login | Valid credentials, invalid password, nonexistent username |
| POST /auth/refresh | Valid refresh token, invalid refresh token |
| POST /auth/logout | Successful logout |
| GET /auth/introspect | Valid token introspection |
| GET /users | List users (admin), unauthorized access |
| POST /users | Create user (admin), duplicate username, unauthorized role |
| GET /users/{id} | Get user by ID, nonexistent user |
| PATCH /users/{id} | Update user |
| DELETE /users/{id} | Delete user |
| GET /robots | List robots |
| POST /robots | Create robot |
| GET /robots/{id} | Get robot by ID, nonexistent robot |
| PATCH /robots/{id} | Update robot |
| DELETE /robots/{id} | Delete robot |
| POST /robots/{id}/command | Send command, invalid command |
| GET /robots/{id}/telemetry | Get telemetry |
| GET /health | Health check |

## Notes

- Tests use `httpx.AsyncClient` with ASGI transport to avoid network calls.
- Authentication tokens are obtained via login fixture.
- Each test is independent and can run in isolation.
- Tests verify HTTP status codes and response body structure, not implementation details.
