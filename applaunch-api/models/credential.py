# applaunch-api/models/credential.py
"""Pydantic schemas for user credentials (keystores, service accounts)."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class CredentialType(str, Enum):
    android_keystore = "android_keystore"
    android_service_account = "android_service_account"
    ios_p8_key = "ios_p8_key"
    ios_provisioning = "ios_provisioning"


class KeystoreMetadata(BaseModel):
    key_alias: str
    store_password: str       # Will be encrypted before storage — never logged
    key_password: str         # Will be encrypted before storage — never logged
    key_cn: Optional[str] = None


class CredentialResponse(BaseModel):
    id: str
    user_id: str
    platform: str
    credential_type: CredentialType
    metadata: dict            # Stripped of secrets before returning
    created_at: datetime

    model_config = {"from_attributes": True}


class CredentialReadinessResponse(BaseModel):
    """Response for GET /credentials/check."""
    android_keystore: bool
    android_service_account: bool
    ios_p8_key: bool
    ios_provisioning: bool
    android_ready: bool       # True if both android_keystore + android_service_account
    ios_ready: bool           # True if both ios_p8_key + ios_provisioning
