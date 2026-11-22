"""Private comment submission, manual moderation, blocking and accurate counts."""
import uuid

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from modules.accounts.models import User
from modules.accounts.staff_auth_test_utils import verify_staff_test_session
from modules.safety.models import UserBlock

from .models import VideoComment, VideoCommentReviewEvent, VideoLike, VideoPost


@override_settings(VIDEO_DELIVERY_HOST="videodelivery.net")
class VideoCommentTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.creator = User.objects.create_user(
            email="comments-creator@example.com", display_name="Creator",
            password="Secret!Password2026", email_verified_at=timezone.now(),
        )
        self.author = User.objects.create_user(
            email="comments-author@example.com", display_name="Reader",
            password="Secret!Password2026", email_verified_at=timezone.now(),
        )
        self.other = User.objects.create_user(
            email="comments-other@example.com", display_name="Other",
            password="Secret!Password2026", email_verified_at=timezone.now(),
        )
        self.staff = User.objects.create_user(
            email="comments-mod@example.com", display_name="Reviewer",
            password="Secret!Password2026", email_verified_at=timezone.now(),
            is_staff=True,
        )
        self.staff.user_permissions.add(Permission.objects.get(
            content_type__app_label="social", codename="review_videocomment",
        ))
        self.video = VideoPost.objects.create(
            creator=self.creator, caption="Kind care for puppies",
            video_uid="2" * 32, rights_attested=True,
            animal_topic_attested=True,
            processed_at=timezone.now(), moderated_at=timezone.now(),
            moderated_by=self.staff, state=VideoPost.State.APPROVED,
        )
        self.url = f"/api/v1/feed/videos/{self.video.pk}/comments/"
        self.payload = {
            "body": "Lovely animal care and enrichment!",
            "client_nonce": str(uuid.uuid4()),
        }
        self.client.force_authenticate(self.author)

    def test_guests_read_only_published_and_no_private_submission(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.url).data["count"], 0)
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 401)
        self.assertEqual(VideoComment.objects.count(), 0)

    def test_submission_is_pending_private_and_nonce_idempotent(self):
        first = self.client.post(self.url, self.payload, format="json")
        second = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data["id"], second.data["id"])
        self.assertEqual(first.data["status"], "pending")
        self.assertNotIn("body", first.data)
        self.assertEqual(VideoComment.objects.count(), 1)
        self.assertEqual(self.client.get(self.url).data["count"], 0)
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["results"][0]["comments_count"], 0)
        bad = {**self.payload, "body": "Different content"}
        self.assertEqual(self.client.post(self.url, bad, format="json").status_code, 400)
        self.assertEqual(VideoComment.objects.count(), 1)

    def test_unverified_inactive_and_invalid_comment_rejected(self):
        self.author.email_verified_at = None
        self.author.save(update_fields=("email_verified_at",))
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 403)
        self.author.email_verified_at = timezone.now()
        self.author.save(update_fields=("email_verified_at",))
        for body in (" ", "!!!", "ab", "x" * 501):
            payload = {**self.payload, "body": body}
            self.assertEqual(self.client.post(self.url, payload, format="json").status_code, 400)
        self.assertEqual(VideoComment.objects.count(), 0)
        self.author.is_active = False
        self.author.save(update_fields=("is_active",))
        self.assertEqual(self.client.post(self.url, self.payload, format="json").status_code, 403)

    def test_removed_unprocessed_and_blocked_creator_deny_content(self):
        UserBlock.objects.create(blocker=self.creator, blocked=self.author)
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 404)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        UserBlock.objects.all().delete()
        self.video.state = VideoPost.State.REMOVED
        self.video.save(update_fields=("state",))
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 404)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertFalse(VideoComment.objects.exists())

    def test_delivery_off_blocks_comments_and_owner_can_withdraw(self):
        posted = self.client.post(self.url, self.payload, format="json")
        comment_id = posted.data["id"]
        endpoint = self.url + f"{comment_id}/"
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.delete(endpoint).status_code, 404)
        self.client.force_authenticate(self.author)
        with override_settings(VIDEO_DELIVERY_HOST=""):
            self.assertEqual(self.client.get(self.url).status_code, 404)
            self.assertEqual(self.client.post(self.url, {**self.payload, "client_nonce": str(uuid.uuid4())}).status_code, 404)
        self.assertEqual(self.client.delete(endpoint).status_code, 204)
        self.assertEqual(self.client.delete(endpoint).status_code, 204)
        self.assertEqual(VideoComment.objects.get(pk=comment_id).status, "removed")

    def test_mfa_permission_moderates_and_aggregates_without_like_fanout(self):
        posted = self.client.post(self.url, self.payload, format="json")
        comment_id = posted.data["id"]
        review_url = reverse("admin:social_videocomment_review", args=[comment_id])
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(review_url).status_code, 302)
        verify_staff_test_session(self.client, self.staff)
        self.assertEqual(self.client.get(review_url).status_code, 200)
        approved = self.client.post(review_url, {
            "decision": "approve", "reason": "Reviewed this animal care comment; no abuse.",
        })
        self.assertEqual(approved.status_code, 302)
        self.assertEqual(VideoComment.objects.get(pk=comment_id).status, "approved")
        self.assertEqual(VideoCommentReviewEvent.objects.count(), 1)
        self.client.logout()
        self.client.force_authenticate(self.author)
        self.assertEqual(self.client.get(self.url).data["count"], 1)
        VideoLike.objects.create(user=self.author, video=self.video)
        VideoLike.objects.create(user=self.other, video=self.video)
        another = VideoComment.objects.create(
            author=self.other, video=self.video,
            body="Animal health matters", client_nonce=uuid.uuid4(),
            status=VideoComment.Status.APPROVED,
            moderated_at=timezone.now(), moderated_by=self.staff,
        )
        feed = self.client.get("/api/v1/feed/videos/").data["results"][0]
        self.assertEqual(feed["likes_count"], 2)
        self.assertEqual(feed["comments_count"], 2)
        UserBlock.objects.create(blocker=self.author, blocked=self.other)
        self.assertEqual(self.client.get(self.url).data["count"], 1)
        self.assertNotIn(another.body, str(self.client.get(self.url).data))
        self.client.force_authenticate(self.staff)
        verify_staff_test_session(self.client, self.staff)
        removed = self.client.post(review_url, {
            "decision": "remove",
            "reason": "Removed after confirmed policy violation.",
        })
        self.assertEqual(removed.status_code, 302)
        self.assertEqual(VideoCommentReviewEvent.objects.count(), 2)

    def test_review_requires_permission_and_rejects_self_review(self):
        post = self.client.post(self.url, self.payload, format="json")
        review_url = reverse("admin:social_videocomment_review", args=[post.data["id"]])
        self.staff.user_permissions.clear()
        verify_staff_test_session(self.client, self.staff)
        self.assertEqual(self.client.get(review_url).status_code, 403)
        self.staff.user_permissions.add(Permission.objects.get(
            content_type__app_label="social", codename="review_videocomment",
        ))
        self.client.logout()
        self.author.is_staff = True
        self.author.save(update_fields=("is_staff",))
        self.author.user_permissions.add(Permission.objects.get(
            content_type__app_label="social", codename="review_videocomment",
        ))
        verify_staff_test_session(self.client, self.author)
        denied = self.client.post(review_url, {
            "decision": "approve", "reason": "Attempt to review one's own comment.",
        })
        self.assertEqual(denied.status_code, 200)
        self.assertEqual(VideoComment.objects.get(pk=post.data["id"]).status, "pending")
        self.assertEqual(VideoCommentReviewEvent.objects.count(), 0)
