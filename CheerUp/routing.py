from channels.routing import ProtocolTypeRouter, URLRouter
from chat import routing as core_routing

application = ProtocolTypeRouter(
    {"websocket": URLRouter(core_routing.websocket_urlpatterns)}
)
