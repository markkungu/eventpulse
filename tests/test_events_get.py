from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.event import Event, EventStatus


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def make_event(**kwargs):
    defaults = dict(
        id=uuid4(),
        type="user.signup",
        source="web",
        payload={"user_id": "abc"},
        status=EventStatus.PROCESSED,
        result={"processed": True},
        created_at=datetime.now(timezone.utc),
        processed_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    event = MagicMock(spec=Event)
    for k, v in defaults.items():
        setattr(event, k, v)
    return event


async def test_get_event_returns_200(client):
    event = make_event()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = event

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.routers.events.get_db", return_value=mock_db):
        response = await client.get(f"/events/{event.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == str(event.id)
    assert data["status"] == "processed"
    assert data["type"] == "user.signup"


async def test_get_event_not_found(client):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.routers.events.get_db", return_value=mock_db):
        response = await client.get(f"/events/{uuid4()}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


async def test_get_event_invalid_uuid(client):
    response = await client.get("/events/not-a-valid-uuid")
    assert response.status_code == 422


async def test_get_event_queued_status(client):
    event = make_event(status=EventStatus.QUEUED, result=None, processed_at=None)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = event

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.routers.events.get_db", return_value=mock_db):
        response = await client.get(f"/events/{event.id}")

    assert response.status_code == 200
    assert response.json()["status"] == "queued"
