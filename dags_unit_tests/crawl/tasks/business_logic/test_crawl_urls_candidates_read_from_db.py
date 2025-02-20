import pytest
from crawl.tasks.business_logic.candidates.read_from_db import (
    crawl_urls_candidates_read_from_db,
)

from unit_tests.qfdmo.acteur_factory import DisplayedActeurFactory


@pytest.mark.django_db()
class TestCrawlUrlsSelectFromDb:
    def test_qfdmo_displayedacteur_url(self):
        url_type = "qfdmo_displayedacteur.url"

        DisplayedActeurFactory(url="")
        DisplayedActeurFactory(url=None)
        a1 = DisplayedActeurFactory(url="https://www.acteur.com/1", nom="Acteur 1")
        a2 = DisplayedActeurFactory(url="https://www.acteur.com/2", nom="Acteur 2")
        DisplayedActeurFactory(url="https://www.acteur.com/3", nom="Acteur 3")
        DisplayedActeurFactory(
            url="https://www.acteur.com/NONACTIF",
            nom="Acteur NON ACTIF",
            statut="INACTIF",
        )

        limit = 2
        df = crawl_urls_candidates_read_from_db(url_type, limit)
        assert df["identifiant_unique"].tolist() == [a1.pk, a2.pk]
        assert df["url_original"].tolist() == [
            "https://www.acteur.com/1",
            "https://www.acteur.com/2",
        ]
