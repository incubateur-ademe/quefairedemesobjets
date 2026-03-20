import pytest
from core.models.constants import EMPTY_ACTEUR_FIELD
from dags.crawl.config.columns import COLS
from dags.crawl.tasks.business_logic.crawl_urls_read_urls_from_db import (
    crawl_urls_read_urls_from_db,
)
from unit_tests.qfdmo.acteur_factory import VueActeurFactory


@pytest.mark.django_db()
class TestCrawlUrlsSelectFromDb:
    def test_qfdmo_displayedacteur_url(self):
        VueActeurFactory(url="")
        # The special empty case we don't want to retrieve
        VueActeurFactory(url=EMPTY_ACTEUR_FIELD, nom="url déjà mise à vide")
        a1 = VueActeurFactory(url="https://test.com/1", nom="Acteur 1")
        a2a = VueActeurFactory(url="https://test.com/2", nom="Acteur 2a")
        a2b = VueActeurFactory(url="https://test.com/2", nom="Acteur 2b")
        VueActeurFactory(url="https://test.com/2", nom="BEYOND LIMIT")
        VueActeurFactory(
            url="https://test.com/NONACTIF",
            nom="Acteur NON ACTIF",
            statut="INACTIF",
        )

        limit = 3
        print("before")
        df = crawl_urls_read_urls_from_db(limit)
        print("df")
        print(df)
        assert df[COLS.URL_ORIGIN].tolist() == [
            "https://test.com/1",
            "https://test.com/2",
        ]
        assert df[COLS.ACTEURS].tolist() == [
            [{COLS.ID: a1.pk, "nom": "Acteur 1", "est_parent": False}],
            [
                {COLS.ID: a2a.pk, "nom": "Acteur 2a", "est_parent": False},
                {COLS.ID: a2b.pk, "nom": "Acteur 2b", "est_parent": False},
            ],
        ]
