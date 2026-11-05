"""ASGI entry point. WebSocket routing is added with messaging milestone M2."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from channels.routing import ProtocolTypeRouter  # noqa: E402
from django.core.asgi import get_asgi_application  # noqa: E402

application = ProtocolTypeRouter({"http": get_asgi_application()})
