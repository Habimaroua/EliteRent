import os
import socket
import consul
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "diagnostic.settings")

def register_with_consul():
    try:
        c = consul.Consul(host='service_registry', port=8500)
        service_id = f"web-platform-{socket.gethostname()}"
        c.agent.service.register(
            "web-platform",
            service_id=service_id,
            address="web_platform",
            port=8001,
            tags=[
                "traefik.enable=true",
                "traefik.http.routers.web.rule=PathPrefix(`/`)",
                "traefik.http.services.web.loadbalancer.server.port=8001"
            ]
        )
        print(f"Registered WEB service: {service_id}")
    except Exception as e:
        print(f"Consul registration failed (WEB): {e}")

register_with_consul()
application = get_wsgi_application()
