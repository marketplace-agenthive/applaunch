# applaunch-api/services/kms_service.py
"""AWS KMS encrypt/decrypt for user credentials (keystores, service accounts)."""

import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class KMSService:
    """Encrypts and decrypts credential blobs using AWS KMS."""

    def __init__(self, settings):
        self._client = boto3.client(
            "kms",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self._key_arn = settings.kms_key_arn

    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Encrypt plaintext using the KMS CMK.

        Returns the ciphertext blob (bytes). Store this in S3 or DB.
        The raw key never leaves KMS — only ciphertext is stored.
        """
        try:
            response = self._client.encrypt(
                KeyId=self._key_arn,
                Plaintext=plaintext,
            )
            return response["CiphertextBlob"]
        except ClientError as exc:
            logger.error(f"KMS encrypt failed: {exc}")
            raise

    def decrypt(self, ciphertext: bytes) -> bytes:
        """
        Decrypt a KMS ciphertext blob back to plaintext.

        NEVER log the return value — it contains raw credential data.
        """
        try:
            response = self._client.decrypt(
                CiphertextBlob=ciphertext,
                KeyId=self._key_arn,
            )
            return response["Plaintext"]
        except ClientError as exc:
            logger.error(f"KMS decrypt failed: {exc}")
            raise
