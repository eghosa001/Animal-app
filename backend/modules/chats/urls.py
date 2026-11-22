from django.urls import path

from .views import (
    ConversationMessagesView, ConversationReadAcknowledgeView, ConversationsView,
)

urlpatterns = [
    path("conversations/", ConversationsView.as_view(), name="chat-conversations"),
    path(
        "conversations/<uuid:conversation_id>/read/",
        ConversationReadAcknowledgeView.as_view(), name="chat-conversation-read",
    ),
    path(
        "conversations/<uuid:conversation_id>/messages/",
        ConversationMessagesView.as_view(), name="chat-conversation-messages",
    ),
]
