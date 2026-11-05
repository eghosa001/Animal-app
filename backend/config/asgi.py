"""ASGI entry point. WebSocket routing is added with messaging milestone M2."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application

application = ProtocolTypeRouter({"http": get_asgi_application()})
