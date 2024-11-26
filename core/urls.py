"""
URL configuration for quefairedemesobjets project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps import views as sitemaps_views
from django.urls import include, path

from qfdmo.models.acteur import DisplayedActeur

from .api import api

info_dict = {
    "queryset": DisplayedActeur.objects.all().order_by("identifiant_unique"),
    "date_field": "modifie_le",
}


class PaginatedSitemap(GenericSitemap):
    limit = 500


sitemaps = {"items": PaginatedSitemap(info_dict, priority=1.0)}


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("explorer/", include("explorer.urls")),
    path(
        "sitemap.xml",
        sitemaps_views.index,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.index",
    ),
    path(
        "sitemap-<section>.xml",
        sitemaps_views.sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("dsfr/", include(("dsfr_hacks.urls", "dsfr_hacks"), namespace="dsfr_hacks")),
    path("", include(("qfdmo.urls", "qfdmo"), namespace="qfdmo")),
    path("", include(("qfdmd.urls", "qfdmd"), namespace="qfdmd")),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns.extend(
        [
            path("__debug__/", include("debug_toolbar.urls")),
            path("__reload__/", include("django_browser_reload.urls")),
        ]
    )
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.WITH_WAGTAIL:
    from django.conf.urls.static import static
    from wagtail import urls as wagtail_urls
    from wagtail.admin import urls as wagtailadmin_urls
    from wagtail.documents import urls as wagtaildocs_urls

    urlpatterns.extend(
        [
            path("cms/", include(wagtailadmin_urls)),
            path("documents/", include(wagtaildocs_urls)),
            path("pages/", include(wagtail_urls)),
        ]
    )
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
