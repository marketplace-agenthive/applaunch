# applaunch-api/workers/play_store_publish.py
"""Celery task: publish signed AAB to Google Play Store (placeholder for Phase 2)."""

from workers.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(
    name="workers.play_store_publish.publish_to_play_store",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="publish",
)
def publish_to_play_store(
    self,
    build_id: str,
    app_id: str,
    user_id: str,
    artifact_s3_key: str,
    track: str,
    version_name: str,
    version_code: int,
) -> dict:
    """
    Publish a signed AAB to Google Play Store.

    Phase 2 task — full implementation in Sprint 2.
    For now, raises NotImplementedError to keep the task registered and routable.
    """
    raise NotImplementedError("Play Store publish — Phase 2, Sprint 2")
