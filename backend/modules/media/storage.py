"""Private provider adapter; all bytes are served through authorized Django routes."""
import io
import os
from pathlib import Path

from django.conf import settings

MAX_READ_BYTES = 8 * 1024 * 1024


class MediaStorageError(RuntimeError):
    pass


def backend_name():
    name = getattr(settings, "MEDIA_STORAGE_BACKEND", "local")
    if name not in ("local", "r2"):
        raise MediaStorageError("Unsupported private media backend")
    if name == "local" and not settings.DEBUG:
        raise MediaStorageError("Filesystem private media is permitted only in debug development")
    return name


def r2_client():
    import boto3
    from botocore.config import Config

    endpoint = getattr(settings, "R2_ENDPOINT_URL", "")
    access = getattr(settings, "R2_ACCESS_KEY_ID", "")
    secret = getattr(settings, "R2_SECRET_ACCESS_KEY", "")
    if not endpoint.startswith("https://") or not access or not secret:
        raise MediaStorageError("Private R2 backend is not configured")
    return boto3.client(
        "s3", endpoint_url=endpoint, region_name="auto",
        aws_access_key_id=access, aws_secret_access_key=secret,
        config=Config(signature_version="s3v4", connect_timeout=5, read_timeout=15, retries={"max_attempts": 2}),
    )


def _bucket(kind):
    from .models import MediaAsset
    bucket = (
        getattr(settings, "R2_BUCKET_EVIDENCE", "") if kind == MediaAsset.Kind.SELLER_EVIDENCE
        else getattr(settings, "R2_BUCKET_PHOTOS", "")
    )
    if not bucket:
        raise MediaStorageError("Private R2 bucket is not configured")
    return bucket


def _local_path(key):
    if not key.startswith(("listing-photos/", "seller-evidence/")) or len(key) > 150:
        raise MediaStorageError("Invalid private media object key")
    if ".." in key or key.count("/") != 1 or not key.endswith(".jpg"):
        raise MediaStorageError("Invalid private media object key")
    root = Path(settings.PRIVATE_MEDIA_ROOT).resolve()
    path = (root / key).resolve()
    if not path.is_relative_to(root):
        raise MediaStorageError("Private object path outside storage root")
    return path


def put_object(*, kind, key, body):
    if backend_name() == "local":
        path = _local_path(key)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(body)
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        return
    r2_client().put_object(
        Bucket=_bucket(kind),
        Key=key,
        Body=body,
        ContentType="image/jpeg",
        CacheControl="private, no-store",
    )


def read_object(*, kind, key):
    if backend_name() == "local":
        path = _local_path(key)
        with path.open("rb") as handle:
            body = handle.read(MAX_READ_BYTES + 1)
    else:
        response = r2_client().get_object(Bucket=_bucket(kind), Key=key)
        try:
            body = response["Body"].read(MAX_READ_BYTES + 1)
        finally:
            response["Body"].close()
    if len(body) > MAX_READ_BYTES:
        raise MediaStorageError("Stored media exceeds safe download size")
    return body


def delete_object(*, kind, key):
    if backend_name() == "local":
        _local_path(key).unlink(missing_ok=True)
    else:
        r2_client().delete_object(Bucket=_bucket(kind), Key=key)
