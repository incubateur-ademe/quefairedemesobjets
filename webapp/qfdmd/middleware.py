from django.conf import settings
from django.shortcuts import redirect
from django.urls import Resolver404, resolve
from django.utils.cache import add_never_cache_headers, patch_vary_headers
from wagtail.admin.viewsets.base import reverse

from core.utils import has_explicit_perm


class BetaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def _set_beta_mode_from(self, request):
        request.beta = False
        if request.user.is_authenticated:
            request.beta = has_explicit_perm(
                request.user, "wagtailadmin.can_see_beta_search"
            )

    def __call__(self, request):
        self._set_beta_mode_from(request)
        response = self.get_response(request)
        return response


class RequestEnhancementMiddleware:
    LOGGED_IN_COOKIE = "logged_in"
    CARTE_PARAM = "carte"
    IFRAME_PARAM = "iframe"
    FORMULAIRE_PARAM = "formulaire"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Prepare request
        self._prepare_request_if_iframe(request)
        if url_to_redirect := self._handle_special_query_params(request):
            return redirect(url_to_redirect, permanent=True)
        if url_to_redirect := self._redirect_embeds_to_assistant_v2(request):
            response = redirect(url_to_redirect)
            # Publishing a fiche moves its embeds to the V2: a cached redirect
            # would keep them on the wrong assistant.
            add_never_cache_headers(response)
            return response

        response = self.get_response(request)

        # Prepare response
        self._set_logged_in_cookie(request, response)
        # Pages render differently in an iframe: nginx caches each version apart.
        patch_vary_headers(response, ["Sec-Fetch-Dest"])
        self._cleanup_vary_header(response)

        return response

    # Legacy routes that embeds open, and their assistant V2 counterparts.
    ASSISTANT_V2_ROUTES = {
        "qfdmd:home": "assistant:home",
        "qfdmd:dechet": "assistant:home",
        "qfdmd:synonyme-detail": "assistant:produit",
    }

    def _redirect_embeds_to_assistant_v2(self, request) -> str | None:
        """Send embeds to the assistant V2, whatever code the embedder copied.

        `iframe.js` always adds `ref`; a bare `<iframe>` has none, but its
        browser sends `Sec-Fetch-Dest: iframe`. Either tells an embed from a
        visit to the site. `data-objet` is a fiche or a legacy synonyme slug,
        resolved to its fiche as the legacy assistant does; a fiche that does not
        exist in V2 stays on the legacy assistant rather than 404ing.
        """
        if "ref" not in request.GET and not request.iframe:
            return None
        try:
            match = resolve(request.path)
        except Resolver404:
            return None
        if not (target := self.ASSISTANT_V2_ROUTES.get(match.view_name)):
            return None
        url_kwargs = match.kwargs
        if slug := match.kwargs.get("slug"):
            if not (fiche_slug := self._fiche_slug(slug)):
                return None
            url_kwargs = {**match.kwargs, "slug": fiche_slug}
        return self._build_redirect_url(
            target,
            request.GET,
            [],
            **url_kwargs,
        )

    @staticmethod
    def _fiche_slug(slug: str) -> str | None:
        from qfdmd.models import ProduitPage, Synonyme

        fiches = ProduitPage.objects.live()
        if fiches.filter(slug=slug).exists():
            return slug
        synonyme = Synonyme.objects.filter(slug=slug).first()
        page = synonyme and synonyme.wagtail_page
        if page and fiches.filter(pk=page.pk).exists():
            return page.slug
        return None

    def _handle_special_query_params(self, request) -> str | None:
        """Old embeds open the home page with `?carte`, `?iframe` or `?formulaire`,
        sometimes through a legacy domain that nginx sends here."""
        try:
            if resolve(request.path).view_name not in ("qfdmd:home", "qfdmd:dechet"):
                return
        except Resolver404:
            # Paths that don't match any urlpattern (e.g. Wagtail's preview
            # dummy request path for pages with accented slugs, see
            # PreviewableMixin._get_dummy_headers) can't be the home view.
            return

        if self.CARTE_PARAM in request.GET:
            return self._build_redirect_url(
                "qfdmo:carte", request.GET, [self.CARTE_PARAM, self.IFRAME_PARAM]
            )

        if self.IFRAME_PARAM in request.GET or self.FORMULAIRE_PARAM in request.GET:
            return self._build_redirect_url(
                "qfdmo:formulaire",
                request.GET,
                [self.IFRAME_PARAM, self.FORMULAIRE_PARAM],
            )
        return None

    def _build_redirect_url(
        self,
        view_name: str,
        get_params,
        params_to_remove: list,
        **url_kwargs,
    ) -> str:
        from urllib.parse import urljoin

        get_params_copy = get_params.copy()

        for param in params_to_remove:
            get_params_copy.pop(param, None)  # Use pop() to avoid KeyError

        query_string = get_params_copy.urlencode()
        relative_url = reverse(view_name, kwargs=url_kwargs)

        base_url = settings.BASE_URL.rstrip("/")
        absolute_url = urljoin(base_url, relative_url.lstrip("/"))
        return f"{absolute_url}?{query_string}" if query_string else absolute_url

    def _set_logged_in_cookie(self, request, response):
        """Set or update the 'logged-in' header based on authentication.
        It is use to bypass cache by nginx.

        If present, the logged_in cookie bypasses the cache."""
        cookie_name = self.LOGGED_IN_COOKIE

        # In some cases, gunicorn can be reached directly without going through
        # nginx, when reaching http://localhost:8000 directly for example, that
        # triggers a DisallowedHost error as localhost is not in
        # settings.ALLOWED_HOSTS.
        # This causes user to not be defined on request object and raises an
        # AttributeError hiding the underlying DisallowedHost error.
        if hasattr(request, "user") and request.user.is_authenticated:
            response.set_cookie(cookie_name, "1")
        elif request.COOKIES.get(cookie_name):
            response.delete_cookie(cookie_name)

    def _prepare_request_if_iframe(self, request):
        """Detect if the request comes from an iframe.
        Detection is based on the Sec-Fetch-Dest header, which is set by modern
        browsers when a request is made from within an iframe.
        """
        request.iframe = request.headers.get("Sec-Fetch-Dest") == "iframe"

    @staticmethod
    def _cleanup_vary_header(response):
        """Remove 'Cookie' from the Vary header so nginx can cache without
        fragmenting by every cookie value."""
        vary_header = response.headers.get("Vary", "")
        cleaned = [
            v.strip()
            for v in vary_header.split(",")
            if v.strip() and v.strip().lower() != "cookie"
        ]
        if cleaned:
            response.headers["Vary"] = ", ".join(cleaned)
        else:
            response.headers.pop("Vary", None)
