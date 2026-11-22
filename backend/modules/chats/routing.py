from django.urls import path

from .consumers import ConversationUpdateConsumer

websocket_urlpatterns = [
    path(
        "ws/v1/chats/conversations/<uuid:conversation_id>/",
        ConversationUpdateConsumer.as_asgi(),
    ),
]
