# applaunch-api/routers/builds.py
"""Build trigger, status, and SSE log-streaming endpoints."""

import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from models.build import AndroidBuildRequest, BuildResponse, BuildStatus, BuildTrack
from routers.auth import AuthenticatedUser, get_current_user
from db.supabase_client import get_supabase
from services.s3_service import S3Service
from config import get_settings
from typing import Optional
import redis.asyncio as aioredis
import uuid

router = APIRouter(prefix="/builds", tags=["builds"])


@router.post("/android", response_model=BuildResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_android_build(
    app_id: str = Form(...),
    version_name: str = Form("1.0.0"),
    version_code: int = Form(1),
    track: BuildTrack = Form(BuildTrack.internal),
    source_zip: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Trigger an Android build job.

    Accepts multipart/form-data with the source ZIP + build parameters.
    Returns a build record immediately with status=queued; actual build is async via Celery.
    """
    settings = get_settings()
    supabase = get_supabase()

    # Verify app belongs to user
    app_result = (
        supabase.table("apps")
        .select("id, package_name, framework")
        .eq("id", app_id)
        .eq("user_id", user.id)
        .maybe_single()
        .execute()
    )
    if not app_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "App not found", "code": "APP_NOT_FOUND"},
        )

    # Upload source ZIP to S3
    build_id = str(uuid.uuid4())
    source_key = f"sources/{user.id}/{app_id}/{build_id}/source.zip"
    s3 = S3Service(settings)
    try:
        content = await source_zip.read()
        s3.upload_bytes(content, settings.s3_bucket_sources, source_key)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"S3 upload failed: {exc}", "code": "S3_UPLOAD_FAILED"},
        )

    # Create build record
    build_result = supabase.table("builds").insert({
        "id": build_id,
        "app_id": app_id,
        "status": BuildStatus.queued.value,
        "platform": "android",
        "version_name": version_name,
        "version_code": version_code,
        "source_s3_key": source_key,
    }).execute()

    # Enqueue Celery task (imported here to avoid circular import at module load)
    from workers.android_build import run_android_build
    run_android_build.apply_async(
        kwargs={
            "build_id": build_id,
            "app_id": app_id,
            "user_id": user.id,
            "source_s3_key": source_key,
            "framework": app_result.data["framework"],
            "version_name": version_name,
            "version_code": version_code,
            "track": track.value,
        },
        task_id=build_id,
    )

    return build_result.data[0]


@router.get("/{build_id}", response_model=BuildResponse)
async def get_build(
    build_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Fetch build status and logs (polling endpoint)."""
    supabase = get_supabase()
    result = (
        supabase.table("builds")
        .select("*, apps!inner(user_id)")
        .eq("id", build_id)
        .eq("apps.user_id", user.id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Build not found", "code": "BUILD_NOT_FOUND"},
        )
    return result.data


@router.get("/{build_id}/stream")
async def stream_build_logs(
    build_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    SSE endpoint — streams live build logs from Redis pub/sub.

    Client receives JSON events: {"log_line": "...", "status": "building"}
    Stream closes automatically when status is done or failed.
    """
    settings = get_settings()

    async def event_generator():
        r = aioredis.from_url(settings.redis_url)
        channel = f"build:{build_id}:logs"
        pubsub = r.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                data = json.loads(message["data"])
                yield f"data: {json.dumps(data)}\n\n"
                if data.get("status") in ("done", "failed"):
                    break
        finally:
            await pubsub.unsubscribe(channel)
            await r.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
