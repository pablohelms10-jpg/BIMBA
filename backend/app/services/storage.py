from __future__ import annotations

import io
import logging
from typing import Iterator, Optional

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """MinIO/S3-compatible object storage operations."""

    def __init__(self) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        self._bucket = settings.minio_bucket
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            if error_code in ("404", "NoSuchBucket"):
                self._client.create_bucket(Bucket=self._bucket)
                logger.info("Created MinIO bucket: %s", self._bucket)
            else:
                raise

    async def upload_bytes(
        self,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload raw bytes and return the object name."""
        self._client.put_object(
            Bucket=self._bucket,
            Key=object_name,
            Body=data,
            ContentType=content_type,
        )
        logger.debug("Uploaded %d bytes to %s", len(data), object_name)
        return object_name

    async def upload_file(
        self,
        object_name: str,
        file_path: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a local file by path."""
        self._client.upload_file(
            Filename=file_path,
            Bucket=self._bucket,
            Key=object_name,
            ExtraArgs={"ContentType": content_type},
        )
        logger.debug("Uploaded file %s → %s", file_path, object_name)
        return object_name

    async def download_bytes(self, object_name: str) -> bytes:
        """Download an object and return its bytes."""
        response = self._client.get_object(Bucket=self._bucket, Key=object_name)
        return response["Body"].read()

    async def download_to_file(self, object_name: str, dest_path: str) -> None:
        """Download an object to a local file path."""
        self._client.download_file(
            Bucket=self._bucket,
            Key=object_name,
            Filename=dest_path,
        )
        logger.debug("Downloaded %s → %s", object_name, dest_path)

    async def delete_object(self, object_name: str) -> None:
        """Delete a single object."""
        self._client.delete_object(Bucket=self._bucket, Key=object_name)
        logger.debug("Deleted %s", object_name)

    async def delete_prefix(self, prefix: str) -> int:
        """Delete all objects with a given prefix. Returns count deleted."""
        paginator = self._client.get_paginator("list_objects_v2")
        deleted = 0
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            objects = page.get("Contents", [])
            if not objects:
                continue
            self._client.delete_objects(
                Bucket=self._bucket,
                Delete={"Objects": [{"Key": obj["Key"]} for obj in objects]},
            )
            deleted += len(objects)
        logger.debug("Deleted %d objects with prefix %s", deleted, prefix)
        return deleted

    def get_presigned_url(self, object_name: str, expires_in: int = 3600) -> str:
        """Generate a pre-signed GET URL."""
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": object_name},
            ExpiresIn=expires_in,
        )

    async def object_exists(self, object_name: str) -> bool:
        """Check whether an object exists."""
        try:
            self._client.head_object(Bucket=self._bucket, Key=object_name)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise
