# applaunch-api/models/build.py
"""Pydantic schemas for Build jobs."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class BuildStatus(str, Enum):
    queued = "queued"
    building = "building"
    signing = "signing"
    uploading = "uploading"
    done = "done"
    failed = "failed"


class BuildTrack(str, Enum):
    internal = "internal"
    alpha = "alpha"
    beta = "beta"
    production = "production"


class AndroidBuildRequest(BaseModel):
    app_id: str
    version_name: str = "1.0.0"
    version_code: int = 1
    track: BuildTrack = BuildTrack.internal
    # source_zip is provided as multipart file upload — not in this schema


class BuildResponse(BaseModel):
    id: str
    app_id: str
    status: BuildStatus
    platform: str
    version_name: str
    version_code: int
    source_s3_key: Optional[str]
    artifact_s3_key: Optional[str]
    logs: Optional[str]
    error_msg: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class BuildStatusUpdate(BaseModel):
    """Internal model used by Celery workers to update build status."""
    status: BuildStatus
    log_line: Optional[str] = None
    error_msg: Optional[str] = None
    artifact_s3_key: Optional[str] = None
