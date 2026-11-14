"""Video-publication review: MFA, safe transitions and provider-sync failures."""
import json
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from modules.accounts.models import User
from modules.accounts.staff_auth_test_utils import verify_staff_test_session

from .models import VideoPost, VideoReviewEvent
from .provider import StreamUnavailable, set_video_private


@override_settings(
    VIDEO_DELIVERY_HOST="videodelivery.net",
    STREAM_PUBLICATION_ENABLED=True,
    STREAM_ACCOUNT_ID="a" * 32,
    STREAM_API_TOKEN="unit-test-token",
)
class VideoModerationTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.creator = User.objects.create_user(
            email="creator-reviewed@example.com",
            display_name="Animal Video Creator",
            password="CreatorStrong!98765",
            email_verified_at=timezone.now(),
        )
        self.reviewer = User.objects.create_user(
            email="video-reviewer@example.com",
            display_name="Animal Video Moderator",
            password="ReviewerStrong!98765",
            is_staff=True,
            email_verified_at=timezone.now(),
        )
        self.reviewer.user_permissions.add(Permission.objects.get(
            content_type__app_label="social", codename="review_videopost",
        ))
        self.video = VideoPost.objects.create(
            creator=self.creator,
            caption="A calm video of animals being cared for",
            video_uid="f" * 32,
            rights_attested=True,
            animal_topic_attested=True,
            processed_at=timezone.now(),
        )
        self.target = reverse("admin:social_videopost_review", args=[self.video.pk])

    def approve_payload(self, **updates):
        result = {
            "decision": "approve",
            "reason": "Reviewed animal care, safety, commercial policy, and footage rights.",
            "visual_review_confirmed": "on",
            "policy_review_confirmed": "on",
        }
        result.update(updates)
        return result

    def sign_in_reviewer(self):
        verify_staff_test_session(self.client, self.reviewer)

    def test_admin_requires_verified_otp_even_with_video_permission(self):
        self.client.force_login(self.reviewer)
        denied = self.client.get(self.target)
        self.assertEqual(denied.status_code, 302)
        self.assertIn("/admin/login/", denied["Location"])
        self.sign_in_reviewer()
        self.assertEqual(self.client.get(self.target).status_code, 200)

    def test_admin_requires_explicit_video_moderation_permission(self):
        self.reviewer.user_permissions.clear()
        self.sign_in_reviewer()
        response = self.client.get(self.target)
        self.assertEqual(response.status_code, 403)

    def test_process_and_both_review_confirmations_required(self):
        self.sign_in_reviewer()
        with patch("modules.social.moderation.set_video_private") as provider:
            denied = self.client.post(self.target, self.approve_payload(
                visual_review_confirmed="",
            ))
            self.assertEqual(denied.status_code, 200)
            self.video.refresh_from_db()
            self.assertEqual(self.video.state, VideoPost.State.PENDING)
            self.assertEqual(VideoReviewEvent.objects.count(), 0)

            self.video.processed_at = None
            self.video.save(update_fields=("processed_at",))
            denied = self.client.post(self.target, self.approve_payload())
            self.assertEqual(denied.status_code, 200)
            self.assertEqual(VideoReviewEvent.objects.count(), 0)
        provider.assert_not_called()

    def test_reviewer_cannot_approve_their_own_post(self):
        self.video.creator = self.reviewer
        self.video.save(update_fields=("creator",))
        self.sign_in_reviewer()
        with patch("modules.social.moderation.set_video_private") as provider:
            denied = self.client.post(self.target, self.approve_payload())
        self.assertEqual(denied.status_code, 200)
        self.assertEqual(VideoReviewEvent.objects.count(), 0)
        provider.assert_not_called()

    def test_provider_confirmation_before_public_feed_exposure(self):
        self.sign_in_reviewer()
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 0)
        with patch("modules.social.moderation.set_video_private") as provider:
            response = self.client.post(self.target, self.approve_payload())
        self.assertEqual(response.status_code, 302)
        provider.assert_called_once_with(self.video.video_uid, private=False)
        self.video.refresh_from_db()
        self.assertEqual(self.video.state, VideoPost.State.APPROVED)
        self.assertFalse(self.video.visibility_sync_needed)
        self.assertEqual(self.video.moderated_by_id, self.reviewer.pk)
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 1)
        event = VideoReviewEvent.objects.get()
        self.assertTrue(event.visual_review_confirmed)
        self.assertTrue(event.policy_review_confirmed)

    def test_provider_outage_leaves_public_feed_hidden_until_retry(self):
        self.sign_in_reviewer()
        with patch("modules.social.moderation.set_video_private", side_effect=StreamUnavailable):
            response = self.client.post(self.target, self.approve_payload())
        self.assertEqual(response.status_code, 302)
        self.video.refresh_from_db()
        self.assertEqual(self.video.state, VideoPost.State.PUBLISHING)
        self.assertTrue(self.video.visibility_sync_needed)
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 0)

        with patch("modules.social.moderation.set_video_private") as provider:
            retry = self.client.post(self.target, {
                "decision": "retry_sync",
                "reason": "Reattempt provider synchronization after a resolved outage.",
            })
        self.assertEqual(retry.status_code, 302)
        provider.assert_called_once_with(self.video.video_uid, private=False)
        self.video.refresh_from_db()
        self.assertEqual(self.video.state, VideoPost.State.APPROVED)
        self.assertEqual(VideoReviewEvent.objects.count(), 2)
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 1)

    def test_rejection_never_calls_provider_or_exposes_video(self):
        self.sign_in_reviewer()
        with patch("modules.social.moderation.set_video_private") as provider:
            response = self.client.post(self.target, {
                "decision": "reject",
                "reason": "Unsafe animal content; publication is not permitted here.",
            })
        self.assertEqual(response.status_code, 302)
        provider.assert_not_called()
        self.video.refresh_from_db()
        self.assertEqual(self.video.state, VideoPost.State.REJECTED)
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 0)
        self.assertEqual(VideoReviewEvent.objects.count(), 1)

    def test_emergency_removal_hides_feed_before_provider_confirmation(self):
        self.sign_in_reviewer()
        with patch("modules.social.moderation.set_video_private"):
            approved = self.client.post(self.target, self.approve_payload())
        self.assertEqual(approved.status_code, 302)
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 1)

        with patch("modules.social.moderation.set_video_private", side_effect=StreamUnavailable):
            removed = self.client.post(self.target, {
                "decision": "remove",
                "reason": "Urgent welfare incident: remove media from all public surfaces.",
            })
        self.assertEqual(removed.status_code, 302)
        self.video.refresh_from_db()
        self.assertEqual(self.video.state, VideoPost.State.REMOVED)
        self.assertTrue(self.video.visibility_sync_needed)
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 0)

        with patch("modules.social.moderation.set_video_private") as provider:
            retry = self.client.post(self.target, {
                "decision": "retry_sync",
                "reason": "Retry immediate Stream video access revocation with operator.",
            })
        self.assertEqual(retry.status_code, 302)
        provider.assert_called_once_with(self.video.video_uid, private=True)
        self.video.refresh_from_db()
        self.assertFalse(self.video.visibility_sync_needed)
        self.assertEqual(self.video.state, VideoPost.State.REMOVED)
        self.assertEqual(VideoReviewEvent.objects.count(), 3)


@override_settings(STREAM_ACCOUNT_ID="a" * 32, STREAM_API_TOKEN="secret-fixture")
class StreamVisibilityApiTests(APITestCase):
    def result_stub(self, uid="f" * 32, private=True):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            "success": True,
            "result": {"uid": uid, "requireSignedURLs": private},
        }).encode("utf-8")
        return response

    def test_uses_cloudflare_post_not_patch(self):
        with patch(
            "modules.social.provider.urllib.request.urlopen",
            return_value=self.result_stub(private=True),
        ) as call:
            set_video_private("f" * 32, private=True)
        sent = call.call_args.args[0]
        self.assertEqual(sent.get_method(), "POST")
        self.assertEqual(json.loads(sent.data), {"requireSignedURLs": True})
        self.assertEqual(
            sent.full_url,
            "https://api.cloudflare.com/client/v4/accounts/"
            + ("a" * 32) + "/stream/" + ("f" * 32),
        )
        self.assertEqual(sent.get_header("Authorization"), "Bearer secret-fixture")

    def test_provider_response_must_confirm_visibility_and_video_identity(self):
        for payload in (
            {"success": True, "result": {"uid": "e" * 32, "requireSignedURLs": True}},
            {"success": True, "result": {"uid": "f" * 32, "requireSignedURLs": False}},
            {"success": False, "result": {"uid": "f" * 32, "requireSignedURLs": True}},
        ):
            response = MagicMock()
            response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
            with patch(
                "modules.social.provider.urllib.request.urlopen", return_value=response,
            ):
                with self.assertRaises(StreamUnavailable):
                    set_video_private("f" * 32, private=True)

    def test_invalid_video_uid_is_rejected_without_network(self):
        with patch("modules.social.provider.urllib.request.urlopen") as call:
            with self.assertRaises(StreamUnavailable):
                set_video_private("../unsafe", private=False)
        call.assert_not_called()
