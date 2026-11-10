"""Signed Stream webhook and private ticket security regression suite."""
import hashlib
import hmac
import json
import time
import uuid
from unittest import mock

from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from modules.accounts.models import User
from .models import VideoPost


@override_settings(
    STREAM_UPLOADS_ENABLED=True,
    STREAM_ACCOUNT_ID="a" * 32,
    STREAM_API_TOKEN="test-fixture-token",
    STREAM_WEBHOOK_SECRET="a-local-signature-fixture",
    VIDEO_DELIVERY_HOST="videodelivery.net",
)
class VideoUploadPipelineTests(APITestCase):
    UID = "f" * 32
    URL = "https://upload.videodelivery.net/" + UID

    def setUp(self):
        cache.clear()
        self.creator = User.objects.create_user(
            email="creator-uploader@example.com", display_name="Poster",
            password="StrongPass!10000", email_verified_at=timezone.now(),
        )
        self.client.force_authenticate(self.creator)

    def provider_stub(self, url=None, uid=None):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            "success": True,
            "result": {"uid": uid or self.UID, "uploadURL": url or self.URL},
        }).encode()
        return mock.patch("modules.social.provider.urllib.request.urlopen", return_value=response)

    def ticket_payload(self):
        return {
            "caption": "A proper animal enrichment video",
            "rights_attested": True,
            "animal_topic_attested": True,
        }

    def create_ticket(self):
        with self.provider_stub() as provider:
            result = self.client.post(
                "/api/v1/feed/videos/upload-ticket/", self.ticket_payload(),
                format="json",
            )
        return result, provider

    def signed_notification(self, payload, secret="a-local-signature-fixture", timestamp=None):
        raw = json.dumps(payload).encode()
        when = int(time.time()) if timestamp is None else timestamp
        digest = hmac.new(
            secret.encode(), str(when).encode() + b"." + raw,
            hashlib.sha256,
        ).hexdigest()
        self.client.force_authenticate(user=None)
        return self.client.post(
            "/api/v1/feed/stream/webhook/", data=raw, content_type="application/json",
            HTTP_WEBHOOK_SIGNATURE=f"time={when},sig1={digest}",
        )

    def test_no_ticket_for_guest_or_unverified_account(self):
        self.client.force_authenticate(user=None)
        result = self.client.post("/api/v1/feed/videos/upload-ticket/", {}, format="json")
        self.assertEqual(result.status_code, 401)
        self.creator.email_verified_at = None
        self.creator.save(update_fields=("email_verified_at",))
        self.client.force_authenticate(self.creator)
        result = self.client.post(
            "/api/v1/feed/videos/upload-ticket/", self.ticket_payload(), format="json",
        )
        self.assertEqual(result.status_code, 403)

    def test_requires_rights_and_animal_topic_attestation(self):
        result = self.client.post(
            "/api/v1/feed/videos/upload-ticket/",
            {**self.ticket_payload(), "rights_attested": False},
            format="json",
        )
        self.assertEqual(result.status_code, 400)
        self.assertFalse(VideoPost.objects.exists())

    def test_private_ticket_issues_single_pending_record(self):
        result, provider = self.create_ticket()
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.data["upload_url"], self.URL)
        self.assertNotIn("test-fixture-token", str(result.data))
        video = VideoPost.objects.get()
        self.assertEqual(video.state, VideoPost.State.PENDING)
        self.assertIsNone(video.processed_at)
        self.assertTrue(video.rights_attested)
        sent = provider.call_args.args[0]
        self.assertEqual(json.loads(sent.data)["maxDurationSeconds"], 60)
        self.assertTrue(json.loads(sent.data)["requireSignedURLs"])
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 0)

    def test_provider_response_cannot_redirect_upload_to_untrusted_host(self):
        with self.provider_stub(url="https://attacker.invalid/upload"):
            result = self.client.post(
                "/api/v1/feed/videos/upload-ticket/", self.ticket_payload(),
                format="json",
            )
        self.assertEqual(result.status_code, 503)
        self.assertFalse(VideoPost.objects.exists())

    def test_uploads_default_off_without_provider_configuration(self):
        with override_settings(STREAM_UPLOADS_ENABLED=False):
            result = self.client.post(
                "/api/v1/feed/videos/upload-ticket/", self.ticket_payload(),
                format="json",
            )
        self.assertEqual(result.status_code, 503)

    def test_rejects_unsigned_or_expired_webhook(self):
        result, _ = self.create_ticket()
        self.assertEqual(result.status_code, 201)
        self.client.force_authenticate(user=None)
        payload = {"uid": self.UID, "readyToStream": True,
                   "status": {"state": "ready", "pctComplete": "100"}, "duration": 10}
        bad = self.client.post(
            "/api/v1/feed/stream/webhook/", payload, format="json",
            HTTP_WEBHOOK_SIGNATURE="time=123,sig1=" + ("f" * 64),
        )
        self.assertEqual(bad.status_code, 403)
        expired = self.signed_notification(payload, timestamp=int(time.time()) - 700)
        self.assertEqual(expired.status_code, 403)
        self.assertIsNone(VideoPost.objects.get().processed_at)

    def test_valid_signature_only_confirms_processing_not_public_approval(self):
        result, _ = self.create_ticket()
        self.assertEqual(result.status_code, 201)
        payload = {"uid": self.UID, "readyToStream": True,
                   "status": {"state": "ready", "pctComplete": "100"}, "duration": 13.5}
        response = self.signed_notification(payload)
        self.assertEqual(response.status_code, 204)
        video = VideoPost.objects.get()
        self.assertIsNotNone(video.processed_at)
        self.assertEqual(video.state, VideoPost.State.PENDING)
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 0)

    def test_ready_processing_rejects_overlong_video(self):
        result, _ = self.create_ticket()
        self.assertEqual(result.status_code, 201)
        response = self.signed_notification({
            "uid": self.UID, "readyToStream": True,
            "status": {"state": "ready", "pctComplete": "100"}, "duration": 61,
        })
        self.assertEqual(response.status_code, 204)
        video = VideoPost.objects.get()
        self.assertEqual(video.state, VideoPost.State.REJECTED)
        self.assertIsNone(video.processed_at)

    def test_provider_error_marks_rejected(self):
        result, _ = self.create_ticket()
        self.assertEqual(result.status_code, 201)
        response = self.signed_notification({
            "uid": self.UID, "readyToStream": False,
            "status": {"state": "error", "errReasonCode": "ERR_NON_VIDEO"},
        })
        self.assertEqual(response.status_code, 204)
        video = VideoPost.objects.get()
        self.assertEqual(video.state, VideoPost.State.REJECTED)
        self.assertEqual(video.processing_error, "ERR_NON_VIDEO")

    def test_daily_upload_cap_is_enforced_even_with_fresh_network_attempt(self):
        for i in range(8):
            VideoPost.objects.create(
                creator=self.creator, caption="Animal video",
                video_uid=uuid.uuid4().hex,
            )
        result = self.client.post(
            "/api/v1/feed/videos/upload-ticket/", self.ticket_payload(), format="json",
        )
        self.assertEqual(result.status_code, 429)
