from django.urls import re_path

from data.revue.views import RevueSuggestionsView

app_name = "revue"

urlpatterns = [
    # Client-side routing: every path is served by the same page
    re_path(r"^(?:.*)$", RevueSuggestionsView.as_view(), name="index"),
]
