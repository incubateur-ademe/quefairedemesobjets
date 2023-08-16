import random

from django.http import HttpRequest

from core.jinja2_handler import is_iframe


class TestIsIframe:
    def test_is_iframe_false(self):
        request = HttpRequest()

        request.GET = {}
        assert is_iframe(request) is False

    def test_is_iframe_true(self):
        request = HttpRequest()

        request.GET = {"iframe": str(random.randint(0, 10))}

        assert is_iframe(request) is True

        request.GET = {"iframe": "anything"}

        assert is_iframe(request) is True
