# applaunch-api/routers/credentials.py
"""Credential upload and readiness check endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from models.credential import (
    CredentialType,
    CredentialResponse,
    CredentialReadinessResponse,
    KeystoreMetadata,
)
from routers.auth import AuthenticatedUser, get_current_user
from db.supabase_client import get_supabase
from services.s3_service import S3Service
from services.kms_service import KMSService
from config import get_settings

router = APIRouter(prefix="/credentials", tags=["credentials"])


@router.post("/android/keystore", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def upload_android_keystore(
    key_alias: str = Form(...),
    store_password: str = Form(...),
    key_password: str = Form(...),
    keystore_file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Upload an Android keystore (.jks/.p12).

    The keystore file and passwords are encrypted with AWS KMS before storage.
    Raw passwords are never written to logs or the database.
    """
    settings = get_settings()
    supabase = get_supabase()
    kms = KMSService(settings)
    s3 = S3Service(settings)

    keystore_bytes = await keystore_file.read()

    # Encrypt keystore file → S3 (ciphertext)
    encrypted_jks = kms.encrypt(keystore_bytes)
    s3_key = f"credentials/{user.id}/android/keystore.jks.enc"
    s3.upload_bytes(encrypted_jks, settings.s3_bucket_sources, s3_key)

    # Encrypt passwords
    encrypted_store_pw = kms.encrypt(store_password.encode()).hex()
    encrypted_key_pw = kms.encrypt(key_password.encode()).hex()

    # Upsert credential record
    result = supabase.table("credentials").upsert({
        "user_id": user.id,
        "platform": "android",
        "credential_type": CredentialType.android_keystore.value,
        "encrypted_payload": s3_key,
        "metadata": {
            "key_alias": key_alias,
            "encrypted_store_password": encrypted_store_pw,
            "encrypted_key_password": encrypted_key_pw,
        },
    }, on_conflict="user_id,credential_type").execute()

    safe_response = result.data[0].copy()
    return safe_response


@router.post("/android/service-account", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def upload_android_service_account(
    service_account_json: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Upload a Google Play Console service account JSON.
    Encrypted with KMS and stored in S3.
    """
    settings = get_settings()
    supabase = get_supabase()
    kms = KMSService(settings)
    s3 = S3Service(settings)

    json_bytes = await service_account_json.read()
    encrypted = kms.encrypt(json_bytes)
    s3_key = f"credentials/{user.id}/android/service-account.json.enc"
    s3.upload_bytes(encrypted, settings.s3_bucket_sources, s3_key)

    result = supabase.table("credentials").upsert({
        "user_id": user.id,
        "platform": "android",
        "credential_type": CredentialType.android_service_account.value,
        "encrypted_payload": s3_key,
        "metadata": {"filename": service_account_json.filename},
    }, on_conflict="user_id,credential_type").execute()

    return result.data[0]


@router.get("/check", response_model=CredentialReadinessResponse)
async def check_credential_readiness(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Check which credentials the user has uploaded.
    Used by the frontend onboarding wizard and the MCP connector.
    """
    supabase = get_supabase()
    result = (
        supabase.table("credentials")
        .select("credential_type")
        .eq("user_id", user.id)
        .execute()
    )
    types = {row["credential_type"] for row in result.data}

    has_keystore = CredentialType.android_keystore.value in types
    has_sa = CredentialType.android_service_account.value in types
    has_p8 = CredentialType.ios_p8_key.value in types
    has_prov = CredentialType.ios_provisioning.value in types

    return CredentialReadinessResponse(
        android_keystore=has_keystore,
        android_service_account=has_sa,
        ios_p8_key=has_p8,
        ios_provisioning=has_prov,
        android_ready=has_keystore and has_sa,
        ios_ready=has_p8 and has_prov,
    )
