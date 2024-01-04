import uuid

import posthog

# Following https://posthog.com/tutorials/event-tracking-guide
posthog.project_api_key = "phc_SGbYOrenShCMKJOQYyl62se9ZqCHntjTlzgKNhrKnzm"
# posthog.personal_api_key = settings.POSTHOG_APIKEY
posthog.host = "https://app.posthog.com"
posthog.debug = True


def track_event(event: str, data: dict) -> None:
    posthog.capture(str(uuid.uuid4()), event, data)
