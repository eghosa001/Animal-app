"""Conversation and message isolation, idempotency and listing safety gates."""
import uuid

from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APITestCase

from modules.accounts.models import SellerProfile, User
from modules.catalog.models import Species
from modules.listings.models import Animal, Listing

from .models import ChatMessage, Conversation


class ListingChatApiTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.buyer = User.objects.create_user(
            email="chat-buyer@example.com", display_name="Buyer",
            password="BuyerPassword!2026", email_verified_at=timezone.now(),
        )
        self.other = User.objects.create_user(
            email="chat-stranger@example.com", display_name="Stranger",
            password="OtherPassword!2026", email_verified_at=timezone.now(),
        )
        self.seller = User.objects.create_user(
            email="chat-seller@example.com", display_name="Animal Seller",
            password="SellerPassword!2026", email_verified_at=timezone.now(),
        )
        self.profile = SellerProfile.objects.create(
            user=self.seller, business_name="Approved Animal Care",
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
            seller=self.seller, animal=self.animal,
            title="Approved animal listing",
            description="Properly reviewed animal in safe and good condition.",
            price_minor=2500000, currency="NGN", region="Lagos",
            status=Listing.Status.ACTIVE,
        )
        self.start_path = "/api/v1/chats/conversations/"

    def start(self):
        return self.client.post(self.start_path, {
            "listing_id": str(self.listing.id),
        }, format="json")

    def chat_path(self, conversation):
        return f"/api/v1/chats/conversations/{conversation.id}/messages/"

    def open_thread(self):
        self.client.force_authenticate(self.buyer)
        result = self.start()
        self.assertEqual(result.status_code, 201, result.data)
        return Conversation.objects.get(pk=result.data["id"])

    def test_guest_may_not_list_or_contact_seller(self):
        self.assertEqual(self.client.get(self.start_path).status_code, 401)
        self.assertEqual(self.start().status_code, 401)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_only_verified_user_can_start_conversation(self):
        self.buyer.email_verified_at = None
        self.buyer.save(update_fields=("email_verified_at",))
        self.client.force_authenticate(self.buyer)
        response = self.start()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_one_conversation_per_buyer_and_listing(self):
        self.client.force_authenticate(self.buyer)
        created = self.start()
        repeated = self.start()
        self.assertEqual(created.status_code, 201)
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(created.data["id"], repeated.data["id"])
        self.assertEqual(created.data["counterparty_name"], "Animal Seller")
        self.assertTrue(created.data["can_send"])
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertNotIn("email", str(created.data))

    def test_owner_cannot_contact_self_and_disallowed_listing_is_not_visible(self):
        self.client.force_authenticate(self.seller)
        self.assertEqual(self.start().status_code, 400)
        self.client.force_authenticate(self.buyer)
        self.species.trade_enabled = False
        self.species.save(update_fields=("trade_enabled",))
        self.assertEqual(self.start().status_code, 404)
        self.assertFalse(Conversation.objects.exists())

    def test_suspended_seller_cannot_receive_new_inquiries(self):
        self.profile.status = SellerProfile.Status.SUSPENDED
        self.profile.save(update_fields=("status",))
        self.client.force_authenticate(self.buyer)
        self.assertEqual(self.start().status_code, 404)
        self.assertFalse(Conversation.objects.exists())

    def test_only_participants_can_read_or_send_messages(self):
        conversation = self.open_thread()
        path = self.chat_path(conversation)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.start_path).data["count"], 0)
        self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.post(path, {
            "body": "I should not have access",
            "client_nonce": str(uuid.uuid4()),
        }, format="json").status_code, 404)
        self.assertFalse(ChatMessage.objects.exists())

    def test_two_way_chat_and_retry_idempotency(self):
        conversation = self.open_thread()
        path = self.chat_path(conversation)
        nonce = str(uuid.uuid4())
        first = self.client.post(path, {
            "body": "Is this animal available for a safe visit?",
            "client_nonce": nonce,
        }, format="json")
        self.assertEqual(first.status_code, 201, first.data)
        repeated = self.client.post(path, {
            "body": "Is this animal available for a safe visit?",
            "client_nonce": nonce,
        }, format="json")
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(first.data["id"], repeated.data["id"])
        conflict = self.client.post(path, {
            "body": "Different text with the same idempotency key",
            "client_nonce": nonce,
        }, format="json")
        self.assertEqual(conflict.status_code, 400)
        self.client.force_authenticate(self.seller)
        second = self.client.post(path, {
            "body": "Yes, we can arrange a visit here in Lagos.",
            "client_nonce": str(uuid.uuid4()),
        }, format="json")
        self.assertEqual(second.status_code, 201)
        inbox = self.client.get(self.start_path)
        self.assertEqual(inbox.status_code, 200)
        self.assertEqual(inbox.data["count"], 1)
        self.assertEqual(inbox.data["results"][0]["counterparty_name"], "Buyer")
        messages = self.client.get(path)
        self.assertEqual(messages.status_code, 200)
        self.assertEqual(messages.data["count"], 2)
        self.assertEqual(messages.data["results"][0]["sender"], str(self.seller.pk))
        self.assertNotIn("chat-buyer@example.com", str(messages.data))
        self.assertEqual(ChatMessage.objects.count(), 2)

    def test_chat_history_remains_private_after_listing_is_sold(self):
        conversation = self.open_thread()
        path = self.chat_path(conversation)
        self.assertEqual(self.client.post(path, {
            "body": "Hello, I would like to meet the animal.",
            "client_nonce": str(uuid.uuid4()),
        }, format="json").status_code, 201)
        self.listing.status = Listing.Status.SOLD
        self.listing.save(update_fields=("status",))
        inbox = self.client.get(self.start_path)
        self.assertEqual(inbox.data["count"], 1)
        self.assertFalse(inbox.data["results"][0]["can_send"])
        self.assertEqual(self.client.get(path).data["count"], 1)
        denied = self.client.post(path, {
            "body": "Cannot continue selling a sold animal.",
            "client_nonce": str(uuid.uuid4()),
        }, format="json")
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(ChatMessage.objects.count(), 1)

    def test_message_requires_text_and_idempotency_id(self):
        conversation = self.open_thread()
        path = self.chat_path(conversation)
        for payload in (
            {"body": "  ", "client_nonce": str(uuid.uuid4())},
            {"body": "This is not an idempotent message"},
            {"body": "A" * 2001, "client_nonce": str(uuid.uuid4())},
        ):
            self.assertEqual(self.client.post(path, payload, format="json").status_code, 400)
        self.assertFalse(ChatMessage.objects.exists())

    def test_database_rejects_same_person_as_buyer_and_seller(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Conversation.objects.create(
                    listing=self.listing, buyer=self.seller, seller=self.seller,
                )
