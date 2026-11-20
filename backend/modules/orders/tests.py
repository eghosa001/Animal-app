"""Unfunded order receipts, privacy, immutable price and no-double-request safeguards."""
import uuid
from datetime import timedelta

from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APITestCase

from modules.accounts.models import SellerProfile, User
from modules.catalog.models import Species
from modules.chats.models import Conversation
from modules.listings.models import Animal, Listing
from modules.offers.models import AnimalOffer
from modules.safety.models import UserBlock

from .models import OrderIntent, OrderIntentEvent


class UnfundedOrderIntentTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.buyer = User.objects.create_user(
            email="intent-buyer@example.com", display_name="Buyer",
            password="BuyerPassword!2026", email_verified_at=timezone.now(),
        )
        self.seller = User.objects.create_user(
            email="intent-seller@example.com", display_name="Approved Seller",
            password="SellerPassword!2026", email_verified_at=timezone.now(),
        )
        self.stranger = User.objects.create_user(
            email="intent-stranger@example.com", display_name="Stranger",
            password="StrangerPassword!2026", email_verified_at=timezone.now(),
        )
        SellerProfile.objects.create(
            user=self.seller, business_name="Responsible animal breeder",
            adult_attested=True, status=SellerProfile.Status.APPROVED,
        )
        self.species = Species.objects.create(
            name="Dogs", slug="dogs", category=Species.Category.COMPANION,
            trade_enabled=True,
        )
        self.animal = Animal.objects.create(
            owner=self.seller, species=self.species, name="Test Bella",
        )
        self.listing = Listing.objects.create(
            animal=self.animal, seller=self.seller,
            title="Approved animal without implied purchase protection",
            description="Single identified animal for safe contact and negotiation.",
            price_minor=85005000, currency="NGN", region="Benin City",
            status=Listing.Status.ACTIVE,
        )
        self.conversation = Conversation.objects.create(
            buyer=self.buyer, seller=self.seller, listing=self.listing,
        )
        self.offer = AnimalOffer.objects.create(
            conversation=self.conversation, proposer=self.buyer,
            amount_minor=80005000, currency="NGN",
            list_price_minor_at_creation=self.listing.price_minor,
            client_nonce=uuid.uuid4(), status=AnimalOffer.Status.ACCEPTED,
            expires_at=timezone.now() + timedelta(days=2),
            responded_at=timezone.now(),
        )
        self.endpoint = "/api/v1/orders/intents/"
        self.nonce = str(uuid.uuid4())
        self.client.force_authenticate(self.buyer)

    def start(self, nonce=None, ack=True, offer=None):
        return self.client.post(self.endpoint, {
            "accepted_offer_id": str(offer or self.offer.pk),
            "request_nonce": nonce or self.nonce,
            "no_payment_acknowledged": ack,
        }, format="json")

    def created(self):
        response = self.start()
        self.assertEqual(response.status_code, 201, response.data)
        return response

    def test_accepted_offer_creates_only_unfunded_receipt(self):
        result = self.created()
        self.assertEqual(result.data["status"], "awaiting_partner")
        self.assertEqual(result.data["price_minor"], 80005000)
        self.assertEqual(result.data["currency"], "NGN")
        self.assertEqual(result.data["fulfillment_mode"], "pickup_planned")
        self.assertEqual(result.data["animal_name_snapshot"], "Test Bella")
        self.assertEqual(result.data["listing_region_snapshot"], "Benin City")
        self.assertEqual(result.data["animal_id_snapshot"], self.animal.pk)
        self.assertIs(result.data["checkout_available"], False)
        self.assertIs(result.data["funds_secured"], False)
        self.assertIs(result.data["animal_reserved"], False)
        self.assertNotIn("checkout_url", result.data)
        self.assertNotIn("payment_reference", result.data)
        self.assertEqual(OrderIntent.objects.count(), 1)
        self.assertEqual(OrderIntentEvent.objects.count(), 1)
        self.assertEqual(Listing.objects.get(pk=self.listing.pk).status, "active")

    def test_user_must_explicitly_acknowledge_no_payment(self):
        self.assertEqual(self.start(ack=False).status_code, 400)
        result = self.client.post(self.endpoint, {
            "accepted_offer_id": str(self.offer.pk),
            "request_nonce": self.nonce,
        }, format="json")
        self.assertEqual(result.status_code, 400)
        self.assertFalse(OrderIntent.objects.exists())

    def test_repeat_same_nonce_idempotent_but_new_nonce_not_another_intent(self):
        first = self.created()
        repeated = self.start()
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(first.data["id"], repeated.data["id"])
        self.assertEqual(self.start(nonce=str(uuid.uuid4())).status_code, 400)
        self.assertEqual(OrderIntent.objects.count(), 1)
        self.assertEqual(OrderIntentEvent.objects.count(), 1)

    def test_guest_seller_stranger_cannot_create_buyer_checkout(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.start().status_code, 401)
        self.assertEqual(self.client.get(self.endpoint).status_code, 401)
        self.client.force_authenticate(self.seller)
        self.assertEqual(self.start().status_code, 400)
        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.start().status_code, 400)
        self.assertFalse(OrderIntent.objects.exists())

    def test_only_buyer_and_seller_can_read_an_unfunded_intent(self):
        response = self.created()
        target = f"{self.endpoint}{response.data['id']}/"
        self.assertEqual(self.client.get(self.endpoint).data["count"], 1)
        self.assertEqual(self.client.get(target).status_code, 200)
        self.client.force_authenticate(self.seller)
        self.assertEqual(self.client.get(self.endpoint).data["count"], 1)
        self.assertEqual(self.client.get(target).status_code, 200)
        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.client.get(self.endpoint).data["count"], 0)
        self.assertEqual(self.client.get(target).status_code, 404)
        self.assertEqual(self.client.post(
            target + "cancel/", {"reason": "Unauthorized cancellation attempt."},
            format="json",
        ).status_code, 404)

    def test_unverified_buyer_blocked_seller_and_species_policy_block_creation(self):
        self.buyer.email_verified_at = None
        self.buyer.save(update_fields=("email_verified_at",))
        self.assertEqual(self.start().status_code, 403)
        self.buyer.email_verified_at = timezone.now()
        self.buyer.save(update_fields=("email_verified_at",))
        UserBlock.objects.create(blocker=self.seller, blocked=self.buyer)
        self.assertEqual(self.start().status_code, 403)
        UserBlock.objects.all().delete()
        self.species.trade_enabled = False
        self.species.save(update_fields=("trade_enabled",))
        self.assertEqual(self.start().status_code, 403)
        self.assertFalse(OrderIntent.objects.exists())

    def test_unapproved_or_sold_or_unaccepted_offer_cannot_create(self):
        self.offer.status = AnimalOffer.Status.PENDING
        self.offer.save(update_fields=("status",))
        self.assertEqual(self.start().status_code, 400)
        self.offer.status = AnimalOffer.Status.ACCEPTED
        self.offer.save(update_fields=("status",))
        self.listing.status = Listing.Status.SOLD
        self.listing.save(update_fields=("status",))
        self.assertEqual(self.start().status_code, 403)
        self.assertFalse(OrderIntent.objects.exists())

    def test_price_change_or_animal_ownership_change_blocks_checkout(self):
        self.listing.price_minor = 70000000
        self.listing.save(update_fields=("price_minor",))
        self.assertEqual(self.start().status_code, 400)
        self.listing.price_minor = 85005000
        self.listing.save(update_fields=("price_minor",))
        self.animal.owner = self.stranger
        self.animal.save(update_fields=("owner",))
        self.assertEqual(self.start().status_code, 400)

    def test_snapshot_is_not_modified_by_later_public_listing_changes(self):
        receipt = self.created()
        self.listing.title = "New headline, not part of the agreed order"
        self.listing.region = "A different location"
        self.listing.price_minor = 84000000
        self.listing.save(update_fields=("title", "region", "price_minor"))
        self.animal.name = "Different public animal name"
        self.animal.save(update_fields=("name",))
        private = self.client.get(self.endpoint + receipt.data["id"] + "/")
        self.assertEqual(private.data["listing_title_snapshot"], receipt.data["listing_title_snapshot"])
        self.assertEqual(private.data["listing_region_snapshot"], "Benin City")
        self.assertEqual(private.data["animal_name_snapshot"], "Test Bella")
        self.assertEqual(private.data["price_minor"], 80005000)

    def test_buyer_cancels_without_changing_inventory_or_refunding(self):
        receipt = self.created()
        target = f"{self.endpoint}{receipt.data['id']}/cancel/"
        cancelled = self.client.post(target, {
            "reason": "I changed my mind before checkout was ever enabled.",
        }, format="json")
        self.assertEqual(cancelled.status_code, 200, cancelled.data)
        self.assertEqual(cancelled.data["status"], "cancelled")
        self.assertIsNotNone(cancelled.data["cancelled_at"])
        self.assertIs(cancelled.data["funds_secured"], False)
        self.assertIs(cancelled.data["animal_reserved"], False)
        repeated = self.client.post(target, {
            "reason": "I changed my mind before checkout was ever enabled.",
        }, format="json")
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(OrderIntentEvent.objects.count(), 2)
        self.assertEqual(Listing.objects.get(pk=self.listing.pk).status, "active")

    def test_seller_can_cancel_existing_intent_but_cannot_open_it(self):
        receipt = self.created()
        self.client.force_authenticate(self.seller)
        self.assertEqual(self.start(nonce=str(uuid.uuid4())).status_code, 400)
        target = self.endpoint + receipt.data["id"] + "/cancel/"
        result = self.client.post(target, {
            "reason": "The seller cannot proceed because the animal is not available.",
        }, format="json")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["status"], "cancelled")
        self.assertEqual(OrderIntentEvent.objects.count(), 2)

    def test_buyer_can_read_cancelled_intent_after_being_blocked(self):
        receipt = self.created()
        UserBlock.objects.create(blocker=self.seller, blocked=self.buyer)
        target = self.endpoint + receipt.data["id"] + "/cancel/"
        self.assertEqual(self.client.post(target, {
            "reason": "I want to cancel because I no longer trust this seller.",
        }, format="json").status_code, 200)
        self.assertEqual(self.client.get(self.endpoint).data["count"], 1)

    def test_database_enforces_exactly_one_intent_per_listing(self):
        self.created()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                item = OrderIntent.objects.get()
                item.pk = uuid.uuid4()
                item.request_nonce = uuid.uuid4()
                item.save(force_insert=True)
        self.assertEqual(OrderIntent.objects.count(), 1)

    def test_payment_and_delivery_endpoints_are_not_available(self):
        self.created()
        for path in (
            "/api/v1/orders/checkout/",
            "/api/v1/orders/confirm-payment/",
            "/api/v1/orders/delivered/",
        ):
            self.assertEqual(self.client.post(path, {}, format="json").status_code, 404)
