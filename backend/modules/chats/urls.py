from django.urls import path

from .views import ConversationMessagesView, ConversationsView

urlpatterns = [
    path("conversations/", ConversationsView.as_view(), name="chat-conversations"),
    path(
        "conversations/<uuid:conversation_id>/messages/",
        ConversationMessagesView.as_view(), name="chat-conversation-messages",
    ),
]
