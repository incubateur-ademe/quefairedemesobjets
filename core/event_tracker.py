import uuid

import posthog
from django.conf import settings

# Following https://posthog.com/tutorials/event-tracking-guide
posthog.project_api_key = settings.POSTHOG_PROJECT_API_KEY
posthog.host = settings.POSTHOG_HOST


def track_event(event: str, data: dict) -> None:
    if settings.DEBUG:
        print(f"Track event: {event} with data: {data}")
        return
    posthog.capture(str(uuid.uuid4()), event, data)
