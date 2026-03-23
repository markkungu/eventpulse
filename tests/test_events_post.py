from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


async def test_post_event_returns_202(client, mock_db_session):
    fake_id = uuid4()

    async def fake_refresh(obj):
        obj.id = fake_id

    mock_db_session.refresh = fake_refresh

    with (
        patch("app.routers.events.get_db", return_value=mock_db_session),
        patch("app.routers.events.process_event.delay"),
    ):
        response = await client.post(
            "/events",
            json={"type": "user.signup", "source": "web", "payload": {"user_id": "123"}},
        )

    assert response.status_code == 202
    data = response.json()
    assert "event_id" in data
    assert data["status"] == "queued"


async def test_post_event_missing_type(client):
    response = await client.post(
        "/events",
        json={"source": "web", "payload": {}},
    )
    assert response.status_code == 422


async def test_post_event_missing_source(client):
    response = await client.post(
        "/events",
        json={"type": "user.signup", "payload": {}},
    )
    assert response.status_code == 422


async def test_post_event_default_payload(client, mock_db_session):
    fake_id = uuid4()

    async def fake_refresh(obj):
        obj.id = fake_id

    mock_db_session.refresh = fake_refresh

    with (
        patch("app.routers.events.get_db", return_value=mock_db_session),
        patch("app.routers.events.process_event.delay"),
    ):
        response = await client.post(
            "/events",
            json={"type": "order.created", "source": "api"},
        )

    assert response.status_code == 202
