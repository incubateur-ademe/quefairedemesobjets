import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from crawl.tasks.business_logic.crawl_url import CrawlUrlModel, crawl_url


class TestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/200":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        elif self.path == "/404":
            self.send_response(404)
            self.end_headers()
        elif self.path == "/500":
            self.send_response(500)
            self.end_headers()
        elif self.path == "/slow":
            time.sleep(2)  # Longer than crawl_url's timeout
            self.send_response(200)
            self.end_headers()
        elif self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/200")
            self.end_headers()
        else:
            self.send_response(400)
            self.end_headers()


@pytest.fixture(scope="module")
def test_server():
    server = HTTPServer(("localhost", 0), TestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://localhost:{port}"
    server.shutdown()


def test_fetch_200(test_server):
    result: CrawlUrlModel = crawl_url(f"{test_server}/200")
    assert result.status_code == 200
    assert result.url_resolved.endswith("/200")


def test_fetch_404(test_server):
    result: CrawlUrlModel = crawl_url(f"{test_server}/404")
    assert result.status_code == 404
    assert result.url_resolved.endswith("/404")


def test_fetch_500(test_server):
    result: CrawlUrlModel = crawl_url(f"{test_server}/500")
    assert result.status_code == 500
    assert result.url_resolved.endswith("/500")


def test_fetch_timeout(test_server):
    result: CrawlUrlModel = crawl_url(f"{test_server}/slow", timeout=1)
    assert result.status_code is None
    assert "Read timed out" in (result.error or "")


def test_fetch_redirect(test_server):
    result: CrawlUrlModel = crawl_url(f"{test_server}/redirect")
    assert result.status_code == 200
    assert result.url_resolved.endswith("/200")
