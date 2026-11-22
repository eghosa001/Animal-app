"""Short-lived, conversation-scoped tickets and best-effort realtime notices.

Socket delivery is only a hint. Durable messages live in the authenticated REST API.
"""
import base64
import binascii
import logging
import uuid

from asgiref.sync import async_to_sync
from django.core import signing
from django.utils.crypto import salted_hmac
from django.utils import timezone
from channels.layers import get_channel_layer

from .models import Conversation

logger = logging.getLogger(__name__)
_TICKET_SALT = "anima-ws-chat-ticket-v1"
_TICKET_MAX_AGE = 45


def _session_tag(user):
    # The token does not expose the password hash, session secret, or JWT.
    return salted_hmac("anima-ws-session-v1", user.password).hexdigest()


def create_socket_ticket(*, user, conversation):
    if user.pk not in (conversation.buyer_id, conversation.seller_id):
        raise ValueError("Conversation participant required")
    if not user.is_active or user.is_staff or not user.is_email_verified:
        raise ValueError("Active verified consumer account required")
    blob = signing.dumps({
        "u": str(user.pk),
        "c": str(conversation.pk),
        "s": _session_tag(user),
    }, salt=_TICKET_SALT)
    return base64.urlsafe_b64encode(blob.encode("ascii")).decode("ascii").rstrip("=")


def validate_socket_ticket(encoded, conversation_id):
    """Return UUID of authorized user, or None; never reveal ticket failure details."""
    try:
        if len(encoded) > 1024 or len(encoded) < 30 or not all(
            ch.isalnum() or ch in "-_" for ch in encoded
        ):
            return None
        padded = encoded + ("=" * (-len(encoded) % 4))
        decoded = base64.urlsafe_b64decode(padded).decode("ascii")
        data = signing.loads(decoded, salt=_TICKET_SALT, max_age=_TICKET_MAX_AGE)
        user_id = uuid.UUID(data["u"])
        scoped_id = uuid.UUID(data["c"])
        if scoped_id != uuid.UUID(str(conversation_id)):
            return None
        from modules.accounts.models import User
        user = User.objects.filter(pk=user_id, is_active=True, is_staff=False).first()
        if user is None or not user.is_email_verified:
            return None
        if data["s"] != _session_tag(user):
            return None
        if not Conversation.objects.filter(pk=scoped_id).filter(
            __import__("django").db.models.Q(buyer=user)
            | __import__("django").db.models.Q(seller=user)
        ).exists():
            return None
        return user_id
    except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError,
            KeyError, UnicodeError, binascii.Error, OverflowError):
        return None


def chat_group_name(conversation_id):
    return f"anima.chat.{uuid.UUID(str(conversation_id)).hex}"


def send_message_notice(*, conversation_id, message_id):
    """Called only after a successfully committed NEW message; no raw body in Redis."""
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        async_to_sync(layer.group_send)(chat_group_name(conversation_id), {
            "type": "chat.update",
            "kind": "message.created",
            "conversation_id": str(conversation_id),
            "message_id": str(message_id),
            "server_timestamp": timezone.now().isoformat(),
        })
    except Exception:
        # Durable message was already committed; mobile reconnect/REST still works.
        logger.exception("Chat websocket notification transport failed")
