from django.http import HttpResponse, StreamingHttpResponse
from django.test import RequestFactory

from core.middleware import HideEmojisMiddleware

HTML = "<p>✅ ok</p>"
WRAPPED = '<p><span aria-hidden="true">✅</span> ok</p>'


def run(response, path="/page/"):
    request = RequestFactory().get(path)
    return HideEmojisMiddleware(lambda _request: response)(request)


class TestHideEmojisMiddleware:
    def test_wraps_emojis_of_html_responses(self):
        response = run(HttpResponse(HTML))
        assert response.content.decode() == WRAPPED

    def test_leaves_other_content_types_alone(self):
        response = run(HttpResponse(HTML, content_type="application/json"))
        assert response.content.decode() == HTML

    def test_leaves_streaming_responses_alone(self):
        response = run(StreamingHttpResponse([HTML]))
        assert b"".join(response.streaming_content).decode() == HTML

    def test_leaves_admin_pages_alone(self):
        response = run(HttpResponse(HTML), path="/cms/pages/")
        assert response.content.decode() == HTML
