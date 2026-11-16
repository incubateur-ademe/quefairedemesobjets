from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig
from django.urls import reverse


class QfdmoAdminSite(AdminSite):
    """Default admin site, with extra entries pointing to screens that live
    outside Django admin (e.g. the suggestions review screen)."""

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        if app_label is None and request.user.is_superuser:
            app_list.append(self._revue_app(request))
        return app_list

    def _revue_app(self, request):
        revue_url = reverse("revue:index")
        return {
            "name": "Revue",
            "app_label": "revue",
            "app_url": revue_url,
            "has_module_perms": True,
            "models": [
                {
                    "name": "Revue des suggestions",
                    "object_name": "RevueSuggestions",
                    "perms": {"view": True},
                    "admin_url": revue_url,
                    "add_url": None,
                    "view_only": True,
                }
            ],
        }


class QfdmoAdminConfig(AdminConfig):
    default_site = "core.admin_site.QfdmoAdminSite"
