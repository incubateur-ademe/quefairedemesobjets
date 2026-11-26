from core.views import healthz, livez

PROBES = {"/healthz/": healthz, "/livez/": livez}


class HealthzMiddleware:
    """Answer the probes before any middleware validates the Host header.

    Container platforms probe with the container's internal IP as Host
    (Scaleway: 100.96.x.x:8000, changing per deployment), which no
    ALLOWED_HOSTS entry can list.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if probe := PROBES.get(request.path):
            return probe(request)
        return self.get_response(request)
