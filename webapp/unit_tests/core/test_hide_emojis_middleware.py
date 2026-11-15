import logging

import pytest
from django.http import HttpResponse, StreamingHttpResponse
from django.test import RequestFactory
from django.urls import resolve

from core.middleware import HideEmojisMiddleware

HTML = "<p>✅ ok</p>"
WRAPPED = '<p><span aria-hidden="true" style="white-space: pre-wrap">✅ </span>ok</p>'


def run(response, path="/qui-sommes-nous/", **headers):
    request = RequestFactory().get(path, **headers)
    request.resolver_match = resolve(path)
    return HideEmojisMiddleware(lambda _request: response)(request)


class TestHideEmojisMiddleware:
    @pytest.mark.parametrize(
        "path", ["/", "/qui-sommes-nous/", "/dechet/pomme/", "/plan-du-site/"]
    )
    def test_wraps_emojis_of_site_pages(self, path):
        assert run(HttpResponse(HTML), path).content.decode() == WRAPPED

    @pytest.mark.parametrize(
        "path",
        [
            "/carte",
            "/formulaire",
            "/infotri/",
            "/data/revue/",
            "/assistant/",
            "/assistant/recherche/",
            "/cms/pages/",
            "/lookbook/",
        ],
    )
    def test_leaves_other_views_alone(self, path):
        assert run(HttpResponse(HTML), path).content.decode() == HTML

    def test_leaves_turbo_frame_requests_alone(self):
        response = run(HttpResponse(HTML), HTTP_TURBO_FRAME="carte")
        assert response.content.decode() == HTML

    def test_leaves_unresolved_requests_alone(self):
        request = RequestFactory().get("/")
        request.resolver_match = None
        response = HideEmojisMiddleware(lambda _request: HttpResponse(HTML))(request)
        assert response.content.decode() == HTML

    def test_leaves_other_content_types_alone(self):
        response = run(HttpResponse(HTML, content_type="application/json"))
        assert response.content.decode() == HTML

    def test_leaves_streaming_responses_alone(self):
        response = run(StreamingHttpResponse([HTML]))
        assert b"".join(response.streaming_content).decode() == HTML

    def test_leaves_non_200_responses_alone(self):
        response = run(HttpResponse(HTML, status=404))
        assert response.content.decode() == HTML

    def test_leaves_encoded_responses_alone(self):
        response = HttpResponse(HTML, headers={"Content-Encoding": "gzip"})
        assert run(response).content.decode() == HTML

    def test_returns_original_response_and_logs_when_processing_fails(
        self, monkeypatch, caplog
    ):
        def fail(_html):
            raise ValueError("boom")

        monkeypatch.setattr("core.middleware.hide_emojis_from_assistive_tech", fail)
        with caplog.at_level(logging.WARNING, logger="core.middleware"):
            response = run(HttpResponse(HTML))
        assert response.status_code == 200
        assert response.content.decode() == HTML
        assert "Emojis not hidden" in caplog.text

    def test_returns_original_response_when_body_cannot_be_decoded(self):
        response = HttpResponse(b"\xff\xfe<p>x</p>")
        assert run(response).content == b"\xff\xfe<p>x</p>"
