import logging

from core.emoji_aria import hide_emojis_from_assistive_tech

logger = logging.getLogger(__name__)

SITE_VIEW_NAMES = frozenset(
    {"wagtail_serve", "qfdmd:home", "qfdmd:synonyme-detail", "readable_sitemap"}
)


class HideEmojisMiddleware:
    """Keep decorative emojis typed in the CMS out of the accessibility tree.

    Only the "Que faire" site pages are processed: map, form, info-tri, data
    back-office, turbo frames and the assistant are left untouched.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if self._should_skip(request, response):
            return response

        try:
            charset = response.charset or "utf-8"
            content = hide_emojis_from_assistive_tech(
                response.content.decode(charset)
            ).encode(charset)
        except Exception:
            logger.warning(
                "Emojis not hidden from assistive technologies on %s",
                request.path,
                exc_info=True,
            )
            return response

        response.content = content
        return response

    @staticmethod
    def _should_skip(request, response) -> bool:
        resolver_match = request.resolver_match
        return (
            resolver_match is None
            or resolver_match.view_name not in SITE_VIEW_NAMES
            or "Turbo-Frame" in request.headers
            or response.streaming
            or response.status_code != 200
            or response.has_header("Content-Encoding")
            or not response.get("Content-Type", "").startswith("text/html")
        )
