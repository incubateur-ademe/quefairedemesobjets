from core.emoji_aria import hide_emojis_from_assistive_tech

UNTOUCHED_PATH_PREFIXES = ("/admin/", "/cms/", "/lookbook/")


class HideEmojisMiddleware:
    """Keep decorative emojis typed in the CMS out of the accessibility tree."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            response.streaming
            or response.status_code != 200
            or response.has_header("Content-Encoding")
            or not response.get("Content-Type", "").startswith("text/html")
            or request.path.startswith(UNTOUCHED_PATH_PREFIXES)
        ):
            return response

        charset = response.charset or "utf-8"
        response.content = hide_emojis_from_assistive_tech(
            response.content.decode(charset)
        ).encode(charset)
        return response
