"""Cloudflare Stream ticket and signed callback helpers; fail closed."""
import hashlib
import hmac
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied


class StreamUnavailable(APIException):
    status_code = 503
    default_detail = "Video upload service is not available"
    default_code = "stream_unavailable"


def request_private_upload_ticket(creator_id):
    """Create a time-limited direct upload that is private until later moderation."""
    if not (settings.STREAM_UPLOADS_ENABLED and settings.STREAM_ACCOUNT_ID and settings.STREAM_API_TOKEN):
        raise StreamUnavailable()

    deadline = timezone.now() + timedelta(minutes=15)
    payload = {
        "maxDurationSeconds": 60,
        # An unmoderated UID must not be streamable by any unauthenticated viewer.
        "requireSignedURLs": True,
        "creator": str(creator_id),
        "expiry": deadline.isoformat().replace("+00:00", "Z"),
    }
    request = urllib.request.Request(
        "https://api.cloudflare.com/client/v4/accounts/"
        + settings.STREAM_ACCOUNT_ID
        + "/stream/direct_upload",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + settings.STREAM_API_TOKEN,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            result = json.loads(response.read(64 * 1024))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        raise StreamUnavailable() from None
    if not isinstance(result, dict) or result.get("success") is not True:
        raise StreamUnavailable()
    data = result.get("result")
    if not isinstance(data, dict):
        raise StreamUnavailable()
    uid = data.get("uid", "")
    upload_url = data.get("uploadURL", "")
    url = urllib.parse.urlsplit(upload_url) if isinstance(upload_url, str) else None
    if (
        not isinstance(uid, str)
        or not re.fullmatch(r"[a-fA-F0-9]{32}", uid)
        or url is None
        or url.scheme != "https"
        or url.hostname != "upload.videodelivery.net"
        or url.username is not None
        or url.password is not None
    ):
        raise StreamUnavailable()
    return uid, upload_url, deadline


def verify_webhook_signature(raw_body, signature_header):
    """Cloudflare: HMAC-SHA256 over `time + "." + raw request body`."""
    secret = settings.STREAM_WEBHOOK_SECRET
    if not secret or not isinstance(signature_header, str) or len(signature_header) > 256:
        raise PermissionDenied("Invalid Stream webhook signature")
    try:
        parts = dict(part.split("=", 1) for part in signature_header.split(","))
        timestamp = int(parts["time"])
        supplied = parts["sig1"]
        if not re.fullmatch(r"[0-9a-fA-F]{64}", supplied):
            raise ValueError("bad signature format")
    except (ValueError, KeyError):
        raise PermissionDenied("Invalid Stream webhook signature") from None
    if abs(int(time.time()) - timestamp) > 300:
        raise PermissionDenied("Stream webhook timestamp expired")
    expected = hmac.new(
        secret.encode("utf-8"), str(timestamp).encode("ascii") + b"." + raw_body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, supplied.lower()):
        raise PermissionDenied("Invalid Stream webhook signature")


def set_video_private(video_uid, *, private):
    """Flip Cloudflare Stream's signed-URL requirement after a human decision.

    Only call with an exact server-issued UID. A successful HTTP response is
    insufficient if the returned state does not confirm the desired policy.
    """
    if (
        not re.fullmatch(r"[a-fA-F0-9]{32}", str(video_uid))
        or not settings.STREAM_ACCOUNT_ID
        or not settings.STREAM_API_TOKEN
    ):
        raise StreamUnavailable()
    request = urllib.request.Request(
        "https://api.cloudflare.com/client/v4/accounts/"
        + settings.STREAM_ACCOUNT_ID
        + "/stream/"
        + video_uid,
        data=json.dumps({"requireSignedURLs": private}).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + settings.STREAM_API_TOKEN,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            result = json.loads(response.read(64 * 1024))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        raise StreamUnavailable() from None
    if (
        not isinstance(result, dict)
        or result.get("success") is not True
        or not isinstance(result.get("result"), dict)
        or result["result"].get("requireSignedURLs") is not private
        or result["result"].get("uid") != video_uid
    ):
        raise StreamUnavailable()
