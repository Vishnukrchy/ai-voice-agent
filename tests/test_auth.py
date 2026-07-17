import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_login_rejects_bad_credentials(client):
    response = await client.post(
        "/api/login",
        json={"email": "nonexistent@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_rejects_short_password(client):
    response = await client.post(
        "/api/login",
        json={"email": "admin@example.com", "password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_agents_endpoint_requires_auth(client):
    response = await client.get("/api/agents")
    assert response.status_code in (401, 403)
