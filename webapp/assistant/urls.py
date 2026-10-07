from django.http import Http404
from django.urls import path

app_name = "assistant"


def not_yet(request, **kwargs):
    # The routes exist so the middleware can reverse them; the screens come
    # with the assistant V2 stack. Until then, keep
    # ASSISTANT_V2_BETA_TESTERS_HOSTS empty.
    raise Http404("Assistant V2 not released yet")


urlpatterns = [
    path("", not_yet, name="home"),
    path("objet/<slug:slug>/", not_yet, name="produit"),
]
