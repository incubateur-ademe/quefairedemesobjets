from sentry_sdk import get_client


def test_sentry_scrubs_the_gateway_auth_token():
    event = {"request": {"headers": {"X-Auth-Token": "the-iam-key"}}}

    get_client().options["event_scrubber"].scrub_event(event)

    assert event["request"]["headers"]["X-Auth-Token"].value == "[Filtered]"


def test_sentry_scrubs_the_gateway_auth_token_in_wsgi_form():
    event = {"extra": {"HTTP_X_AUTH_TOKEN": "the-iam-key"}}

    get_client().options["event_scrubber"].scrub_event(event)

    assert event["extra"]["HTTP_X_AUTH_TOKEN"].value == "[Filtered]"


def test_sentry_keeps_the_default_denylist():
    event = {"request": {"headers": {"Authorization": "Bearer x", "Cookie": "y"}}}

    get_client().options["event_scrubber"].scrub_event(event)

    headers = event["request"]["headers"]
    assert headers["Authorization"].value == "[Filtered]"
    assert headers["Cookie"].value == "[Filtered]"
