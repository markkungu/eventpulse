import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Liveness and readiness probe endpoint.
    Returns 200 if DB and Redis are reachable, 503 otherwise.
    """
    checks = {"db": "ok", "redis": "ok"}
    healthy = True

    # Check PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        checks["db"] = "unavailable"
        healthy = False

    # Check Redis
    try:
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
    except Exception as exc:
        logger.error("Redis health check failed: %s", exc)
        checks["redis"] = "unavailable"
        healthy = False

    http_status = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=http_status,
        content={"status": "ok" if healthy else "degraded", **checks},
    )
