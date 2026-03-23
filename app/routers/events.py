import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.metrics import events_received_total
from app.models.event import Event
from app.schemas.event import EventCreate, EventQueued, EventResponse
from app.tasks.process_event import process_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=EventQueued)
async def submit_event(body: EventCreate, db: AsyncSession = Depends(get_db)):
    """
    Accept an event, persist it as QUEUED, push to Celery for async processing.
    Returns immediately with the event_id — does not wait for processing.
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

    process_event.delay(
        event_id=str(event.id),
        event_type=event.type,
        source=event.source,
        payload=event.payload,
    )

    events_received_total.labels(event_type=body.type).inc()
    logger.info("Event %s queued (type=%s)", event.id, event.type)
    return EventQueued(event_id=event.id, status="queued")


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Fetch a processed event by its ID.
    Returns 404 if the event does not exist.
    """
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found",
        )

    return event
