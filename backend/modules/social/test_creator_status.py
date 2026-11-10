"""The video creator UI API never exposes other users' private upload records."""
from django.test import override_settings
from rest_framework.test import APITestCase

from modules.accounts.models import User
from .models import VideoPost


class CreatorVideoStatusTests(APITestCase):
    def setUp(self):
        self.first = User.objects.create_user(
            email="first-creator@example.com", display_name="First",
            password="StrongPass!10001",
        )
        self.second = User.objects.create_user(
            email="second-creator@example.com", display_name="Second",
            password="StrongPass!10002",
        )

    def test_capabilities_show_disabled_by_default(self):
        with override_settings(STREAM_UPLOADS_ENABLED=False):
            result = self.client.get("/api/v1/feed/videos/upload-capabilities/")
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.data["enabled"])
        self.assertEqual(result.data["max_duration_seconds"], 60)
        self.assertEqual(result.data["max_file_bytes"], 200_000_000)

    def test_private_status_never_reveals_others_or_stream_uid(self):
        mine = VideoPost.objects.create(
            creator=self.first, caption="Animal video awaiting moderation",
            video_uid="a" * 32,
        )
        VideoPost.objects.create(
            creator=self.second, caption="Private second person's clip",
            video_uid="b" * 32,
        )
        self.assertEqual(self.client.get("/api/v1/feed/videos/mine/").status_code, 401)
        self.client.force_authenticate(self.first)
        result = self.client.get("/api/v1/feed/videos/mine/")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["count"], 1)
        self.assertEqual(result.data["results"][0]["id"], str(mine.pk))
        self.assertFalse(result.data["results"][0]["processed"])
        self.assertNotIn("video_uid", result.data["results"][0])
        self.assertNotIn("upload_url", str(result.data))

    def test_capabilities_are_truthful_when_operator_enabled_uploads(self):
        with override_settings(STREAM_UPLOADS_ENABLED=True):
            result = self.client.get("/api/v1/feed/videos/upload-capabilities/")
        self.assertTrue(result.data["enabled"])
