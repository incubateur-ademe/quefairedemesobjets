from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView


@method_decorator(ensure_csrf_cookie, name="dispatch")
class RevueSuggestionsView(UserPassesTestMixin, TemplateView):
    """Shell page of the review screen: the React application handles the routing
    of every path below /data/revue/."""

    template_name = "data/revue.html"
    login_url = reverse_lazy("admin:login")

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bootstrap"] = {
            "basepath": reverse("revue:index"),
            "apiBase": "/api/suggestions",
            "adminBase": reverse("admin:index"),
            "environment": settings.ENVIRONMENT,
            "user": {
                "id": self.request.user.id,
                "username": self.request.user.get_username(),
            },
        }
        return context
