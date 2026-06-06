from __future__ import annotations

import io
import logging
import os
import shutil
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Storage operations — local filesystem or MinIO/S3-compatible."""

    def __init__(self) -> None:
        if settings.use_local_storage:
            os.makedirs(settings.local_storage_path, exist_ok=True)
            logger.info("Using local storage at %s", settings.local_storage_path)
        else:
            import boto3
            from botocore.client import Config
            from botocore.exceptions import ClientError

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
        from botocore.exceptions import ClientError

        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            if error_code in ("404", "NoSuchBucket"):
                self._client.create_bucket(Bucket=self._bucket)
                logger.info("Created MinIO bucket: %s", self._bucket)
            else:
                raise

    # ---- Upload -----------------------------------------------------------------

    async def upload_bytes(
        self,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload raw bytes and return the object name."""
        if settings.use_local_storage:
            dest = os.path.join(settings.local_storage_path, object_name)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(data)
            logger.debug("Saved %d bytes to %s", len(data), dest)
        else:
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
        if settings.use_local_storage:
            dest = os.path.join(settings.local_storage_path, object_name)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(file_path, dest)
            logger.debug("Copied file %s → %s", file_path, dest)
        else:
            self._client.upload_file(
                Filename=file_path,
                Bucket=self._bucket,
                Key=object_name,
                ExtraArgs={"ContentType": content_type},
            )
            logger.debug("Uploaded file %s → %s", file_path, object_name)
        return object_name

    # ---- Download ---------------------------------------------------------------

    async def download_bytes(self, object_name: str) -> bytes:
        """Download an object and return its bytes."""
        if settings.use_local_storage:
            src = os.path.join(settings.local_storage_path, object_name)
            with open(src, "rb") as f:
                return f.read()
        else:
            response = self._client.get_object(Bucket=self._bucket, Key=object_name)
            return response["Body"].read()

    async def download_to_file(self, object_name: str, dest_path: str) -> None:
        """Download an object to a local file path."""
        if settings.use_local_storage:
            src = os.path.join(settings.local_storage_path, object_name)
            shutil.copy2(src, dest_path)
            logger.debug("Copied %s → %s", src, dest_path)
        else:
            self._client.download_file(
                Bucket=self._bucket,
                Key=object_name,
                Filename=dest_path,
            )
            logger.debug("Downloaded %s → %s", object_name, dest_path)

    # ---- Delete -----------------------------------------------------------------

    async def delete_object(self, object_name: str) -> None:
        """Delete a single object."""
        if settings.use_local_storage:
            path = os.path.join(settings.local_storage_path, object_name)
            if os.path.exists(path):
                os.remove(path)
            logger.debug("Deleted %s", path)
        else:
            self._client.delete_object(Bucket=self._bucket, Key=object_name)
            logger.debug("Deleted %s", object_name)

    async def delete_prefix(self, prefix: str) -> int:
        """Delete all objects with a given prefix. Returns count deleted."""
        if settings.use_local_storage:
            base = os.path.join(settings.local_storage_path, prefix)
            deleted = 0
            if os.path.isdir(base):
                shutil.rmtree(base)
                deleted = -1  # unknown count after rmtree
            else:
                # prefix may refer to files with that prefix
                parent = os.path.dirname(base)
                stem = os.path.basename(base)
                if os.path.isdir(parent):
                    for name in os.listdir(parent):
                        if name.startswith(stem):
                            os.remove(os.path.join(parent, name))
                            deleted += 1
            logger.debug("Deleted objects with prefix %s", prefix)
            return deleted
        else:
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

    # ---- URL --------------------------------------------------------------------

    def get_url(self, object_name: str) -> str:
        """Return a URL for the object (static path or presigned URL)."""
        if settings.use_local_storage:
            return f"/files/{object_name}"
        return self.get_presigned_url(object_name)

    def get_presigned_url(self, object_name: str, expires_in: int = 3600) -> str:
        """Generate a pre-signed GET URL (MinIO/S3 only)."""
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": object_name},
            ExpiresIn=expires_in,
        )

    # ---- Existence --------------------------------------------------------------

    async def object_exists(self, object_name: str) -> bool:
        """Check whether an object exists."""
        if settings.use_local_storage:
            path = os.path.join(settings.local_storage_path, object_name)
            return os.path.exists(path)
        else:
            from botocore.exceptions import ClientError

            try:
                self._client.head_object(Bucket=self._bucket, Key=object_name)
                return True
            except ClientError as exc:
                if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                    return False
                raise
