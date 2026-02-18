import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pandas as pd
import pytest
from crawl.config.cohorts import COHORTS
from crawl.config.columns import COLS

from dags.crawl.tasks.business_logic.crawl_urls_check_crawl import (
    CrawlUrlModel,
    crawl_url,
    df_cohorts_split,
)


class MockHTTPHandler(BaseHTTPRequestHandler):
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
    server = HTTPServer(("localhost", 0), MockHTTPHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://localhost:{port}"
    server.shutdown()


def test_fetch_200(test_server):
    result: CrawlUrlModel = crawl_url(f"{test_server}/200")
    assert result.status_code == 200
    assert result.url_reached.endswith("/200")


def test_fetch_404(test_server):
    result: CrawlUrlModel = crawl_url(f"{test_server}/404")
    assert result.status_code == 404
    assert result.url_reached.endswith("/404")


def test_fetch_500(test_server):
    result: CrawlUrlModel = crawl_url(f"{test_server}/500")
    assert result.status_code == 500
    assert result.url_reached.endswith("/500")


def test_fetch_timeout(test_server):
    result: CrawlUrlModel = crawl_url(f"{test_server}/slow", timeout=1)
    assert result.status_code is None
    assert "Read timed out" in (result.error or "")


def test_fetch_redirect(test_server):
    result: CrawlUrlModel = crawl_url(f"{test_server}/redirect")
    assert result.status_code == 200
    assert result.url_reached.endswith("/200")


class TestCrawlUrlsCheckCrawl:

    def test_df_cohorts_split(self):  # noqa
        # 🟢 URL en succès ET inchangée
        case_ok_same = {
            COLS.CRAWL_WAS_SUCCESS: True,
            COLS.URL_ORIGIN: "http://localhost:0/200",
            COLS.URLS_TO_TRY: ["http://localhost:0/200"],
            COLS.CRAWL_URL_SUCCESS: "http://localhost:0/200",
            COLS.DOMAINS_TO_TRY: ["localhost"],
        }
        # 🟡 URL différente HTTPs dispo -> HTTPs proposée
        case_diff_standard = {
            COLS.CRAWL_WAS_SUCCESS: True,
            COLS.URL_ORIGIN: "http://www.google.com/",
            COLS.URLS_TO_TRY: ["https://www.google.com/"],
            COLS.CRAWL_URL_SUCCESS: "https://www.google.com/",
            COLS.DOMAINS_TO_TRY: ["www.google.com"],
        }
        # 🟡 URL différente (et pas juste HTTPs) -> nouvelle proposée
        case_diff_other = {
            COLS.CRAWL_WAS_SUCCESS: True,
            COLS.URL_ORIGIN: "http://localhost:0/redirect",
            COLS.URLS_TO_TRY: ["http://localhost:0/redirect"],
            COLS.CRAWL_URL_SUCCESS: "http://localhost:0/200",
            COLS.DOMAINS_TO_TRY: ["localhost"],
        }
        # 🔴 URL inaccessible -> mise à vide
        case_fail = {
            COLS.CRAWL_WAS_SUCCESS: False,
            COLS.URL_ORIGIN: "http://localhost:0/404",
            COLS.URLS_TO_TRY: ["http://localhost:0/404"],
            COLS.CRAWL_URL_SUCCESS: None,
            COLS.DOMAINS_TO_TRY: ["localhost"],
        }
        df = pd.DataFrame(
            [
                case_ok_same,
                # x 1
                case_diff_standard,
                # x 2
                case_diff_other,
                case_diff_other,
                # x 3
                case_fail,
                case_fail,
                case_fail,
            ]
        )
        df_ok_diff_standard, df_ok_diff_other, df_fail = df_cohorts_split(df=df)
        assert len(df_ok_diff_standard) == 1
        assert len(df_ok_diff_other) == 2
        assert len(df_fail) == 3
        assert df_ok_diff_standard[COLS.COHORT].iloc[0] == COHORTS.CRAWL_DIFF_STANDARD
        assert df_ok_diff_other[COLS.COHORT].iloc[0] == COHORTS.CRAWL_DIFF_OTHER
        assert df_fail[COLS.COHORT].iloc[0] == COHORTS.CRAWL_FAIL
