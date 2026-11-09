import re

import pytest
from django.contrib.gis.geos import Point
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from assistant.lieu import gestes_of, offers_bonus, practical_info_of
from unit_tests.assistant.helpers import action_of, fiche_for, html_of
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    LabelQualiteFactory,
)
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory

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
        """The MVP only keeps the Bonus Réparation, not ESS nor Répar'Acteurs."""
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


def lieu_page(client, lieu, params=None):
    return html_of(client.get(reverse("assistant:lieu", args=[lieu.uuid]), params))


def contact_lines(page):
    """The lines of the "Adresse et contact" section."""
    return list(page.select_one(".qfa-lieu__section p").stripped_strings)


def definitions(page):
    """The "more about the lieu" list, as {term: [values]}."""
    terms = {}
    for dt in page.select("dl dt"):
        values = []
        for sibling in dt.find_next_siblings():
            if sibling.name != "dd":
                break
            values.append(sibling.get_text(strip=True))
        terms[dt.get_text(strip=True)] = values
    return terms


class TestLieuPage:
    def test_the_page_shows_the_identity(self, client):
        lieu = DisplayedActeurFactory(
            nom="Ressourcerie", nom_commercial="La Recyclerie"
        )

        page = lieu_page(client, lieu)

        assert page.select_one("h1").get_text(strip=True) == "La Recyclerie"

    def test_the_phone_is_not_a_link(self, client):
        """The MVP shows the phone as text, without action."""
        lieu = DisplayedActeurFactory(telephone="0299000000")

        page = lieu_page(client, lieu)

        assert "0299000000" in contact_lines(page)
        assert page.select('a[href^="tel:"]') == []

    def test_the_website_is_not_a_link(self, client):
        lieu = DisplayedActeurFactory(url="https://exemple.fr")

        page = lieu_page(client, lieu)

        assert contact_lines(page)[-1] == "https://exemple.fr"
        assert page.select_one(".qfa-lieu__section p").find("a") is None

    def test_data_freshness_is_shown(self, client):
        lieu = DisplayedActeurFactory()

        assert definitions(lieu_page(client, lieu))["Dernière mise à jour"]

    def test_the_distance_follows_the_type_when_located(self, client):
        lieu = DisplayedActeurFactory(location=Point(-0.40, 47.40, srid=4326))

        located = lieu_page(
            client, lieu, {"longitude": "-0.5616", "latitude": "47.4675"}
        )
        not_located = lieu_page(client, lieu)

        line = located.select_one(".qfa-lieu__type").get_text()
        match = re.fullmatch(
            rf"{re.escape(lieu.acteur_type.libelle)} - (\d+),(\d)km", line
        )
        assert match, line
        assert 13 <= int(match[1]) <= 15  # Angers to ~14 km south-east
        assert "km" not in not_located.select_one(".qfa-lieu__type").get_text()

    def test_more_about_the_lieu_lists_its_type_and_labels(self, client):
        """One heading per section, one value per line."""
        lieu = DisplayedActeurFactory()
        lieu.labels.add(
            LabelQualiteFactory(code="ess", libelle="ESS"),
            LabelQualiteFactory(code="reparacteurs", libelle="Répar'Acteurs"),
        )

        terms = definitions(lieu_page(client, lieu))

        assert terms["Type d'enseigne"] == [lieu.acteur_type.libelle]
        assert sorted(terms["Labels"]) == ["ESS", "Répar'Acteurs"]

    def test_the_prefetch_avoids_cascading_queries(self, client):
        """`for_the_detail()` loads the lieu, its labels and its sources at once.

        Only the queries about the lieu are counted: the page's other queries
        (context processors, menus) are unrelated to it.
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


def offer(lieu, groupe_code, label, sous_categorie=None):
    """`lieu` offers the groupe's geste, for `sous_categorie` when given."""
    proposition = DisplayedPropositionServiceFactory(
        acteur=lieu, action=action_of(groupe_code, libelle_court=label)
    )
    if sous_categorie is not None:
        proposition.sous_categories.add(sous_categorie)


class TestLieuGestes:
    def test_a_lieu_without_proposition_has_no_geste(self):
        assert gestes_of(DisplayedActeurFactory()) == []

    def test_gestes_are_deduplicated(self):
        """Several actions share a groupe: "Réparer" must not show twice."""
        lieu = DisplayedActeurFactory()
        # Made-up action codes: an existing one would bring back the real
        # action, with its own groupe.
        for code in ("reparer_test_a", "reparer_test_b"):
            DisplayedPropositionServiceFactory(
                acteur=lieu,
                action=action_of("reparer", code, libelle_court="Réparer"),
            )

        assert [g["code"] for g in gestes_of(lieu)] == ["reparer"]

    def test_gestes_follow_the_spec_order(self):
        lieu = DisplayedActeurFactory()
        offer(lieu, "trier", "Déposer")
        offer(lieu, "reparer", "Réparer")

        assert [g["code"] for g in gestes_of(lieu)] == ["reparer", "trier"]

    def test_only_the_gestes_offered_for_the_objet(self):
        """A shop selling phones and collecting batteries must not show
        "Déposer" on the phone fiche's map."""
        telephone, pile = SousCategorieObjetFactory(), SousCategorieObjetFactory()
        lieu = DisplayedActeurFactory()
        offer(lieu, "vendre_acheter", "Vendre", telephone)
        offer(lieu, "trier", "Déposer", pile)

        assert [g["code"] for g in gestes_of(lieu, [telephone.id])] == [
            "vendre_acheter"
        ]

    @pytest.mark.parametrize("unhandled", [False, True])
    def test_without_a_known_objet_every_geste_is_offered(self, unhandled):
        """Reached without a fiche, or for an objet it does not handle (a
        shared link): every geste, rather than none."""
        telephone, pile = SousCategorieObjetFactory(), SousCategorieObjetFactory()
        lieu = DisplayedActeurFactory()
        offer(lieu, "vendre_acheter", "Vendre", telephone)
        offer(lieu, "trier", "Déposer", pile)
        sous_categorie_ids = [SousCategorieObjetFactory().id] if unhandled else []

        assert [g["code"] for g in gestes_of(lieu, sous_categorie_ids)] == [
            "vendre_acheter",
            "trier",
        ]

    def test_the_page_narrows_the_gestes_to_the_fiche(self, client):
        telephone, pile = SousCategorieObjetFactory(), SousCategorieObjetFactory()
        fiche = fiche_for([telephone])
        lieu = DisplayedActeurFactory()
        offer(lieu, "vendre_acheter", "Vendre", telephone)
        offer(lieu, "trier", "Déposer", pile)

        response = client.get(
            reverse("assistant:lieu", args=[lieu.uuid]), {"fiche": fiche.slug}
        )

        assert [g["code"] for g in response.context["gestes"]] == ["vendre_acheter"]
