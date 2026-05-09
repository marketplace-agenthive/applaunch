# applaunch-api/services/s3_service.py
"""AWS S3 upload/download helpers."""

import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class S3Service:
    """Thin wrapper around boto3 S3 client with structured error handling."""

    def __init__(self, settings):
        self._client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

    def upload_bytes(self, data: bytes, bucket: str, key: str) -> None:
        """Upload raw bytes to S3."""
        try:
            self._client.put_object(Body=data, Bucket=bucket, Key=key)
            logger.info(f"Uploaded {len(data)} bytes to s3://{bucket}/{key}")
        except ClientError as exc:
            logger.error(f"S3 upload failed: {exc}")
            raise

    def download_bytes(self, bucket: str, key: str) -> bytes:
        """Download an object from S3 and return its bytes."""
        try:
            response = self._client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except ClientError as exc:
            logger.error(f"S3 download failed: {exc}")
            raise

    def generate_presigned_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        """Generate a pre-signed download URL valid for `expires_in` seconds."""
        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        except ClientError as exc:
            logger.error(f"Presigned URL generation failed: {exc}")
            raise

    def delete_object(self, bucket: str, key: str) -> None:
        """Delete a single object (used in build cleanup)."""
        try:
            self._client.delete_object(Bucket=bucket, Key=key)
        except ClientError as exc:
            logger.warning(f"S3 delete failed for {key}: {exc}")
