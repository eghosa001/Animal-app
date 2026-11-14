"""Price quote privacy, idempotency, counteroffers, expiry and no-payment safety."""
import uuid
from datetime import timedelta

from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from modules.accounts.models import SellerProfile, User
from modules.catalog.models import Species
from modules.chats.models import Conversation
from modules.listings.models import Animal, Listing
from modules.safety.models import UserBlock

from .models import AnimalOffer, AnimalOfferEvent


@override_settings(PAYMENTS_ENABLED=False)
class NegotiationApiTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.buyer = User.objects.create_user(
            email="offer-buyer@example.com", display_name="Buyer",
            password="StrongPassword!1234", email_verified_at=timezone.now(),
        )
        self.second_buyer = User.objects.create_user(
            email="offer-second-buyer@example.com", display_name="Other buyer",
            password="StrongPassword!1234", email_verified_at=timezone.now(),
        )
        self.seller = User.objects.create_user(
            email="offer-seller@example.com", display_name="Seller",
            password="StrongPassword!1234", email_verified_at=timezone.now(),
        )
        self.stranger = User.objects.create_user(
            email="offer-stranger@example.com", display_name="Stranger",
            password="StrongPassword!1234", email_verified_at=timezone.now(),
        )
        SellerProfile.objects.create(
            user=self.seller, business_name="Approved",
            adult_attested=True, status=SellerProfile.Status.APPROVED,
        )
        self.species = Species.objects.create(
            name="Dogs", slug="dogs", category=Species.Category.COMPANION,
            trade_enabled=True,
        )
        animal = Animal.objects.create(
            owner=self.seller, species=self.species, name="Milo",
        )
        self.listing = Listing.objects.create(
            seller=self.seller, animal=animal,
            title="Individual companion animal",
            description="Test listing without any payment custody guarantee.",
            region="Abuja", currency="NGN", price_minor=45005000,
            status=Listing.Status.ACTIVE,
        )
        self.thread = Conversation.objects.create(
            listing=self.listing, buyer=self.buyer, seller=self.seller,
        )
        self.endpoint = f"/api/v1/offers/conversations/{self.thread.pk}/"
        self.client.force_authenticate(self.buyer)

    def propose(self, amount=40000000, nonce=None, url=None):
        return self.client.post(url or self.endpoint, {
            "amount_minor": amount,
            "client_nonce": nonce or str(uuid.uuid4()),
        }, format="json")

    def decide(self, offer_id, action):
        return self.client.post(
            f"/api/v1/offers/{offer_id}/decision/",
            {"decision": action}, format="json",
        )

    def test_guest_and_stranger_cannot_read_or_write_offers(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.endpoint).status_code, 401)
        self.assertEqual(self.propose().status_code, 401)
        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.client.get(self.endpoint).status_code, 404)
        self.assertEqual(self.propose().status_code, 404)
        self.assertFalse(AnimalOffer.objects.exists())

    def test_quote_is_integer_minor_units_and_never_creates_payment(self):
        result = self.propose(amount=37500050)
        self.assertEqual(result.status_code, 201, result.data)
        self.assertEqual(result.data["amount_minor"], 37500050)
        self.assertEqual(result.data["currency"], "NGN")
        self.assertEqual(result.data["list_price_minor_at_creation"], 45005000)
        self.assertEqual(result.data["status"], "pending")
        self.assertEqual(AnimalOfferEvent.objects.count(), 1)
        self.assertNotIn("payment_url", result.data)
        self.assertNotIn("escrow", str(result.data))
        self.assertEqual(self.listing.status, Listing.Status.ACTIVE)
        self.assertEqual(self.client.get(self.endpoint).data["count"], 1)

    def test_duplicate_client_nonce_returns_same_quote_but_conflicting_amount_fails(self):
        nonce = str(uuid.uuid4())
        first = self.propose(amount=25005000, nonce=nonce)
        again = self.propose(amount=25005000, nonce=nonce)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(again.status_code, 200)
        self.assertEqual(first.data["id"], again.data["id"])
        self.assertEqual(self.propose(amount=24000000, nonce=nonce).status_code, 400)
        self.assertEqual(AnimalOffer.objects.count(), 1)
        self.assertEqual(AnimalOfferEvent.objects.count(), 1)

    def test_counterparty_counter_replaces_pending_offer_and_audits_both(self):
        buyer_offer = self.propose()
        self.assertEqual(buyer_offer.status_code, 201)
        self.assertEqual(self.propose(amount=39000000).status_code, 400)
        self.client.force_authenticate(self.seller)
        counter = self.propose(amount=42000000)
        self.assertEqual(counter.status_code, 201, counter.data)
        self.assertEqual(str(counter.data["replaces"]), str(buyer_offer.data["id"]))
        old = AnimalOffer.objects.get(pk=buyer_offer.data["id"])
        self.assertEqual(old.status, AnimalOffer.Status.SUPERSEDED)
        self.assertEqual(AnimalOfferEvent.objects.count(), 3)
        self.assertEqual(self.decide(buyer_offer.data["id"], "accept").status_code, 400)

    def test_recipient_acceptance_is_recorded_without_transaction(self):
        created = self.propose()
        self.assertEqual(self.decide(created.data["id"], "accept").status_code, 403)
        self.client.force_authenticate(self.seller)
        accepted = self.decide(created.data["id"], "accept")
        self.assertEqual(accepted.status_code, 200, accepted.data)
        self.assertEqual(accepted.data["status"], "accepted")
        repeated = self.decide(created.data["id"], "accept")
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(AnimalOfferEvent.objects.count(), 2)
        self.assertEqual(self.propose(amount=35000000).status_code, 400)
        self.assertEqual(Listing.objects.get(pk=self.listing.pk).status, Listing.Status.ACTIVE)

    def test_seller_quote_can_be_accepted_by_buyer(self):
        self.client.force_authenticate(self.seller)
        created = self.propose(amount=44500000)
        self.assertEqual(created.status_code, 201)
        self.client.force_authenticate(self.buyer)
        response = self.decide(created.data["id"], "accept")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "accepted")

    def test_recipient_can_decline_and_then_propose_new_price(self):
        first = self.propose()
        self.client.force_authenticate(self.seller)
        declined = self.decide(first.data["id"], "decline")
        self.assertEqual(declined.status_code, 200)
        self.assertEqual(declined.data["status"], "declined")
        second = self.propose(amount=38000000)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(AnimalOffer.objects.count(), 2)

    def test_price_above_listing_and_sold_animal_rejected(self):
        self.assertEqual(self.propose(amount=45005001).status_code, 400)
        self.assertEqual(self.propose(amount=0).status_code, 400)
        self.listing.status = Listing.Status.SOLD
        self.listing.save(update_fields=("status",))
        self.assertEqual(self.propose().status_code, 403)
        self.assertEqual(self.client.get(self.endpoint).status_code, 200)

    def test_blocks_prevent_price_proposal_and_acceptance(self):
        created = self.propose()
        UserBlock.objects.create(blocker=self.seller, blocked=self.buyer)
        self.client.force_authenticate(self.seller)
        self.assertEqual(self.decide(created.data["id"], "accept").status_code, 403)
        self.assertEqual(self.propose(amount=40000000).status_code, 403)
        self.client.force_authenticate(self.buyer)
        self.assertEqual(self.propose(amount=33000000).status_code, 403)

    def test_expired_offer_cannot_be_accepted_and_new_quote_starts(self):
        created = self.propose()
        offer = AnimalOffer.objects.get(pk=created.data["id"])
        offer.expires_at = timezone.now() - timedelta(seconds=2)
        offer.save(update_fields=("expires_at",))
        self.assertEqual(self.client.get(self.endpoint).data["results"][0]["status"], "expired")
        self.client.force_authenticate(self.seller)
        self.assertEqual(self.decide(offer.pk, "accept").status_code, 400)
        next_offer = self.propose(amount=35000000)
        self.assertEqual(next_offer.status_code, 201)
        offer.refresh_from_db()
        self.assertEqual(offer.status, AnimalOffer.Status.EXPIRED)

    def test_price_drop_requires_renegotiation_before_acceptance(self):
        created = self.propose(amount=43000000)
        self.listing.price_minor = 42000000
        self.listing.save(update_fields=("price_minor",))
        self.client.force_authenticate(self.seller)
        self.assertEqual(self.decide(created.data["id"], "accept").status_code, 400)
        self.assertEqual(AnimalOffer.objects.get(pk=created.data["id"]).status,
                         AnimalOffer.Status.PENDING)

    def test_another_buyer_cannot_reach_two_agreements_on_one_listing(self):
        self.client.force_authenticate(self.buyer)
        first = self.propose()
        self.client.force_authenticate(self.seller)
        self.assertEqual(self.decide(first.data["id"], "accept").status_code, 200)
        second_thread = Conversation.objects.create(
            listing=self.listing, buyer=self.second_buyer, seller=self.seller,
        )
        self.client.force_authenticate(self.second_buyer)
        second_url = f"/api/v1/offers/conversations/{second_thread.pk}/"
        self.assertEqual(self.propose(url=second_url).status_code, 400)

    def test_unverified_user_cannot_offer(self):
        self.buyer.email_verified_at = None
        self.buyer.save(update_fields=("email_verified_at",))
        self.assertEqual(self.propose().status_code, 403)
