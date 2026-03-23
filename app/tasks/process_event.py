import logging
import time
from uuid import UUID

from celery import Celery

from app.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "eventpulse",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="process_event", bind=True, max_retries=3)
def process_event(self, event_id: str, event_type: str, source: str, payload: dict):
    """Process an event from the queue and write result to PostgreSQL."""
    import asyncio

    from sqlalchemy import update

    from app.database import AsyncSessionLocal
    from app.metrics import event_processing_duration_seconds, events_processed_total
    from app.models.event import Event, EventStatus

    logger.info("Processing event %s (type=%s)", event_id, event_type)
    start = time.time()

    try:
        # Simulate processing work
        time.sleep(0.5)
        result = {
            "processed": True,
            "event_type": event_type,
            "source": source,
            "items_count": len(payload),
        }

        async def _update():
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(Event)
                    .where(Event.id == UUID(event_id))
                    .values(status=EventStatus.PROCESSED, result=result)
                )
                await session.commit()

        asyncio.run(_update())

        duration = time.time() - start
        event_processing_duration_seconds.observe(duration)
        events_processed_total.labels(status="processed").inc()
        logger.info("Event %s processed in %.2fs", event_id, duration)
        return result

    except Exception as exc:
        events_processed_total.labels(status="failed").inc()
        logger.error("Failed to process event %s: %s", event_id, exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries)
