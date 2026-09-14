import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from assistant.lieu import gestes_de, infos_pratiques_de, propose_le_bonus
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    LabelQualiteFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory, GroupeActionFactory

pytestmark = pytest.mark.django_db


class TestBonusReparation:
    def test_un_lieu_sans_label_ne_propose_pas_le_bonus(self):
        assert not propose_le_bonus(DisplayedActeurFactory())

    @pytest.mark.parametrize(
        "code", ["bonusrepar", "BonusRepar_ASL", "bonusrepar_ABJ_TH"]
    )
    def test_les_variantes_du_bonus_comptent_toutes(self, code):
        """Les éco-organismes déclarent le même dispositif sous des codes
        différents : les distinguer afficherait deux fois le même label."""
        lieu = DisplayedActeurFactory()
        lieu.labels.add(LabelQualiteFactory(code=code))

        assert propose_le_bonus(lieu)

    @pytest.mark.parametrize("code", ["ess", "reparacteur", "qualirepar"])
    def test_les_autres_labels_sont_ecartes_du_mvp(self, code):
        """#3295 ne retient que le Bonus Réparation, pas ESS ni Répar'Acteurs."""
        lieu = DisplayedActeurFactory()
        lieu.labels.add(LabelQualiteFactory(code=code))

        assert not propose_le_bonus(lieu)


class TestInfosPratiques:
    def test_un_lieu_sans_precision_n_affiche_rien(self):
        lieu = DisplayedActeurFactory(
            uniquement_sur_rdv=False,
            exclusivite_de_reprisereparation=False,
            reprise="",
            public_accueilli="",
            consignes_dacces="",
            lieu_prestation="SUR_PLACE",
        )

        assert infos_pratiques_de(lieu) == []

    def test_sur_place_seul_n_est_pas_signale(self):
        """C'est le cas courant : le dire n'apprend rien."""
        lieu = DisplayedActeurFactory(lieu_prestation="SUR_PLACE")

        assert "Sur place ou à domicile" not in infos_pratiques_de(lieu)

    def test_le_domicile_est_signale(self):
        lieu = DisplayedActeurFactory(lieu_prestation="SUR_PLACE_OU_A_DOMICILE")

        assert "Sur place ou à domicile" in infos_pratiques_de(lieu)

    def test_les_precisions_du_mvp_sont_reprises(self):
        lieu = DisplayedActeurFactory(
            uniquement_sur_rdv=True,
            exclusivite_de_reprisereparation=True,
            reprise="1 pour 1",
            public_accueilli="Particuliers",
        )

        infos = infos_pratiques_de(lieu)

        assert "Uniquement sur rendez-vous" in infos
        assert any("propres marques" in info for info in infos)
        assert any("1 pour 1" in info for info in infos)
        assert any("Particuliers" in info for info in infos)


class TestPageLieu:
    def test_la_fiche_affiche_l_identite(self, client):
        lieu = DisplayedActeurFactory(
            nom="Ressourcerie", nom_commercial="La Recyclerie"
        )

        contenu = client.get(
            reverse("assistant:lieu", args=[lieu.uuid])
        ).content.decode()

        assert "La Recyclerie" in contenu

    def test_le_telephone_n_est_pas_un_lien(self, client):
        """Le MVP affiche le téléphone en texte, sans action (#3295)."""
        lieu = DisplayedActeurFactory(telephone="0299000000")

        contenu = client.get(
            reverse("assistant:lieu", args=[lieu.uuid])
        ).content.decode()

        assert "0299000000" in contenu
        assert "tel:" not in contenu

    def test_le_site_n_est_pas_un_lien(self, client):
        lieu = DisplayedActeurFactory(url="https://exemple.fr")

        contenu = client.get(
            reverse("assistant:lieu", args=[lieu.uuid])
        ).content.decode()

        assert "exemple.fr" in contenu
        assert '<a href="https://exemple.fr"' not in contenu

    def test_la_fraicheur_de_la_donnee_est_affichee(self, client):
        lieu = DisplayedActeurFactory()

        contenu = client.get(
            reverse("assistant:lieu", args=[lieu.uuid])
        ).content.decode()

        assert "Dernière mise à jour" in contenu

    def test_le_prefetch_evite_les_requetes_en_cascade(self, client):
        """`pour_le_detail()` charge le lieu, ses labels et ses sources d'un coup.

        Compter les requêtes de la page entière mesurerait surtout les
        processeurs de contexte (DSFR, menus), sans rapport avec la fiche.
        Seules celles portant sur le lieu sont donc retenues.
        """
        lieu = DisplayedActeurFactory()
        lieu.labels.add(LabelQualiteFactory(code="bonusrepar"))

        with CaptureQueriesContext(connection) as requetes:
            client.get(reverse("assistant:lieu", args=[lieu.uuid]))

        sur_le_lieu = [
            requete
            for requete in requetes.captured_queries
            if "displayedacteur" in requete["sql"]
        ]
        assert len(sur_le_lieu) == 3


class TestGestesDuLieu:
    def test_un_lieu_sans_proposition_n_a_pas_de_geste(self):
        assert gestes_de(DisplayedActeurFactory()) == []

    def test_les_gestes_sont_dedupliques(self):
        """Plusieurs actions partagent un groupe : « Réparer » ne doit pas
        s'afficher deux fois."""
        lieu = DisplayedActeurFactory()
        groupe = GroupeActionFactory(code="reparer", libelle_court="Réparer")
        for code in ("reparer", "donner"):
            DisplayedPropositionServiceFactory(
                acteur=lieu, action=ActionFactory(code=code, groupe_action=groupe)
            )

        assert [g["code"] for g in gestes_de(lieu)] == ["reparer"]

    def test_les_gestes_suivent_l_ordre_de_la_spec(self):
        lieu = DisplayedActeurFactory()
        for code, libelle in [("trier", "Déposer"), ("reparer", "Réparer")]:
            groupe = GroupeActionFactory(code=code, libelle_court=libelle)
            DisplayedPropositionServiceFactory(
                acteur=lieu, action=ActionFactory(code=code, groupe_action=groupe)
            )

        assert [g["code"] for g in gestes_de(lieu)] == ["reparer", "trier"]
