"""Public feed and listing publication remain guarded server-side."""
from django.utils import timezone
from rest_framework.test import APITestCase

from modules.accounts.models import SellerProfile, User
from modules.catalog.models import Species

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
        submitted = self.client.post(f"/api/v1/listings/{created.data['id']}/submit/")
        self.assertEqual(submitted.status_code, 200)
        self.assertEqual(submitted.data["status"], "pending")
        self.assertEqual(self.client.get("/api/v1/listings/").data["count"], 0)
        reviewer = User.objects.create_superuser(
            email="admin@example.com", password="SuperStrong!90102", display_name="Moderator",
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
