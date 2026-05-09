# applaunch-api/workers/celery_app.py
"""
Celery application configuration.

AL-6: Configure Celery with Redis broker.

Broker and result backend both use Redis.
All long-running tasks (Android build, Play Store publish) go through this queue.
"""

from celery import Celery
from config import get_settings

settings = get_settings()

celery_app = Celery(
    "applaunch",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "workers.android_build",
        "workers.play_store_publish",
    ],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task routing — all build tasks go to the "build" queue
    task_routes={
        "workers.android_build.*": {"queue": "build"},
        "workers.play_store_publish.*": {"queue": "publish"},
    },

    # Worker behavior
    worker_prefetch_multiplier=1,      # One task at a time per worker slot (builds are heavy)
    task_acks_late=True,               # Only ack after task completes (safe retry on crash)
    task_reject_on_worker_lost=True,   # Re-queue if worker dies mid-task

    # Result expiry
    result_expires=86400,              # Keep results for 24 hours

    # Disable the Celery daemon from consuming all memory on large payloads
    worker_max_tasks_per_child=10,
)


@celery_app.task(name="workers.health_check")
def health_check() -> dict:
    """
    Minimal health-check task — used by Railway health probes and smoke tests.

    Usage:
        from workers.celery_app import health_check
        result = health_check.delay()
        print(result.get(timeout=5))  # {"status": "ok"}
    """
    return {"status": "ok"}
