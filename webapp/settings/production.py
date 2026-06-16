# ruff: noqa: F405
# F405 is suppressed because this file relies on star imports from base.py.
# All names (STORAGES, ENVIRONMENT, etc.) are defined in settings.base
# and intentionally re-used here.
from settings.base import *  # noqa: F403

import logging

import decouple
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# ---------------------------------------------------------------------------
# HTTPS / reverse proxy headers
# ---------------------------------------------------------------------------
# The reverse proxy terminates TLS; these tell Django to trust the forwarded
# protocol and host headers so that redirects & CSRF use the right scheme.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# ---------------------------------------------------------------------------
# Production EMAIL_BACKEND — via SMTP configured through environment
# ---------------------------------------------------------------------------
EMAIL_BACKEND = decouple.config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
    cast=str,
)

# ---------------------------------------------------------------------------
# S3 storage for user-uploaded files (default storage)
# ---------------------------------------------------------------------------
AWS_ACCESS_KEY_ID = decouple.config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = decouple.config("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = decouple.config("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_REGION_NAME = decouple.config("AWS_S3_REGION_NAME", default="")
AWS_S3_ENDPOINT_URL = decouple.config("AWS_S3_ENDPOINT_URL", default="")

if AWS_ACCESS_KEY_ID:
    STORAGES["default"]["BACKEND"] = "storages.backends.s3.S3Storage"

# ---------------------------------------------------------------------------
# Sentry
# ---------------------------------------------------------------------------
SENTRY_DSN = decouple.config("SENTRY_DSN", cast=str, default="")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            ),
        ],
        environment=ENVIRONMENT,
        send_default_pii=False,
        traces_sample_rate=0.01,
    )
