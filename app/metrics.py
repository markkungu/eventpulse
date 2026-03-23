from prometheus_client import Counter, Histogram

events_received_total = Counter(
    "events_received_total",
    "Total number of events received by the API",
    labelnames=["event_type"],
)

events_processed_total = Counter(
    "events_processed_total",
    "Total number of events processed by the worker",
    labelnames=["status"],
)

event_processing_duration_seconds = Histogram(
    "event_processing_duration_seconds",
    "Time taken to process an event in the Celery worker",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)
