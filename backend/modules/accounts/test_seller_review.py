"""Security regressions for the manual seller-review lifecycle."""
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from modules.catalog.models import Species
from modules.listings.models import Animal, Listing, ListingEvent

from .forms import SellerReviewForm
from .models import SellerProfile, SellerReviewEvent, User
from .review_service import review_seller


CASE_REF = "CASE-2026-001"
RATIONALE = "Identity evidence reviewed and applicant details matched the secure case."


class SellerReviewTests(APITestCase):
    def setUp(self):
        self.applicant = User.objects.create_user(
            email="animal-owner@example.com",
            password="ReallyStrong!2026",
            display_name="Animal Owner",
            email_verified_at=timezone.now(),
        )
        self.seller = SellerProfile.objects.create(
            user=self.applicant,
            business_name="Green Meadow Animals",
            adult_attested=True,
        )
        self.reviewer = User.objects.create_user(
            email="moderator@example.com",
            password="Moderation!2026",
            display_name="Moderator",
            is_staff=True,
        )
        self.reviewer.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="accounts",
                codename="review_sellerprofile",
            ),
            Permission.objects.get(
                content_type__app_label="accounts",
                codename="view_sellerprofile",
            ),
        )
        self.reviewer.refresh_from_db()

    def decision(self, decision, **kwargs):
        return review_seller(
            seller_id=self.seller.pk,
            reviewer=kwargs.pop("reviewer", self.reviewer),
            decision=decision,
            reason=kwargs.pop("reason", RATIONALE),
            evidence_case_reference=kwargs.pop("evidence_case_reference", CASE_REF),
            evidence_reviewed=kwargs.pop("evidence_reviewed", True),
            **kwargs,
        )

    def test_approval_requires_documented_case_and_records_actor(self):
        with self.assertRaises(ValidationError):
            self.decision("approve", evidence_case_reference="")
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.status, SellerProfile.Status.PENDING)
        self.assertEqual(SellerReviewEvent.objects.count(), 0)

        event = self.decision("approve")
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.status, SellerProfile.Status.APPROVED)
        self.assertEqual(event.reviewer, self.reviewer)
        self.assertEqual(event.previous_status, "pending")
        self.assertEqual(event.new_status, "approved")
        self.assertEqual(event.evidence_case_reference, CASE_REF)
        self.assertIsNotNone(self.seller.reviewed_at)

    def test_approval_fails_without_evidence_confirmation_even_for_authorized_staff(self):
        with self.assertRaises(ValidationError):
            self.decision("approve", evidence_reviewed=False)
        self.assertEqual(self.seller.status, "pending")
        self.assertEqual(SellerReviewEvent.objects.count(), 0)

    def test_unverified_underage_attestation_and_disabled_accounts_are_rejected(self):
        self.applicant.email_verified_at = None
        self.applicant.save(update_fields=["email_verified_at"])
        with self.assertRaises(ValidationError):
            self.decision("approve")
        self.applicant.email_verified_at = timezone.now()
        self.applicant.is_active = False
        self.applicant.save(update_fields=["email_verified_at", "is_active"])
        with self.assertRaises(ValidationError):
            self.decision("approve")
        self.applicant.is_active = True
        self.applicant.save(update_fields=["is_active"])
        self.seller.adult_attested = False
        self.seller.save(update_fields=["adult_attested"])
        with self.assertRaises(ValidationError):
            self.decision("approve")
        self.assertFalse(SellerReviewEvent.objects.exists())

    def test_reviewer_permission_and_self_review_are_enforced(self):
        outsider = User.objects.create_user(
            email="outsider@example.com",
            password="AnotherPass!2026",
            display_name="Outsider",
        )
        with self.assertRaises(PermissionDenied):
            self.decision("approve", reviewer=outsider)
        unprivileged_staff = User.objects.create_user(
            email="staff@example.com",
            password="StaffPass!2026",
            display_name="Staff",
            is_staff=True,
        )
        with self.assertRaises(PermissionDenied):
            self.decision("approve", reviewer=unprivileged_staff)

        self.applicant.is_staff = True
        self.applicant.is_superuser = True
        self.applicant.save(update_fields=["is_staff", "is_superuser"])
        with self.assertRaises(PermissionDenied):
            self.decision("approve", reviewer=self.applicant)

        self.assertEqual(self.seller.status, "pending")
        self.assertEqual(SellerReviewEvent.objects.count(), 0)

    def test_invalid_and_repeated_transitions_do_not_create_extra_events(self):
        with self.assertRaises(ValidationError):
            self.decision("suspend")
        self.decision("approve")
        with self.assertRaises(ValidationError):
            self.decision("approve")
        with self.assertRaises(ValidationError):
            self.decision("reject")
        self.assertEqual(SellerReviewEvent.objects.count(), 1)

    def test_rejected_seller_must_be_reopened_before_reapproval(self):
        rejected = self.decision("reject", evidence_case_reference="")
        self.assertEqual(rejected.new_status, "rejected")
        with self.assertRaises(ValidationError):
            self.decision("approve")
        reopened = self.decision("reopen", evidence_case_reference="")
        self.assertEqual(reopened.new_status, "pending")
        self.decision("approve")
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.status, "approved")
        self.assertEqual(SellerReviewEvent.objects.count(), 3)

    def test_case_reference_must_not_contain_sensitive_freeform_text(self):
        for value in ("x", "NIN: 012345", "https://example.com/secret.pdf", "\nOFFLINE-CASE"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.decision("approve", evidence_case_reference=value)
        with self.assertRaises(ValidationError):
            self.decision("approve", reason="Approved")
        self.assertFalse(SellerReviewEvent.objects.exists())

    def test_suspension_unpublishes_existing_listings_without_resurrection(self):
        species = Species.objects.create(
            slug="dogs", name="Dogs", category=Species.Category.COMPANION,
            trade_enabled=True,
        )
        animal = Animal.objects.create(
            owner=self.applicant, species=species, name="Example animal",
        )
        listing = Listing.objects.create(
            animal=animal, seller=self.applicant, title="Sample animal for sale",
            description="Test listing only; not a production animal.",
            price_minor=25000000, currency="NGN", region="Lagos", status=Listing.Status.ACTIVE,
        )
        self.decision("approve")
        self.assertEqual(self.client.get("/api/v1/listings/").data["count"], 1)

        suspended = self.decision("suspend", evidence_case_reference="")
        self.assertEqual(suspended.new_status, "suspended")
        listing.refresh_from_db()
        self.assertEqual(listing.status, Listing.Status.REMOVED)
        self.assertEqual(self.client.get("/api/v1/listings/").data["count"], 0)
        event = ListingEvent.objects.get(listing=listing)
        self.assertEqual((event.from_status, event.to_status), ("active", "removed"))

        self.decision("reopen", evidence_case_reference="")
        self.decision("approve")
        self.assertEqual(self.client.get("/api/v1/listings/").data["count"], 0)
        listing.refresh_from_db()
        self.assertEqual(listing.status, "removed")

    def test_public_listings_filtered_for_inactive_seller_and_trade_policy(self):
        species = Species.objects.create(
            slug="cats", name="Cats", category=Species.Category.COMPANION,
            trade_enabled=True,
        )
        animal = Animal.objects.create(owner=self.applicant, species=species, name="Kitten")
        Listing.objects.create(
            animal=animal, seller=self.applicant,
            title="Example cat listing", description="Only for regression testing.",
            price_minor=10000000, currency="NGN", region="Abuja", status="active",
        )
        self.decision("approve")
        self.assertEqual(self.client.get("/api/v1/listings/").data["count"], 1)
        self.applicant.is_active = False
        self.applicant.save(update_fields=["is_active"])
        self.assertEqual(self.client.get("/api/v1/listings/").data["count"], 0)
        self.applicant.is_active = True
        self.applicant.save(update_fields=["is_active"])
        species.trade_enabled = False
        species.save(update_fields=["trade_enabled"])
        self.assertEqual(self.client.get("/api/v1/listings/").data["count"], 0)

    def test_form_confirmation_and_case_reference(self):
        data = {
            "decision": "approve",
            "reason": RATIONALE,
            "evidence_case_reference": CASE_REF,
        }
        self.assertFalse(SellerReviewForm(data).is_valid())  # Unticked confirmation.
        form = SellerReviewForm({**data, "confirm_manual_evidence_review": True})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(SellerReviewForm({
            "decision": "reject",
            "reason": RATIONALE,
            "evidence_case_reference": "",
        }).is_valid())

    def test_admin_route_is_permissioned_and_records_review(self):
        url = reverse("admin:accounts_sellerprofile_review", args=[self.seller.pk])
        anon = self.client.get(url)
        self.assertEqual(anon.status_code, 302)
        unauthorized_staff = User.objects.create_user(
            email="read-only@example.com", password="ReadOnly!2026",
            display_name="Read Only", is_staff=True,
        )
        self.client.force_login(unauthorized_staff)
        self.assertEqual(self.client.get(url).status_code, 403)

        self.client.force_login(self.reviewer)
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Review seller application")
        completed = self.client.post(url, {
            "decision": "approve",
            "reason": RATIONALE,
            "evidence_case_reference": CASE_REF,
            "confirm_manual_evidence_review": "on",
        })
        self.assertEqual(completed.status_code, 302)
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.status, "approved")
        self.assertEqual(self.seller.review_events.count(), 1)

    def test_direct_admin_status_edit_is_not_available(self):
        from .admin import SellerProfileAdmin
        from django.contrib.admin import site
        model_admin = SellerProfileAdmin(SellerProfile, site)
        self.client.force_login(self.reviewer)
        request = self.client.get("/admin/accounts/sellerprofile/").wsgi_request
        request.user = self.reviewer
        self.assertFalse(model_admin.has_change_permission(request, self.seller))
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request, self.seller))
