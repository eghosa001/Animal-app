"""ASGI entry: HTTP APIs and authenticated read-only chat notifications."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from django.core.asgi import get_asgi_application  # noqa: E402

django_http_app = get_asgi_application()
from modules.chats.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_http_app,
    "websocket": URLRouter(websocket_urlpatterns),
})
