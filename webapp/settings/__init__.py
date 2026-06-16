# Re-export everything from base for backward compatibility
# Specific deployments should reference settings.base directly
# ruff: noqa: F405
# F405 is suppressed because this file re-exports everything from base.py
# for backward compatibility with code that still imports core.settings.
from settings.base import *  # noqa: F403
