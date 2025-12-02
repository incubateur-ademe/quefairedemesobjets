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
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps import views as sitemaps_views
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView
from sites_faciles.content_manager.urls import urlpatterns as sites_faciles_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.sitemap_generator import Sitemap
from wagtail.contrib.sitemaps.views import index
from wagtail.documents import urls as wagtaildocs_urls

from qfdmd.models import Synonyme

from .api import api
from .views import AutocompleteSynonyme, autocomplete_address, backlink, robots_txt

info_dict = {
    "queryset": Synonyme.objects.filter().order_by("nom"),
    "date_field": "modifie_le",
}


class PaginatedSitemap(GenericSitemap):
    limit = 500


sitemaps = {
    "produits": PaginatedSitemap(info_dict, priority=1.0),
    "pages": Sitemap(),
}

autocomplete_urlpatterns = [
    path(
        "autocomplete/synonyme",
        AutocompleteSynonyme.as_view(),
        name="autocomplete_synonyme",
    ),
    path(
        "autocomplete/address",
        autocomplete_address,
        name="autocomplete_address",
    ),
]
sitemap_urlpatterns = [
    path(
        "sitemap.xml",
        index,
        {"sitemaps": sitemaps},
        name="wagtail.contrib.sitemaps.views",
    ),
    path(
        "sitemap-<section>.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path(
        "sitemap-<section>.xml",
        sitemaps_views.sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]

urlpatterns = (
    autocomplete_urlpatterns
    + sitemap_urlpatterns
    + [
        path("admin/", admin.site.urls),
        path("api/", api.urls),
        path("robots.txt", robots_txt),
        path("embed/backlink", backlink),
        path("", include(("qfdmo.urls", "qfdmo"), namespace="qfdmo")),
        path("", include(("qfdmd.urls", "qfdmd"), namespace="qfdmd")),
        path("infotri/", include(("infotri.urls", "infotri"), namespace="infotri")),
        path(
            "docs/",
            TemplateView.as_view(template_name="techdocs.html"),
            name="techdocs",
        ),
    ]
)

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.views.defaults import page_not_found, server_error

    if "debug_toolbar" in settings.INSTALLED_APPS:
        urlpatterns.extend([path("__debug__/", include("debug_toolbar.urls"))])
    if "django_browser_reload" in settings.INSTALLED_APPS:
        urlpatterns.extend([path("__reload__/", include("django_browser_reload.urls"))])

    urlpatterns.extend(
        [
            path(
                "dsfr/",
                include(("dsfr_hacks.urls", "dsfr_hacks"), namespace="dsfr_hacks"),
            ),
            path("500", server_error, {"template_name": "ui/pages/500.html"}),
            path("404", page_not_found, {"template_name": "ui/pages/404.html"}),
        ]
    )
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Django Lookbook URLS
urlpatterns.extend([path("lookbook/", include("django_lookbook.urls"))])

# Wagtail urls
urlpatterns.extend(
    [
        path("cms/", include(wagtailadmin_urls)),
        path("documents/", include(wagtaildocs_urls)),
        # This URL should not be move above other "" paths in order to prevent
        # Wagtail pages' slugs to override internal routes defined in the project
        path("", include(sites_faciles_urls)),
    ]
)
