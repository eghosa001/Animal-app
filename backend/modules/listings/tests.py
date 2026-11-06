"""Public feed and listing publication remain guarded server-side."""
from django.utils import timezone
from rest_framework.test import APITestCase

from modules.accounts.models import SellerProfile, User
from modules.catalog.models import Species
from modules.media.models import MediaAsset
from modules.media.services import review_listing_photo

from .models import Animal, Listing, ListingEvent
from .services import approve_listing


class ListingApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="seller@example.com", display_name="Seller",
            password="StrongPass!90909", email_verified_at=timezone.now(),
        )
        self.species = Species.objects.create(
            name="Dogs", slug="dogs", category=Species.Category.COMPANION,
            trade_enabled=False,
        )
        self.seller = SellerProfile.objects.create(
            user=self.user, business_name="Sample Animals", adult_attested=True,
            status=SellerProfile.Status.PENDING,
        )
        login = self.client.post("/api/v1/auth/login", {
            "email": self.user.email, "password": "StrongPass!90909",
        }, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        self.payload = {
            "title": "Healthy animal listing",
            "description": "This is a sample listing used exclusively for backend testing.",
            "price_minor": 25000000,
            "currency": "NGN",
            "region": "Lagos",
            "species_id": self.species.pk,
            "animal_name": "Bella",
            "breed_label": "Mixed",
            "sex": "female",
            "estimated_age_months": 10,
        }

    def test_draft_private_until_approved(self):
        created = self.client.post("/api/v1/listings/", self.payload, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(Animal.objects.count(), 1)
        self.assertEqual(Listing.objects.count(), 1)
        self.assertEqual(self.client.get("/api/v1/listings/").data["count"], 0)
        mine = self.client.get("/api/v1/listings/mine/")
        self.assertEqual(mine.data["count"], 1)
        denied = self.client.post(f"/api/v1/listings/{created.data['id']}/submit/")
        self.assertEqual(denied.status_code, 400)
        self.seller.status = SellerProfile.Status.APPROVED
        self.seller.save(update_fields=["status"])
        still_denied = self.client.post(f"/api/v1/listings/{created.data['id']}/submit/")
        self.assertEqual(still_denied.status_code, 400)  # Species restriction.
        self.species.trade_enabled = True
        self.species.save(update_fields=["trade_enabled"])
        photo = MediaAsset.objects.create(
            owner=self.user, listing=Listing.objects.get(pk=created.data["id"]),
            kind=MediaAsset.Kind.LISTING_PHOTO,
            state=MediaAsset.State.PENDING, storage_key="listing-photos/test-listing.jpg",
            size_bytes=100, width=32, height=24, sha256="0" * 64,
        )
        submitted = self.client.post(f"/api/v1/listings/{created.data['id']}/submit/")
        self.assertEqual(submitted.status_code, 200)
        self.assertEqual(submitted.data["status"], "pending")
        self.assertEqual(self.client.get("/api/v1/listings/").data["count"], 0)
        reviewer = User.objects.create_superuser(
            email="admin@example.com", password="SuperStrong!90102", display_name="Moderator",
        )
        with self.assertRaisesMessage(Exception, "approved animal photograph"):
            approve_listing(created.data["id"], reviewer)
        review_listing_photo(
            asset_id=photo.pk, reviewer=reviewer, decision="approve",
            reason="Moderator visually inspected photo for matching animal and content.",
        )
        approve_listing(created.data["id"], reviewer)
        self.assertEqual(ListingEvent.objects.count(), 2)
        self.assertEqual(self.client.get("/api/v1/listings/").data["count"], 1)

    def test_unauthenticated_cannot_create_listing(self):
        self.client.credentials()
        response = self.client.post("/api/v1/listings/", self.payload, format="json")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(Listing.objects.exists())

    def test_listing_price_must_be_positive(self):
        response = self.client.post("/api/v1/listings/", {
            **self.payload, "price_minor": -1000,
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Animal.objects.exists())

    def test_draft_patch_updates_owner_and_animal_atomically(self):
        draft = self.client.post("/api/v1/listings/", self.payload, format="json")
        self.assertEqual(draft.status_code, 201)
        url = f"/api/v1/listings/{draft.data['id']}/"
        revised = self.client.patch(url, {
            "title": "Revised animal listing",
            "price_minor": 30005000,
            "breed_label": "Local mix",
            "sex": "male",
            "animal_name": "Chester",
            "estimated_age_months": 12,
            "status": "active",
            "seller": "someone-else",
        }, format="json")
        self.assertEqual(revised.status_code, 200, revised.data)
        self.assertEqual(revised.data["title"], "Revised animal listing")
        self.assertEqual(revised.data["animal_name"], "Chester")
        self.assertEqual(revised.data["price_minor"], 30005000)
        self.assertEqual(revised.data["sex"], "male")
        self.assertEqual(revised.data["status"], "draft")
        listing = Listing.objects.get(pk=draft.data["id"])
        self.assertEqual(listing.animal.name, "Chester")
        self.assertEqual(listing.animal.owner, self.user)
        self.assertEqual(listing.seller, self.user)
        self.assertEqual(self.client.get("/api/v1/listings/").data["count"], 0)
        self.assertEqual(self.client.get(url).status_code, 404)  # Not public.

    def test_age_estimate_can_be_cleared_on_draft_edit(self):
        draft = self.client.post("/api/v1/listings/", self.payload, format="json")
        url = f"/api/v1/listings/{draft.data['id']}/"
        updated = self.client.patch(
            url, {"estimated_age_months": None}, format="json"
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertIsNone(updated.data["estimated_age_months"])
        animal = Animal.objects.get(listing__pk=draft.data["id"])
        self.assertIsNone(animal.estimated_age_months)

    def test_invalid_partial_patch_rolls_back_entire_edit(self):
        draft = self.client.post("/api/v1/listings/", self.payload, format="json")
        url = f"/api/v1/listings/{draft.data['id']}/"
        response = self.client.patch(url, {
            "animal_name": "Changed",
            "price_minor": -4,
        }, format="json")
        self.assertEqual(response.status_code, 400)
        listing = Listing.objects.select_related("animal").get(pk=draft.data["id"])
        self.assertEqual(listing.animal.name, "Bella")
        self.assertEqual(listing.price_minor, self.payload["price_minor"])

    def test_other_seller_cannot_read_or_edit_draft(self):
        draft = self.client.post("/api/v1/listings/", self.payload, format="json")
        other = User.objects.create_user(
            email="other-seller@example.com", display_name="Other",
            password="AnotherPass!0929", email_verified_at=timezone.now(),
        )
        SellerProfile.objects.create(
            user=other, business_name="Other Seller",
            adult_attested=True, status=SellerProfile.Status.APPROVED,
        )
        self.client.force_authenticate(user=other)
        url = f"/api/v1/listings/{draft.data['id']}/"
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.patch(url, {"title": "Stolen listing"}, format="json").status_code, 404)
        self.assertEqual(self.client.post(f"{url}submit/").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/listings/mine/").data["count"], 0)

    def test_draft_patch_blocked_after_submission_even_for_owner(self):
        created = self.client.post("/api/v1/listings/", self.payload, format="json")
        listing = Listing.objects.get(pk=created.data["id"])
        self.seller.status = SellerProfile.Status.APPROVED
        self.seller.save(update_fields=["status"])
        self.species.trade_enabled = True
        self.species.save(update_fields=["trade_enabled"])
        MediaAsset.objects.create(
            owner=self.user, listing=listing, kind=MediaAsset.Kind.LISTING_PHOTO,
            state=MediaAsset.State.PENDING, storage_key="listing-photos/pending.jpg",
            size_bytes=100, width=32, height=24, sha256="a" * 64,
        )
        submitted = self.client.post(f"/api/v1/listings/{listing.pk}/submit/")
        self.assertEqual(submitted.status_code, 200, submitted.data)
        self.assertEqual(self.client.patch(
            f"/api/v1/listings/{listing.pk}/", {"title": "Bypass moderation"}, format="json",
        ).status_code, 404)
        listing.refresh_from_db()
        self.assertEqual(listing.title, self.payload["title"])
        self.assertEqual(ListingEvent.objects.count(), 1)

    def test_submit_needs_photo_even_with_approved_seller_and_species(self):
        created = self.client.post("/api/v1/listings/", self.payload, format="json")
        self.seller.status = SellerProfile.Status.APPROVED
        self.seller.save(update_fields=["status"])
        self.species.trade_enabled = True
        self.species.save(update_fields=["trade_enabled"])
        response = self.client.post(f"/api/v1/listings/{created.data['id']}/submit/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("photos", response.data)
        self.assertEqual(ListingEvent.objects.count(), 0)

    def test_species_switch_not_allowed_after_images_attached(self):
        created = self.client.post("/api/v1/listings/", self.payload, format="json")
        animal = Animal.objects.get(listing__pk=created.data["id"])
        new_species = Species.objects.create(
            name="Cats", slug="cats-listing", category=Species.Category.COMPANION,
        )
        MediaAsset.objects.create(
            owner=self.user, listing=Listing.objects.get(pk=created.data["id"]),
            kind=MediaAsset.Kind.LISTING_PHOTO, state=MediaAsset.State.PENDING,
            storage_key="listing-photos/locked.jpg", size_bytes=100,
            width=32, height=24, sha256="b" * 64,
        )
        response = self.client.patch(f"/api/v1/listings/{created.data['id']}/", {
            "species_id": new_species.pk,
        }, format="json")
        self.assertEqual(response.status_code, 400)
        animal.refresh_from_db()
        self.assertEqual(animal.species_id, self.species.pk)

    def test_suspended_seller_cannot_edit_existing_draft(self):
        created = self.client.post("/api/v1/listings/", self.payload, format="json")
        self.seller.status = SellerProfile.Status.SUSPENDED
        self.seller.save(update_fields=["status"])
        response = self.client.patch(f"/api/v1/listings/{created.data['id']}/", {
            "title": "Suspended edit attempt",
        }, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Listing.objects.get(pk=created.data["id"]).title, self.payload["title"])

    def test_disabled_species_still_allows_drafts_but_not_submission(self):
        created = self.client.post("/api/v1/listings/", self.payload, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["species"]["trade_enabled"], False)
        self.assertEqual(self.client.post(f"/api/v1/listings/{created.data['id']}/submit/").status_code, 400)
