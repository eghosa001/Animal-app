"""Private unread counters and non-regressing read cursors for both parties."""
import uuid

from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase

from modules.accounts.models import SellerProfile, User
from modules.catalog.models import Species
from modules.listings.models import Animal, Listing

from .models import ChatMessage, Conversation


class ReadReceiptTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.buyer = User.objects.create_user(
            email="unread-buyer@example.com", display_name="Buyer",
            password="BuyerPassword!2026", email_verified_at=timezone.now(),
        )
        self.seller = User.objects.create_user(
            email="unread-seller@example.com", display_name="Seller",
            password="SellerPassword!2026", email_verified_at=timezone.now(),
        )
        self.stranger = User.objects.create_user(
            email="unread-stranger@example.com", display_name="Stranger",
            password="StrangerPassword!2026", email_verified_at=timezone.now(),
        )
        SellerProfile.objects.create(
            user=self.seller, business_name="Registered Breeder",
            adult_attested=True, status=SellerProfile.Status.APPROVED,
        )
        species = Species.objects.create(
            name="Dogs", slug="dogs", category=Species.Category.COMPANION,
            trade_enabled=True,
        )
        animal = Animal.objects.create(
            owner=self.seller, species=species, name="Bella",
        )
        self.listing = Listing.objects.create(
            seller=self.seller, animal=animal, title="Approved animal listing",
            description="The animal has been reviewed and may be discussed.",
            price_minor=45005000, currency="NGN", region="Abuja",
            status=Listing.Status.ACTIVE,
        )
        self.conversation = Conversation.objects.create(
            listing=self.listing, buyer=self.buyer, seller=self.seller,
        )
        self.read_path = f"/api/v1/chats/conversations/{self.conversation.pk}/read/"
        self.messages_path = f"/api/v1/chats/conversations/{self.conversation.pk}/messages/"
        self.client.force_authenticate(self.buyer)

    def send(self, sender, text):
        return ChatMessage.objects.create(
            conversation=self.conversation, sender=sender,
            body=text, client_nonce=uuid.uuid4(),
        )

    def unread(self):
        response = self.client.get("/api/v1/chats/conversations/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        return response.data["results"][0]["unread_count"]

    def ack(self, msg):
        return self.client.post(
            self.read_path, {"message_id": str(msg.pk)}, format="json",
        )

    def test_inbox_does_not_mark_messages_read_implicitly(self):
        self.send(self.seller, "New animal photos will be ready this week")
        self.send(self.seller, "Please review the animal listing before visiting")
        self.assertEqual(self.unread(), 2)
        self.assertEqual(self.unread(), 2)
        self.assertEqual(self.client.get(self.messages_path).data["count"], 2)
        self.assertEqual(self.unread(), 2)
        self.client.force_authenticate(self.seller)
        self.assertEqual(self.unread(), 0)

    def test_reading_latest_message_clears_unread_and_older_ack_cannot_regress(self):
        old = self.send(self.seller, "First message")
        latest = self.send(self.seller, "Second message")
        self.assertEqual(self.unread(), 2)
        first = self.ack(latest)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["last_read_message"], str(latest.pk))
        self.assertEqual(self.unread(), 0)
        repeated = self.ack(latest)
        self.assertEqual(repeated.status_code, 200)
        older = self.ack(old)
        self.assertEqual(older.status_code, 200)
        self.assertEqual(older.data["last_read_message"], str(latest.pk))
        self.assertEqual(self.unread(), 0)
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.buyer_last_read_message_id, latest.pk)
        self.assertIsNone(self.conversation.seller_last_read_message_id)
        self.send(self.seller, "Third message after you last read")
        self.assertEqual(self.unread(), 1)

    def test_buyer_sending_does_not_increase_their_own_unread_count(self):
        self.send(self.buyer, "Hello, is the animal available?")
        self.send(self.buyer, "I would like a safe viewing")
        self.assertEqual(self.unread(), 0)
        self.client.force_authenticate(self.seller)
        self.assertEqual(self.unread(), 2)
        last = ChatMessage.objects.order_by("-created_at", "-id").first()
        self.assertEqual(self.ack(last).status_code, 200)
        self.assertEqual(self.unread(), 0)
        self.client.force_authenticate(self.buyer)
        self.assertEqual(self.unread(), 0)

    def test_stranger_cannot_acknowledge_messages_or_read_cursors(self):
        msg = self.send(self.seller, "Private message")
        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.ack(msg).status_code, 404)
        self.assertEqual(self.client.get(self.messages_path).status_code, 404)
        self.assertEqual(self.client.get("/api/v1/chats/conversations/").data["count"], 0)
        self.conversation.refresh_from_db()
        self.assertIsNone(self.conversation.buyer_last_read_message_id)
        self.assertIsNone(self.conversation.seller_last_read_message_id)

    def test_guessing_message_uuid_or_invalid_input_does_not_advance_cursor(self):
        self.send(self.seller, "Genuine existing message")
        bad = self.client.post(
            self.read_path, {"message_id": str(uuid.uuid4())}, format="json",
        )
        self.assertEqual(bad.status_code, 404)
        self.assertEqual(
            self.client.post(
                self.read_path, {"message_id": "not-a-uuid"}, format="json",
            ).status_code, 400,
        )
        self.assertEqual(self.unread(), 1)

    def test_cannot_acknowledge_message_from_another_conversation(self):
        other_buyer = User.objects.create_user(
            email="unread-other@example.com", display_name="Other buyer",
            password="BuyerPassword!2026", email_verified_at=timezone.now(),
        )
        other_thread = Conversation.objects.create(
            listing=self.listing, buyer=other_buyer, seller=self.seller,
        )
        other_msg = ChatMessage.objects.create(
            conversation=other_thread, sender=self.seller,
            body="Unrelated buyer private message", client_nonce=uuid.uuid4(),
        )
        self.assertEqual(self.ack(other_msg).status_code, 404)
        self.conversation.refresh_from_db()
        self.assertIsNone(self.conversation.buyer_last_read_message_id)

    def test_read_old_messages_still_allowed_after_sold_or_blocked(self):
        msg = self.send(self.seller, "We spoke before this animal was sold.")
        self.listing.status = Listing.Status.SOLD
        self.listing.save(update_fields=("status",))
        self.assertEqual(self.ack(msg).status_code, 200)
        self.assertEqual(self.unread(), 0)

    def test_guest_cannot_write_read_receipts(self):
        msg = self.send(self.seller, "Private message")
        self.client.force_authenticate(user=None)
        self.assertEqual(self.ack(msg).status_code, 401)
