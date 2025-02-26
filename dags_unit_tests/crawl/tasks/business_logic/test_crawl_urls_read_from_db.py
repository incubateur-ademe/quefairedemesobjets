import pytest
from sources.config.shared_constants import EMPTY_ACTEUR_FIELD

from dags.crawl.config.constants import COL_ACTEURS, COL_ID, COL_URL_ORIGINAL
from dags.crawl.tasks.business_logic.crawl_urls_read_from_db import (
    crawl_urls_candidates_read_from_db,
)
from unit_tests.qfdmo.acteur_factory import DisplayedActeurFactory


@pytest.mark.django_db()
class TestCrawlUrlsSelectFromDb:
    def test_qfdmo_displayedacteur_url(self):
        url_type = "qfdmo_displayedacteur.url"

        DisplayedActeurFactory(url="")
        DisplayedActeurFactory(url=None)
        # The special empty case we don't want to retrieve
        DisplayedActeurFactory(url=EMPTY_ACTEUR_FIELD, nom="url déjà mise à vide")
        a1 = DisplayedActeurFactory(url="https://test.com/1", nom="Acteur 1")
        a2a = DisplayedActeurFactory(url="https://test.com/2", nom="Acteur 2a")
        a2b = DisplayedActeurFactory(url="https://test.com/2", nom="Acteur 2b")
        DisplayedActeurFactory(url="https://test.com/2", nom="BEYOND LIMIT")
        DisplayedActeurFactory(
            url="https://test.com/NONACTIF",
            nom="Acteur NON ACTIF",
            statut="INACTIF",
        )

        limit = 3
        df = crawl_urls_candidates_read_from_db(url_type, limit)
        assert df[COL_URL_ORIGINAL].tolist() == [
            "https://test.com/1",
            "https://test.com/2",
        ]
        assert df[COL_ACTEURS].tolist() == [
            [{COL_ID: a1.pk, "nom": "Acteur 1"}],
            [
                {COL_ID: a2a.pk, "nom": "Acteur 2a"},
                {COL_ID: a2b.pk, "nom": "Acteur 2b"},
            ],
        ]
