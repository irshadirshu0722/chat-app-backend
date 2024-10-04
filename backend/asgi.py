"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter,URLRouter
from user_chat.routes import websocket_urlpatterns
from .middleware import JWTWebsocketMiddleware
# import asyncio
# from .redis import get_redis_pool

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = ProtocolTypeRouter(
  {
    'http':get_asgi_application(),
    'websocket':JWTWebsocketMiddleware(
        URLRouter(
            websocket_urlpatterns
        )
    )
  }
)


# asyncio.get_event_loop().run_until_complete(get_redis_pool())