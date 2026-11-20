"""Read only up to a message the participant actually received and displayed."""
from django.db import transaction
from rest_framework.exceptions import PermissionDenied

from .models import ChatMessage, Conversation


@transaction.atomic
def acknowledge_read_message(*, conversation_id, actor, message_id):
    conversation = Conversation.objects.select_for_update(of=("self",)).get(
        pk=conversation_id,
    )
    if actor.pk == conversation.buyer_id:
        field = "buyer_last_read_message"
    elif actor.pk == conversation.seller_id:
        field = "seller_last_read_message"
    else:
        raise PermissionDenied("Only chat participants can acknowledge messages")

    # Caller-supplied IDs must refer to a REAL message from this conversation;
    # never allow reading ahead by client timestamp or an arbitrary future UUID.
    target = ChatMessage.objects.get(pk=message_id, conversation=conversation)
    current = getattr(conversation, field)
    if current is not None:
        current_position = (current.created_at, current.pk.hex)
        requested_position = (target.created_at, target.pk.hex)
        if requested_position <= current_position:
            return current

    setattr(conversation, field, target)
    conversation.save(update_fields=(field,))
    return target
