"""API v1 endpoints of the assistant's search fields."""

import pytest
from django.urls import reverse

from unit_tests.assistant.helpers import rename_search_term

pytestmark = pytest.mark.django_db


class TestObjets:
    def test_too_short_query_yields_nothing(self, client):
        assert client.get(reverse("api_v1:objets"), {"q": "a"}).json() == {
            "results": []
        }

    @pytest.mark.parametrize(
        "searchable_title,label",
        [
            ("Bidule test", "Bidule test"),
            # Synonymes are typed in lower case in the CMS.
            ("bidule en grès", "Bidule en grès"),
        ],
    )
    def test_suggests_a_fiche_with_its_slug_and_a_capitalized_label(
        self, client, fiche, searchable_title, label
    ):
        rename_search_term(fiche, searchable_title)

        results = client.get(reverse("api_v1:objets"), {"q": "bidule"}).json()[
            "results"
        ]

        assert {"label": label, "slug": fiche.slug} in results
