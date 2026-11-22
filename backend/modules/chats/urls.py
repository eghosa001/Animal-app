from django.urls import path

from .views import (
    ConversationMessagesView, ConversationReadAcknowledgeView, ConversationSocketTicketView, ConversationsView,
)

urlpatterns = [
    path("conversations/", ConversationsView.as_view(), name="chat-conversations"),
    path(
        "conversations/<uuid:conversation_id>/socket-ticket/",
        ConversationSocketTicketView.as_view(), name="chat-socket-ticket",
    ),
    path(
        "conversations/<uuid:conversation_id>/read/",
        ConversationReadAcknowledgeView.as_view(), name="chat-conversation-read",
    ),
    path(
        "conversations/<uuid:conversation_id>/messages/",
        ConversationMessagesView.as_view(), name="chat-conversation-messages",
    ),
]
