"""Short-lived ticket authentication, isolated websocket notices, durable REST send."""
import uuid
from unittest.mock import patch

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.core import signing
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase

from config.asgi import application
from modules.accounts.models import SellerProfile, User
from modules.catalog.models import Species
from modules.listings.models import Animal, Listing

from .models import ChatMessage, Conversation
from .realtime import chat_group_name, create_socket_ticket, validate_socket_ticket


class ConversationRealtimeTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.buyer = User.objects.create_user(
            email="socket-buyer@example.com", display_name="Buyer",
            password="SocketBuyerPassword!2026", email_verified_at=timezone.now(),
        )
        self.seller = User.objects.create_user(
            email="socket-seller@example.com", display_name="Seller",
            password="SocketSellerPassword!2026", email_verified_at=timezone.now(),
        )
        self.other = User.objects.create_user(
            email="socket-unrelated@example.com", display_name="Other",
            password="SocketOtherPassword!2026", email_verified_at=timezone.now(),
        )
        SellerProfile.objects.create(
            user=self.seller, business_name="Registered animal seller",
            adult_attested=True, status=SellerProfile.Status.APPROVED,
        )
        species = Species.objects.create(
            name="Dogs", slug="dogs", category=Species.Category.COMPANION,
            trade_enabled=True,
        )
        animal = Animal.objects.create(
            owner=self.seller, species=species, name="Milo",
        )
        listing = Listing.objects.create(
            animal=animal, seller=self.seller, title="Verified animal posting",
            description="Approved individual animal with eligible seller.",
            price_minor=7500000, currency="NGN", region="Abuja",
            status=Listing.Status.ACTIVE,
        )
        self.conversation = Conversation.objects.create(
            listing=listing, buyer=self.buyer, seller=self.seller,
        )
        self.path = f"/ws/v1/chats/conversations/{self.conversation.pk}/"
        self.ticket_path = (
            f"/api/v1/chats/conversations/{self.conversation.pk}/socket-ticket/"
        )
        self.client.force_authenticate(self.buyer)

    def ticket(self):
        response = self.client.post(self.ticket_path, {}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["expires_in_seconds"], 45)
        return response.data["ticket"]

    def test_ticket_is_private_scoped_and_does_not_contain_jwt(self):
        ticket = self.ticket()
        self.assertNotIn("Bearer", ticket)
        self.assertNotIn(":", ticket)
        self.assertEqual(
            validate_socket_ticket(ticket, self.conversation.pk), self.buyer.pk,
        )
        self.assertIsNone(validate_socket_ticket(ticket, uuid.uuid4()))
        self.assertIsNone(validate_socket_ticket("invalid-ticket", self.conversation.pk))
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(
            self.ticket_path, {}, format="json",
        ).status_code, 404)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post(
            self.ticket_path, {}, format="json",
        ).status_code, 401)

    def test_ticket_refuses_older_signature_and_revoked_account(self):
        ticket = self.ticket()
        with patch(
            "modules.chats.realtime.signing.loads",
            side_effect=signing.SignatureExpired("old"),
        ):
            self.assertIsNone(validate_socket_ticket(ticket, self.conversation.pk))
        self.buyer.set_password("ChangedToRevokeSocket!2026")
        self.buyer.save(update_fields=("password",))
        self.assertIsNone(validate_socket_ticket(ticket, self.conversation.pk))

    def test_staff_or_unverified_cannot_get_socket_ticket(self):
        self.buyer.email_verified_at = None
        self.buyer.save(update_fields=("email_verified_at",))
        self.assertEqual(self.client.post(
            self.ticket_path, {}, format="json",
        ).status_code, 403)
        self.buyer.email_verified_at = timezone.now()
        self.buyer.is_staff = True
        self.buyer.save(update_fields=("email_verified_at", "is_staff"))
        with self.assertRaises(ValueError):
            create_socket_ticket(user=self.buyer, conversation=self.conversation)

    def test_socket_only_delivers_scoped_message_ids(self):
        ticket = self.ticket()
        conv_id = self.conversation.pk
        message_id = uuid.uuid4()

        async def exercise():
            socket = WebsocketCommunicator(
                application, self.path,
                subprotocols=["anima.chat.v1", "anima.ticket." + ticket],
            )
            connected, protocol = await socket.connect()
            self.assertTrue(connected)
            self.assertEqual(protocol, "anima.chat.v1")
            await get_channel_layer().group_send(
                chat_group_name(conv_id),
                {
                    "type": "chat.update",
                    "kind": "message.created",
                    "conversation_id": str(conv_id),
                    "message_id": str(message_id),
                    "server_timestamp": timezone.now().isoformat(),
                },
            )
            event = await socket.receive_json_from(timeout=3)
            self.assertEqual(event["type"], "message.created")
            self.assertEqual(event["message_id"], str(message_id))
            self.assertNotIn("body", event)
            await socket.send_json_to({"type": "ping"})
            self.assertEqual(
                (await socket.receive_json_from(timeout=3))["type"], "pong",
            )
            await socket.disconnect()

        async_to_sync(exercise)()

    def test_invalid_or_missing_protocol_cannot_connect(self):
        async def exercise():
            socket = WebsocketCommunicator(
                application, self.path, subprotocols=["anima.chat.v1"],
            )
            connected, _ = await socket.connect()
            self.assertFalse(connected)
            await socket.disconnect()

        async_to_sync(exercise)()

    def test_rest_sends_notification_only_for_new_committed_message(self):
        endpoint = (
            f"/api/v1/chats/conversations/{self.conversation.pk}/messages/"
        )
        nonce = str(uuid.uuid4())
        with patch("modules.chats.views.send_message_notice") as publish:
            with self.captureOnCommitCallbacks(execute=True):
                first = self.client.post(endpoint, {
                    "body": "Is the animal ready for a safe visit?",
                    "client_nonce": nonce,
                }, format="json")
            self.assertEqual(first.status_code, 201)
            publish.assert_called_once()
            with self.captureOnCommitCallbacks(execute=True):
                repeat = self.client.post(endpoint, {
                    "body": "Is the animal ready for a safe visit?",
                    "client_nonce": nonce,
                }, format="json")
            self.assertEqual(repeat.status_code, 200)
            publish.assert_called_once()
        self.assertEqual(ChatMessage.objects.count(), 1)
