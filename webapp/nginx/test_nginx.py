# Integration tests for the nginx container (nginx/Dockerfile).
# Requires the container to be running: docker compose --profile lvao up lvao-proxy -d
# Override the target with NGINX_TEST_URL. Django does not need to be running.

import os
import subprocess
import time

import pytest
import requests

import decouple

BASE_URL = decouple.config(
    "NGINX_TEST_URL", "https://quefairedemesdechets.ademe.local"
).rstrip("/")
BASE_DOMAIN = decouple.config("BASE_DOMAIN", "quefairedemesdechets.ademe.local")
LEGACY_DOMAIN = decouple.config("LEGACY_SITE_VITRINE_DOMAIN", "")
CACHE_DISABLED = decouple.config("NGINX_DISABLE_CACHE", "0") == "1"


# Use the mkcert CA bundle when available so requests can verify local certs.
# Falls back to False (no verification) if mkcert is not installed.
def _ssl_verify():
    try:
        caroot = subprocess.check_output(["mkcert", "-CAROOT"], text=True).strip()
        ca = os.path.join(caroot, "rootCA.pem")
        return ca if os.path.exists(ca) else False
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


SSL_VERIFY = _ssl_verify()


def get(path="/", **kwargs) -> requests.Response:
    kwargs.setdefault("allow_redirects", False)
    kwargs.setdefault("timeout", 5)
    kwargs.setdefault("verify", SSL_VERIFY)
    return requests.get(f"{BASE_URL}{path}", **kwargs)


@pytest.fixture(scope="session", autouse=True)
def wait_for_nginx():
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            requests.get(BASE_URL, timeout=2, allow_redirects=False, verify=SSL_VERIFY)
            return
        except requests.ConnectionError:
            time.sleep(0.5)
    pytest.fail(
        f"nginx not reachable at {BASE_URL}. "
        "Run: docker compose --profile lvao up lvao-proxy -d"
    )


class TestHostValidation:
    def test_known_host_is_not_redirected(self):
        resp = get("/", headers={"Host": BASE_DOMAIN})
        assert resp.status_code != 301

    def test_unknown_host_redirects_to_base_domain(self):
        resp = get("/some/path", headers={"Host": "evil.example.com"})
        assert resp.status_code == 301
        location = resp.headers.get("Location", "")
        assert BASE_DOMAIN in location
        assert location.startswith("https://")

    @pytest.mark.skipif(not LEGACY_DOMAIN, reason="LEGACY_SITE_VITRINE_DOMAIN not set")
    def test_legacy_domain_is_not_redirected(self):
        legacy_url = BASE_URL.replace(BASE_DOMAIN, LEGACY_DOMAIN)
        resp = requests.get(
            legacy_url + "/", allow_redirects=False, timeout=5, verify=SSL_VERIFY
        )
        assert resp.status_code != 301

    @pytest.mark.skipif(not LEGACY_DOMAIN, reason="LEGACY_SITE_VITRINE_DOMAIN not set")
    def test_legacy_domain_request_reaches_upstream(self):
        legacy_url = BASE_URL.replace(BASE_DOMAIN, LEGACY_DOMAIN)
        resp = requests.get(
            legacy_url + "/", allow_redirects=False, timeout=5, verify=SSL_VERIFY
        )
        assert resp.status_code in (200, 404, 502, 504)


class TestCacheBypass:
    def test_logged_in_cookie_bypasses_cache(self):
        resp = get("/", headers={"Host": BASE_DOMAIN}, cookies={"logged_in": "1"})
        assert resp.headers.get("X-Cache-Status") == "BYPASS"

    def test_logged_in_cookie_does_not_bypass_embeddable_js(self):
        # The JS location intentionally omits proxy_cache_bypass - logged-in
        # users must still get cached responses for carte.js / iframe.js.
        for path in ("/carte.js", "/iframe.js"):
            resp = get(path, headers={"Host": BASE_DOMAIN}, cookies={"logged_in": "1"})
            assert resp.headers.get("X-Cache-Status") != "BYPASS", (
                f"{path}: expected cache-eligible response for logged-in user, "
                f"got {resp.headers.get('X-Cache-Status')!r}"
            )

    @pytest.mark.skipif(
        not CACHE_DISABLED, reason="Only valid when NGINX_DISABLE_CACHE=1"
    )
    def test_nginx_disable_cache_bypasses_all(self):
        resp = get("/", headers={"Host": BASE_DOMAIN})
        assert resp.headers.get("X-Cache-Status") == "BYPASS"

    @pytest.mark.skipif(
        CACHE_DISABLED, reason="Container built with NGINX_DISABLE_CACHE=1"
    )
    def test_anonymous_request_is_cache_eligible(self):
        resp = get("/", headers={"Host": BASE_DOMAIN})
        assert resp.headers.get("X-Cache-Status") in ("MISS", "HIT", "STALE", "EXPIRED")


class TestCacheKeySecFetchDest:
    @pytest.mark.skipif(
        CACHE_DISABLED, reason="Container built with NGINX_DISABLE_CACHE=1"
    )
    def test_iframe_and_document_have_separate_cache_entries(self):
        # Use a unique path to avoid hitting entries cached by other tests.
        path = f"/?_cache_test={time.time()}"

        resp_doc_1 = get(
            path, headers={"Host": BASE_DOMAIN, "Sec-Fetch-Dest": "document"}
        )
        assert resp_doc_1.headers.get("X-Cache-Status") == "MISS"

        # iframe request to the same URL must be a MISS too,
        # not a HIT from the document entry.
        resp_iframe = get(
            path, headers={"Host": BASE_DOMAIN, "Sec-Fetch-Dest": "iframe"}
        )
        assert resp_iframe.headers.get("X-Cache-Status") == "MISS"

        # Second document request must now be a HIT.
        resp_doc_2 = get(
            path, headers={"Host": BASE_DOMAIN, "Sec-Fetch-Dest": "document"}
        )
        assert resp_doc_2.headers.get("X-Cache-Status") == "HIT"


class TestXCacheStatusHeader:
    @pytest.mark.parametrize(
        "path", ["/", "/carte.js", "/iframe.js", "/static/carte.js"]
    )
    def test_header_always_present(self, path):
        resp = get(path, headers={"Host": BASE_DOMAIN})
        assert "X-Cache-Status" in resp.headers
