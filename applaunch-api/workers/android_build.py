# applaunch-api/workers/android_build.py
"""
Celery task: Android build pipeline.

Flow: download source → spawn Docker builder → sign AAB → upload to S3 → update DB.
"""

import os
import json
import shutil
import logging
import tempfile
from datetime import datetime, timezone

import docker
import redis

from workers.celery_app import celery_app
from config import get_settings
from db.supabase_client import get_supabase
from services.s3_service import S3Service
from services.kms_service import KMSService
from models.build import BuildStatus

logger = logging.getLogger(__name__)

BUILDER_IMAGE = "ghcr.io/applaunch/android-builder:latest"


def _publish_log(r: redis.Redis, build_id: str, line: str, status: str) -> None:
    """Push a log event to the Redis pub/sub channel for this build."""
    r.publish(
        f"build:{build_id}:logs",
        json.dumps({"log_line": line, "status": status}),
    )


def _update_build_status(supabase, build_id: str, **fields) -> None:
    """Update the builds table row for this build."""
    supabase.table("builds").update(fields).eq("id", build_id).execute()


@celery_app.task(
    name="workers.android_build.run_android_build",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    queue="build",
)
def run_android_build(
    self,
    build_id: str,
    app_id: str,
    user_id: str,
    source_s3_key: str,
    framework: str,
    version_name: str,
    version_code: int,
    track: str,
) -> dict:
    """
    Full Android build pipeline task.

    Steps:
    1. Update status → building
    2. Download source ZIP from S3
    3. Decrypt keystore from KMS + S3
    4. Spawn Docker builder container
    5. Stream container logs → Redis pub/sub
    6. Upload signed AAB to S3
    7. Update status → done (or failed)
    """
    settings = get_settings()
    supabase = get_supabase()
    s3 = S3Service(settings)
    kms = KMSService(settings)
    r = redis.from_url(settings.redis_url)
    build_dir = None

    try:
        # 1. Mark as building
        _update_build_status(supabase, build_id, status=BuildStatus.building.value)
        _publish_log(r, build_id, "Build started", BuildStatus.building.value)

        # 2. Download + extract source ZIP
        build_dir = tempfile.mkdtemp(prefix=f"build_{build_id}_")
        source_dir = os.path.join(build_dir, "source")
        output_dir = os.path.join(build_dir, "output")
        keystore_dir = os.path.join(build_dir, "keystore")
        os.makedirs(source_dir)
        os.makedirs(output_dir)
        os.makedirs(keystore_dir)

        _publish_log(r, build_id, "Downloading source...", BuildStatus.building.value)
        zip_bytes = s3.download_bytes(settings.s3_bucket_sources, source_s3_key)
        zip_path = os.path.join(build_dir, "source.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_bytes)
        shutil.unpack_archive(zip_path, source_dir)

        # 3. Decrypt keystore
        _update_build_status(supabase, build_id, status=BuildStatus.signing.value)
        _publish_log(r, build_id, "Preparing signing credentials...", BuildStatus.signing.value)

        cred_result = (
            supabase.table("credentials")
            .select("encrypted_payload, metadata")
            .eq("user_id", user_id)
            .eq("credential_type", "android_keystore")
            .maybe_single()
            .execute()
        )
        if not cred_result.data:
            raise ValueError("Android keystore not found — upload credentials first")

        cred = cred_result.data
        enc_jks = s3.download_bytes(settings.s3_bucket_sources, cred["encrypted_payload"])
        jks_bytes = kms.decrypt(enc_jks)
        jks_path = os.path.join(keystore_dir, "release.jks")
        with open(jks_path, "wb") as f:
            f.write(jks_bytes)
        os.chmod(jks_path, 0o400)

        meta = cred["metadata"]
        store_pw = kms.decrypt(bytes.fromhex(meta["encrypted_store_password"])).decode()
        key_pw = kms.decrypt(bytes.fromhex(meta["encrypted_key_password"])).decode()

        # 4. Spawn Docker builder
        _update_build_status(supabase, build_id, status=BuildStatus.building.value)
        _publish_log(r, build_id, "Spawning build container...", BuildStatus.building.value)

        docker_client = docker.from_env()
        container_logs = docker_client.containers.run(
            image=BUILDER_IMAGE,
            command="/usr/local/bin/build_android.sh",
            environment={
                "SOURCE_DIR": "/workspace/app",
                "FRAMEWORK": framework,
                "KEYSTORE_PATH": "/workspace/release.jks",
                "KEY_ALIAS": meta["key_alias"],
                "STORE_PASSWORD": store_pw,
                "KEY_PASSWORD": key_pw,
                "OUTPUT_DIR": "/workspace/output",
                "VERSION_CODE": str(version_code),
                "VERSION_NAME": version_name,
            },
            volumes={
                source_dir:    {"bind": "/workspace/app",        "mode": "rw"},
                jks_path:      {"bind": "/workspace/release.jks", "mode": "ro"},
                output_dir:    {"bind": "/workspace/output",      "mode": "rw"},
            },
            mem_limit="4g",
            cpu_period=100000,
            cpu_quota=200000,
            network_mode="none",
            remove=True,
            stdout=True,
            stderr=True,
        )

        # 5. Stream container output lines to Redis
        for line in container_logs.decode().splitlines():
            _publish_log(r, build_id, line, BuildStatus.building.value)

        # 6. Upload AAB artifact
        _update_build_status(supabase, build_id, status=BuildStatus.uploading.value)
        _publish_log(r, build_id, "Uploading artifact...", BuildStatus.uploading.value)

        aab_path = os.path.join(output_dir, "release.aab")
        if not os.path.exists(aab_path):
            raise FileNotFoundError("Build completed but release.aab not found")

        artifact_key = f"artifacts/{user_id}/{app_id}/{build_id}/release.aab"
        with open(aab_path, "rb") as f:
            s3.upload_bytes(f.read(), settings.s3_bucket_artifacts, artifact_key)

        # 7. Mark done
        now = datetime.now(timezone.utc).isoformat()
        _update_build_status(
            supabase, build_id,
            status=BuildStatus.done.value,
            artifact_s3_key=artifact_key,
            completed_at=now,
        )
        _publish_log(r, build_id, "Build complete!", BuildStatus.done.value)
        return {"status": "done", "artifact_key": artifact_key}

    except Exception as exc:
        logger.exception(f"Build {build_id} failed: {exc}")
        now = datetime.now(timezone.utc).isoformat()
        _update_build_status(
            supabase, build_id,
            status=BuildStatus.failed.value,
            error_msg=str(exc),
            completed_at=now,
        )
        _publish_log(r, build_id, f"BUILD FAILED: {exc}", BuildStatus.failed.value)
        raise self.retry(exc=exc) if self.request.retries < self.max_retries else exc

    finally:
        # Always clean up local build directory
        if build_dir and os.path.exists(build_dir):
            shutil.rmtree(build_dir, ignore_errors=True)
