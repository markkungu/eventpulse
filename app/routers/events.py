import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import Event
from app.schemas.event import EventCreate, EventQueued
from app.tasks.process_event import process_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=EventQueued)
async def submit_event(body: EventCreate, db: AsyncSession = Depends(get_db)):
    """
    Accept an event, persist it as QUEUED, push to Celery for async processing.
    Returns immediately with the event_id — do not wait for processing.
    """
    event = Event(
        id=uuid4(),
        type=body.type,
        source=body.source,
        payload=body.payload,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    # Push to Celery queue — non-blocking
    process_event.delay(
        event_id=str(event.id),
        event_type=event.type,
        source=event.source,
        payload=event.payload,
    )

    logger.info("Event %s queued (type=%s)", event.id, event.type)
    return EventQueued(event_id=event.id, status="queued")
