"""Video reactions: uniqueness, participant privacy, blocked creators, moderation."""
import uuid

from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from modules.accounts.models import User
from modules.safety.models import UserBlock

from .models import VideoLike, VideoPost


@override_settings(VIDEO_DELIVERY_HOST="videodelivery.net")
class VideoLikeTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.creator = User.objects.create_user(
            email="likes-creator@example.com", display_name="Creator",
            password="StrongPassword!2026", email_verified_at=timezone.now(),
        )
        self.viewer = User.objects.create_user(
            email="likes-viewer@example.com", display_name="Viewer",
            password="StrongPassword!2026", email_verified_at=timezone.now(),
        )
        self.other = User.objects.create_user(
            email="likes-other@example.com", display_name="Other viewer",
            password="StrongPassword!2026", email_verified_at=timezone.now(),
        )
        self.staff = User.objects.create_superuser(
            email="likes-staff@example.com", display_name="Reviewer",
            password="StrongPassword!2026",
        )
        self.video = VideoPost.objects.create(
            creator=self.creator,
            caption="Enrichment with companion animals",
            video_uid="1" * 32,
            rights_attested=True, animal_topic_attested=True,
            processed_at=timezone.now(), moderated_at=timezone.now(),
            moderated_by=self.staff, state=VideoPost.State.APPROVED,
        )
        self.url = f"/api/v1/feed/videos/{self.video.pk}/like/"
        self.client.force_authenticate(self.viewer)

    def feed_item(self):
        response = self.client.get("/api/v1/feed/videos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        return response.data["results"][0]

    def test_guest_feed_has_public_count_but_never_user_identity(self):
        self.client.force_authenticate(user=None)
        item = self.feed_item()
        self.assertEqual(item["likes_count"], 0)
        self.assertFalse(item["is_liked"])
        self.assertNotIn(self.viewer.email, str(item))
        self.assertEqual(self.client.put(self.url, {}, format="json").status_code, 401)
        self.assertEqual(self.client.delete(self.url).status_code, 401)

    def test_single_account_like_is_idempotent_and_private(self):
        first = self.client.put(self.url, {}, format="json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["likes_count"], 1)
        self.assertTrue(first.data["is_liked"])
        self.assertEqual(self.client.put(self.url, {}, format="json").data["likes_count"], 1)
        self.assertEqual(VideoLike.objects.count(), 1)
        self.assertEqual(self.feed_item()["likes_count"], 1)
        self.assertTrue(self.feed_item()["is_liked"])
        self.assertNotIn("email", str(first.data))
        self.assertNotIn("user", first.data)

        self.client.force_authenticate(self.other)
        self.assertFalse(self.feed_item()["is_liked"])
        self.assertEqual(self.feed_item()["likes_count"], 1)
        self.assertEqual(self.client.put(self.url, {}, format="json").data["likes_count"], 2)

        self.client.force_authenticate(user=None)
        self.assertEqual(self.feed_item()["likes_count"], 2)
        self.assertFalse(self.feed_item()["is_liked"])

    def test_unlike_is_idempotent_without_negative_counts(self):
        self.client.put(self.url, {}, format="json")
        first = self.client.delete(self.url)
        second = self.client.delete(self.url)
        self.assertEqual(first.status_code, 200)
        self.assertFalse(first.data["is_liked"])
        self.assertEqual(first.data["likes_count"], 0)
        self.assertEqual(second.data["likes_count"], 0)
        self.assertFalse(VideoLike.objects.exists())

    def test_reaction_requires_verified_active_customer(self):
        self.viewer.email_verified_at = None
        self.viewer.save(update_fields=("email_verified_at",))
        self.assertEqual(self.client.put(self.url, {}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(self.url).status_code, 403)
        self.assertFalse(VideoLike.objects.exists())

    def test_blocking_either_direction_denies_reaction_and_feed(self):
        UserBlock.objects.create(blocker=self.viewer, blocked=self.creator)
        self.assertEqual(self.client.put(self.url, {}, format="json").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 0)
        UserBlock.objects.all().delete()
        UserBlock.objects.create(blocker=self.creator, blocked=self.viewer)
        self.assertEqual(self.client.delete(self.url).status_code, 404)
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 0)

    def test_video_must_be_reviewed_processed_and_currently_approved(self):
        cases = [
            ("pending", "processed_at"),
            ("rejected", "processed_at"),
            ("removed", "processed_at"),
            ("approved", "processed_at"),
            ("approved", "moderated_at"),
        ]
        for state, missing_field in cases:
            self.video.state = state
            original = getattr(self.video, missing_field)
            if state == "approved":
                setattr(self.video, missing_field, None)
            self.video.save(update_fields=("state", missing_field))
            self.assertEqual(self.client.put(self.url, {}, format="json").status_code, 404)
            self.assertEqual(self.client.delete(self.url).status_code, 404)
            setattr(self.video, missing_field, original)
            self.video.save(update_fields=(missing_field,))
        self.assertFalse(VideoLike.objects.exists())

    def test_disabling_stream_delivery_hides_reaction_endpoint(self):
        with override_settings(VIDEO_DELIVERY_HOST=""):
            self.assertEqual(self.client.put(self.url, {}, format="json").status_code, 404)

    def test_inactive_creator_or_unknown_uuid_cannot_be_liked(self):
        self.assertEqual(
            self.client.put(f"/api/v1/feed/videos/{uuid.uuid4()}/like/", {},
                            format="json").status_code,
            404,
        )
        self.creator.is_active = False
        self.creator.save(update_fields=("is_active",))
        self.assertEqual(self.client.put(self.url, {}, format="json").status_code, 404)

    def test_inactive_likers_do_not_inflate_public_counter(self):
        self.client.put(self.url, {}, format="json")
        self.viewer.is_active = False
        self.viewer.save(update_fields=("is_active",))
        self.client.force_authenticate(user=None)
        self.assertEqual(self.feed_item()["likes_count"], 0)
