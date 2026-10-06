import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from assistant.lieu import gestes_of, offers_bonus, practical_info_of
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    LabelQualiteFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory, GroupeActionFactory

pytestmark = pytest.mark.django_db


class TestBonusReparation:
    def test_a_lieu_without_label_does_not_offer_the_bonus(self):
        assert not offers_bonus(DisplayedActeurFactory())

    @pytest.mark.parametrize(
        "code", ["bonusrepar", "BonusRepar_ASL", "bonusrepar_ABJ_TH"]
    )
    def test_every_bonus_variant_counts(self, code):
        """Eco-organismes declare the same scheme under different codes:
        telling them apart would show the same label twice."""
        lieu = DisplayedActeurFactory()
        lieu.labels.add(LabelQualiteFactory(code=code))

        assert offers_bonus(lieu)

    @pytest.mark.parametrize("code", ["ess", "reparacteur", "qualirepar"])
    def test_other_labels_are_left_out_of_the_mvp(self, code):
        """#3295 only keeps the Bonus Réparation, not ESS nor Répar'Acteurs."""
        lieu = DisplayedActeurFactory()
        lieu.labels.add(LabelQualiteFactory(code=code))

        assert not offers_bonus(lieu)


class TestPracticalInfo:
    def test_a_lieu_without_details_shows_nothing(self):
        lieu = DisplayedActeurFactory(
            uniquement_sur_rdv=False,
            exclusivite_de_reprisereparation=False,
            reprise="",
            public_accueilli="",
            consignes_dacces="",
            lieu_prestation="SUR_PLACE",
        )

        assert practical_info_of(lieu) == []

    def test_on_site_alone_is_not_pointed_out(self):
        """It is the common case: saying it tells nothing."""
        lieu = DisplayedActeurFactory(lieu_prestation="SUR_PLACE")

        assert "Sur place ou à domicile" not in practical_info_of(lieu)

    def test_home_service_is_pointed_out(self):
        lieu = DisplayedActeurFactory(lieu_prestation="SUR_PLACE_OU_A_DOMICILE")

        assert "Sur place ou à domicile" in practical_info_of(lieu)

    def test_the_mvp_details_are_carried_over(self):
        lieu = DisplayedActeurFactory(
            uniquement_sur_rdv=True,
            exclusivite_de_reprisereparation=True,
            reprise="1 pour 1",
            public_accueilli="Particuliers",
        )

        infos = practical_info_of(lieu)

        assert "Uniquement sur rendez-vous" in infos
        assert any("propres marques" in info for info in infos)
        assert any("1 pour 1" in info for info in infos)
        assert any("Particuliers" in info for info in infos)


class TestLieuPage:
    def test_the_page_shows_the_identity(self, client):
        lieu = DisplayedActeurFactory(
            nom="Ressourcerie", nom_commercial="La Recyclerie"
        )

        content = client.get(
            reverse("assistant:lieu", args=[lieu.uuid])
        ).content.decode()

        assert "La Recyclerie" in content

    def test_the_phone_is_not_a_link(self, client):
        """The MVP shows the phone as text, without action (#3295)."""
        lieu = DisplayedActeurFactory(telephone="0299000000")

        content = client.get(
            reverse("assistant:lieu", args=[lieu.uuid])
        ).content.decode()

        assert "0299000000" in content
        assert "tel:" not in content

    def test_the_website_is_not_a_link(self, client):
        lieu = DisplayedActeurFactory(url="https://exemple.fr")

        content = client.get(
            reverse("assistant:lieu", args=[lieu.uuid])
        ).content.decode()

        assert "exemple.fr" in content
        assert '<a href="https://exemple.fr"' not in content

    def test_data_freshness_is_shown(self, client):
        lieu = DisplayedActeurFactory()

        content = client.get(
            reverse("assistant:lieu", args=[lieu.uuid])
        ).content.decode()

        assert "Dernière mise à jour" in content

    def test_the_prefetch_avoids_cascading_queries(self, client):
        """`for_the_detail()` loads the lieu, its labels and its sources at once.

        Counting the queries of the whole page would mostly measure the
        context processors (DSFR, menus), unrelated to the page. Only those
        about the lieu are kept.
        """
        lieu = DisplayedActeurFactory()
        lieu.labels.add(LabelQualiteFactory(code="bonusrepar"))

        with CaptureQueriesContext(connection) as queries:
            client.get(reverse("assistant:lieu", args=[lieu.uuid]))

        about_the_lieu = [
            query
            for query in queries.captured_queries
            if "displayedacteur" in query["sql"]
        ]
        assert len(about_the_lieu) == 3


class TestLieuGestes:
    def test_a_lieu_without_proposition_has_no_geste(self):
        assert gestes_of(DisplayedActeurFactory()) == []

    def test_gestes_are_deduplicated(self):
        """Several actions share a groupe: "Réparer" must not show twice."""
        lieu = DisplayedActeurFactory()
        groupe = GroupeActionFactory(code="reparer", libelle_court="Réparer")
        # Two distinct actions of the *same* groupe. The codes are made up:
        # `ActionFactory` does a get_or_create on the code, and reusing an
        # existing code would bring back the real action, with its own groupe.
        for code in ("reparer_test_a", "reparer_test_b"):
            DisplayedPropositionServiceFactory(
                acteur=lieu, action=ActionFactory(code=code, groupe_action=groupe)
            )

        assert [g["code"] for g in gestes_of(lieu)] == ["reparer"]

    def test_gestes_follow_the_spec_order(self):
        lieu = DisplayedActeurFactory()
        for code, label in [("trier", "Déposer"), ("reparer", "Réparer")]:
            groupe = GroupeActionFactory(code=code, libelle_court=label)
            DisplayedPropositionServiceFactory(
                acteur=lieu, action=ActionFactory(code=code, groupe_action=groupe)
            )

        assert [g["code"] for g in gestes_of(lieu)] == ["reparer", "trier"]
