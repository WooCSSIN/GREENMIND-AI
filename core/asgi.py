"""
ASGI config for GreenMind WMS project.
Version: 3.0 - Real-Time with Django Channels + WebSocket
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

# Import consumers after django.setup()
from apps.dashboard.consumers import DashboardConsumer

# WebSocket URL patterns
websocket_urlpatterns = [
    path("ws/dashboard/<int:user_id>/", DashboardConsumer.as_asgi()),
]

# ASGI application with Protocol routing
application = ProtocolTypeRouter({
    # HTTP → Django views
    "http": get_asgi_application(),

    # WebSocket → Django Channels (with auth + host validation)
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
