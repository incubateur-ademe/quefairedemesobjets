import pytest

from dags.crawl.tasks.business_logic import crawl_urls_select_from_db
from unit_tests.qfdmd.qfdmod_factory import LienFactory
from unit_tests.qfdmo.acteur_factory import DisplayedActeurFactory


@pytest.mark.django_db()
class TestCrawlUrlsSelectFromDb:
    def test_qfdmo_displayedacteur_url(self):
        # Given
        url_type = "qfdmo_displayedacteur.url"

        DisplayedActeurFactory(url="")
        DisplayedActeurFactory(url=None)
        DisplayedActeurFactory(url="https://www.acteur.com/1", nom="Acteur 1")
        DisplayedActeurFactory(url="https://www.acteur.com/2", nom="Acteur 2")
        DisplayedActeurFactory(url="https://www.acteur.com/3", nom="Acteur 3")

        limit = 2
        result = crawl_urls_select_from_db(url_type, limit)
        assert [x["url"] for x in result] == [
            "https://www.acteur.com/1",
            "https://www.acteur.com/2",
        ]
        assert [x["nom"] for x in result] == ["Acteur 1", "Acteur 2"]
        assert all(x["identifiant_unique"] for x in result)

    def test_qfdmd_lien_url(self):
        url_type = "qfdmd_lien.url"
        LienFactory(url="")
        # null value in column "url" of relation "qfdmd_lien"
        # violates not-null constraint
        # LienFactory(url=None)
        LienFactory(url="https://www.lien.com/A", titre_du_lien="Lien A")
        LienFactory(url="https://www.lien.com/B", titre_du_lien="Lien B")
        LienFactory(url="https://www.lien.com/C", titre_du_lien="Lien C")

        limit = 2
        result = crawl_urls_select_from_db(url_type, limit)
        assert [x["url"] for x in result] == [
            "https://www.lien.com/A",
            "https://www.lien.com/B",
        ]
        assert [x["titre_du_lien"] for x in result] == ["Lien A", "Lien B"]
        assert all(x["id"] for x in result)
