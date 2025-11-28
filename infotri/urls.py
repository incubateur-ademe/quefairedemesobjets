from django.urls import path

from infotri.views import (
    InfotriConfiguratorView,
    InfotriEmbedView,
    get_infotri_configurator_iframe_script,
    get_infotri_iframe_script,
)

urlpatterns = [
    # This route needs to be touched with care as it is embedded
    # on many websites, enabling the load of Info-tri as an iframe
    path("static/infotri.js", get_infotri_iframe_script, name="infotri_script"),
    path(
        "static/infotri-configurator.js",
        get_infotri_configurator_iframe_script,
        name="infotri_configurator_script",
    ),
    path("", InfotriConfiguratorView.as_view(), name="configurator"),
    path("embed", InfotriEmbedView.as_view(), name="embed"),
]
