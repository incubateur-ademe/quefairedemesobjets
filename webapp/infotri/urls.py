from django.urls import path

from infotri.views import (
    InfotriConfiguratorView,
    InfotriEmbedView,
    get_infotri_configurator_iframe_script,
    get_infotri_iframe_script,
)

urlpatterns = [
    # These routes are embedded on external sites, do not remove or rename them.
    path("iframe.js", get_infotri_iframe_script, name="infotri_script"),
    path(
        "configurateur.js",
        get_infotri_configurator_iframe_script,
        name="infotri_configurator_script",
    ),
    path("", InfotriConfiguratorView.as_view(), name="configurator"),
    path("embed", InfotriEmbedView.as_view(), name="embed"),
]
