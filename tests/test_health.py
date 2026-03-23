from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_health_all_ok(client):
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock()
    mock_redis.aclose = AsyncMock()

    with (
        patch("app.routers.health.get_db", return_value=mock_db),
        patch("app.routers.health.aioredis.from_url", return_value=mock_redis),
    ):
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"
    assert data["redis"] == "ok"


async def test_health_db_down(client):
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=Exception("connection refused"))

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock()
    mock_redis.aclose = AsyncMock()

    with (
        patch("app.routers.health.get_db", return_value=mock_db),
        patch("app.routers.health.aioredis.from_url", return_value=mock_redis),
    ):
        response = await client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["db"] == "unavailable"
    assert data["redis"] == "ok"


async def test_health_redis_down(client):
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(side_effect=Exception("connection refused"))
    mock_redis.aclose = AsyncMock()

    with (
        patch("app.routers.health.get_db", return_value=mock_db),
        patch("app.routers.health.aioredis.from_url", return_value=mock_redis),
    ):
        response = await client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["redis"] == "unavailable"
    assert data["db"] == "ok"


async def test_health_both_down(client):
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=Exception("db down"))

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(side_effect=Exception("redis down"))
    mock_redis.aclose = AsyncMock()

    with (
        patch("app.routers.health.get_db", return_value=mock_db),
        patch("app.routers.health.aioredis.from_url", return_value=mock_redis),
    ):
        response = await client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["db"] == "unavailable"
    assert data["redis"] == "unavailable"
