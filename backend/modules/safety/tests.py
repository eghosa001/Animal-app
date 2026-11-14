"""Safety boundaries: per-user blocks, authorized reports, MFA-only triage."""
import uuid

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from modules.accounts.models import SellerProfile, User
from modules.accounts.staff_auth_test_utils import verify_staff_test_session
from modules.catalog.models import Species
from modules.chats.models import ChatMessage, Conversation
from modules.listings.models import Animal, Listing
from modules.social.models import VideoPost

from .models import SafetyReport, SafetyReportReviewEvent, UserBlock


@override_settings(VIDEO_DELIVERY_HOST="videodelivery.net")
class SafetyBoundaryTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.buyer = User.objects.create_user(
            email="safety-buyer@example.com", display_name="Buyer",
            password="BuyerPassword!2026", email_verified_at=timezone.now(),
        )
        self.seller = User.objects.create_user(
            email="safety-seller@example.com", display_name="Breeder",
            password="SellerPassword!2026", email_verified_at=timezone.now(),
        )
        self.stranger = User.objects.create_user(
            email="safety-stranger@example.com", display_name="Stranger",
            password="StrangerPassword!2026", email_verified_at=timezone.now(),
        )
        self.staff = User.objects.create_user(
            email="safety-reviewer@example.com", display_name="Reviewer",
            password="ReviewerPassword!2026", is_staff=True,
            email_verified_at=timezone.now(),
        )
        self.staff.user_permissions.add(Permission.objects.get(
            content_type__app_label="safety", codename="review_safetyreport",
        ))
        self.profile = SellerProfile.objects.create(
            user=self.seller, business_name="Animal Care",
            adult_attested=True, status=SellerProfile.Status.APPROVED,
        )
        self.species = Species.objects.create(
            name="Dogs", slug="dogs", category=Species.Category.COMPANION,
            trade_enabled=True,
        )
        self.animal = Animal.objects.create(
            owner=self.seller, species=self.species, name="Bella",
        )
        self.listing = Listing.objects.create(
            animal=self.animal, seller=self.seller, title="Approved companion animal",
            description="Test animal description, no claims about its health",
            price_minor=2500000, currency="NGN", region="Lagos",
            status=Listing.Status.ACTIVE,
        )
        self.video = VideoPost.objects.create(
            creator=self.seller, caption="Human-reviewed animal care video",
            video_uid="a" * 32, rights_attested=True,
            animal_topic_attested=True, processed_at=timezone.now(),
            moderated_at=timezone.now(), moderated_by=self.staff,
            state=VideoPost.State.APPROVED,
        )
        self.conversation = Conversation.objects.create(
            listing=self.listing, buyer=self.buyer, seller=self.seller,
        )
        self.message = ChatMessage.objects.create(
            conversation=self.conversation, sender=self.seller,
            body="Meet at the approved location on Saturday.",
            client_nonce=uuid.uuid4(),
        )
        self.client.force_authenticate(self.buyer)

    def report(self, target_type, target_id, **overrides):
        return self.client.post("/api/v1/safety/reports/", {
            "target_type": target_type,
            "target_id": str(target_id),
            "category": "scam",
            "detail": "Suspicious request to transfer funds outside the application.",
            **overrides,
        }, format="json")

    def test_guest_must_authenticate_for_reports_or_blocks(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/api/v1/safety/reports/").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/safety/blocks/").status_code, 401)
        self.assertEqual(self.report("video", self.video.pk).status_code, 401)
        self.assertEqual(self.client.post("/api/v1/safety/blocks/", {
            "blocked_user_id": str(self.seller.pk),
        }, format="json").status_code, 401)

    def test_block_is_scoped_idempotent_and_cannot_block_self(self):
        endpoint = "/api/v1/safety/blocks/"
        bad = self.client.post(endpoint, {
            "blocked_user_id": str(self.buyer.pk),
        }, format="json")
        self.assertEqual(bad.status_code, 400)
        first = self.client.post(endpoint, {
            "blocked_user_id": str(self.seller.pk),
        }, format="json")
        self.assertEqual(first.status_code, 201)
        again = self.client.post(endpoint, {
            "blocked_user_id": str(self.seller.pk),
        }, format="json")
        self.assertEqual(again.status_code, 200)
        self.assertEqual(first.data["id"], again.data["id"])
        mine = self.client.get(endpoint)
        self.assertEqual(mine.data["count"], 1)
        self.assertNotIn(self.seller.email, str(mine.data))
        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.client.get(endpoint).data["count"], 0)
        self.assertEqual(self.client.delete(
            f"/api/v1/safety/blocks/{self.seller.pk}/",
        ).status_code, 404)
        self.client.force_authenticate(self.buyer)
        self.assertEqual(self.client.delete(
            f"/api/v1/safety/blocks/{self.seller.pk}/",
        ).status_code, 204)
        self.assertFalse(UserBlock.objects.exists())

    def test_db_prevents_self_block_and_duplicate_blocks(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserBlock.objects.create(blocker=self.buyer, blocked=self.buyer)
        UserBlock.objects.create(blocker=self.buyer, blocked=self.seller)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserBlock.objects.create(blocker=self.buyer, blocked=self.seller)

    def test_blocking_either_direction_hides_feed_market_and_stops_chat(self):
        listing_url = f"/api/v1/listings/{self.listing.pk}/"
        message_url = (
            f"/api/v1/chats/conversations/{self.conversation.pk}/messages/"
        )
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 1)
        self.assertEqual(self.client.get("/api/v1/listings/").data["count"], 1)
        self.assertEqual(self.client.get(listing_url).status_code, 200)
        UserBlock.objects.create(blocker=self.buyer, blocked=self.seller)
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 0)
        self.assertEqual(self.client.get("/api/v1/listings/").data["count"], 0)
        self.assertEqual(self.client.get(listing_url).status_code, 404)
        self.assertEqual(self.client.post(message_url, {
            "body": "Should not be sent", "client_nonce": str(uuid.uuid4()),
        }, format="json").status_code, 403)
        self.assertEqual(self.client.get(message_url).data["count"], 1)
        self.assertEqual(self.client.post("/api/v1/chats/conversations/", {
            "listing_id": str(self.listing.pk),
        }, format="json").status_code, 403)
        UserBlock.objects.all().delete()
        UserBlock.objects.create(blocker=self.seller, blocked=self.buyer)
        self.assertEqual(self.client.get("/api/v1/feed/videos/").data["count"], 0)
        self.assertEqual(self.client.post(message_url, {
            "body": "Still denied", "client_nonce": str(uuid.uuid4()),
        }, format="json").status_code, 403)
        self.assertEqual(self.client.get(message_url).data["count"], 1)

    def test_account_owner_can_still_manage_own_listing_when_blocked(self):
        UserBlock.objects.create(blocker=self.buyer, blocked=self.seller)
        self.client.force_authenticate(self.seller)
        mine = self.client.get("/api/v1/listings/mine/")
        self.assertEqual(mine.status_code, 200)
        self.assertEqual(mine.data["count"], 1)

    def test_report_all_target_types_with_minimal_private_receipts(self):
        for typ, target in (
            ("video", self.video.pk),
            ("listing", self.listing.pk),
            ("message", self.message.pk),
            ("user", self.seller.pk),
        ):
            response = self.report(typ, target)
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(response.data["target_type"], typ)
            self.assertEqual(response.data["status"], "open")
            self.assertNotIn("detail", response.data)
            self.assertNotIn("reporter", response.data)
        mine = self.client.get("/api/v1/safety/reports/")
        self.assertEqual(mine.status_code, 200)
        self.assertEqual(mine.data["count"], 4)
        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.client.get("/api/v1/safety/reports/").data["count"], 0)
        self.assertEqual(SafetyReport.objects.count(), 4)

    def test_unverified_reporter_invalid_targets_and_too_short_details_denied(self):
        self.assertEqual(self.report("user", self.buyer.pk).status_code, 400)
        self.assertEqual(self.report("message", uuid.uuid4()).status_code, 404)
        self.assertEqual(self.report("video", uuid.uuid4()).status_code, 404)
        self.assertEqual(self.report("user", self.seller.pk, detail="No").status_code, 400)
        self.buyer.email_verified_at = None
        self.buyer.save(update_fields=("email_verified_at",))
        self.assertEqual(self.report("listing", self.listing.pk).status_code, 403)
        self.assertFalse(SafetyReport.objects.exists())

    def test_stranger_cannot_report_another_users_private_message(self):
        self.client.force_authenticate(self.stranger)
        response = self.report("message", self.message.pk)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(SafetyReport.objects.exists())

    def test_hidden_video_cannot_be_reported_by_uninvolved_user(self):
        self.video.state = VideoPost.State.REMOVED
        self.video.save(update_fields=("state",))
        self.assertEqual(self.report("video", self.video.pk).status_code, 404)

    def test_database_rejects_report_with_multiple_targets(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SafetyReport.objects.create(
                    reporter=self.buyer, subject_user=self.seller,
                    video=self.video, category=SafetyReport.Category.SCAM,
                    detail="Improper dual target report should never be persisted.",
                )

    def test_report_admin_requires_second_factor_and_permission(self):
        report = self.report("message", self.message.pk)
        self.assertEqual(report.status_code, 201)
        case = SafetyReport.objects.get()
        target = reverse("admin:safety_safetyreport_review", args=[case.pk])
        self.client.force_authenticate(user=None)
        self.client.force_login(self.staff)
        denied = self.client.get(target)
        self.assertEqual(denied.status_code, 302)
        self.assertIn("/admin/login/", denied["Location"])
        verify_staff_test_session(self.client, self.staff)
        self.assertEqual(self.client.get(target).status_code, 200)
        response = self.client.post(target, {
            "to_status": "actioned",
            "reason": "Reviewed the safety case, retained evidence, and escalated it.",
        })
        self.assertEqual(response.status_code, 302)
        case.refresh_from_db()
        self.assertEqual(case.status, SafetyReport.Status.ACTIONED)
        self.assertEqual(SafetyReportReviewEvent.objects.count(), 1)
        event = SafetyReportReviewEvent.objects.get()
        self.assertEqual(event.reviewer_id, self.staff.pk)
        self.assertEqual(event.from_status, SafetyReport.Status.OPEN)
        # Terminal cases cannot be silently revised without formal appeal.
        self.assertEqual(self.client.post(target, {
            "to_status": "dismissed",
            "reason": "Attempt to overwrite a terminal case without appeal.",
        }).status_code, 200)
        self.assertEqual(SafetyReportReviewEvent.objects.count(), 1)

    def test_staff_without_report_permission_cannot_open_case(self):
        report = self.report("user", self.seller.pk)
        self.assertEqual(report.status_code, 201)
        case = SafetyReport.objects.get()
        self.staff.user_permissions.clear()
        verify_staff_test_session(self.client, self.staff)
        target = reverse("admin:safety_safetyreport_review", args=[case.pk])
        self.assertEqual(self.client.get(target).status_code, 403)
