"""
Celery worker entry point.
Run with: celery -A worker.main.celery_app worker --loglevel=info
"""
from app.tasks.process_event import celery_app  # noqa: F401
