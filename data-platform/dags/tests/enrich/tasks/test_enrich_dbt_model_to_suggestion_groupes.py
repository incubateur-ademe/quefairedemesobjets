import json
from datetime import datetime, timezone

import pandas as pd
import pytest
from enrich.config.cohorts import COHORTS
from enrich.config.columns import COLS
from enrich.tasks.business_logic.enrich_dbt_model_to_suggestion_groupes import (
    _unitaires_par_champ,
    enrich_dbt_model_to_suggestion_groupes,
    suggestion_groupes_prepare,
)

from data.models.changes.acteur_rgpd_anonymize import ACTEUR_FIELDS_TO_ANONYMIZE

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _write_and_get_groupes(df, cohort, identifiant_action):
    from data.models.suggestion import SuggestionAction, SuggestionGroupe

    assert enrich_dbt_model_to_suggestion_groupes(
        df=df,
        cohort=cohort,
        identifiant_action=identifiant_action,
        dry_run=False,
    )
    groupes = SuggestionGroupe.objects.filter(
        suggestion_cohorte__identifiant_action=identifiant_action
    ).order_by("id")
    assert groupes.exists()
    assert groupes[0].suggestion_cohorte.type_action in SuggestionAction.values
    return groupes


def _apply(groupes):
    for groupe in groupes:
        groupe.apply()


@pytest.mark.django_db
class TestEnrichSuggestionGroupesVilles:
    @pytest.fixture
    def df_typo(self):
        return pd.DataFrame(
            {
                COLS.SUGGEST_COHORT: [COHORTS.VILLES_TYPO] * 3,
                COLS.ACTEUR_ID: ["typo1", "typo2", "typo3"],
                COLS.ACTEUR_STATUT: ["ACTIF"] * 3,
                COLS.ACTEUR_ADRESSE: ["1 rue", "2 rue", "3 rue"],
                COLS.ACTEUR_CODE_POSTAL: ["12345", "12345", "53000"],
                COLS.ACTEUR_VILLE: ["Pâris", "Pâris", "Lâval"],
                COLS.SUGGEST_VILLE: ["Paris", "Paris", "Laval"],
            }
        )

    @pytest.fixture
    def acteurs(self, df_typo):
        from unit_tests.qfdmo.acteur_factory import ActeurFactory

        for _, row in df_typo.iterrows():
            ActeurFactory(
                identifiant_unique=row[COLS.ACTEUR_ID],
                ville=row[COLS.ACTEUR_VILLE],
            )

    def test_grouped_by_ville_and_applied(self, acteurs, df_typo):
        from qfdmo.models import Acteur, RevisionActeur

        groupes = _write_and_get_groupes(df_typo, COHORTS.VILLES_TYPO, "test_villes")

        # 1 groupe per (current ville -> suggested ville)
        assert len(groupes) == 2
        paris = groupes[0]
        assert paris.contexte == {
            "ville actuel(le)": "Pâris",
            "ville proposé(e)": "Paris",
            "# acteurs": 2,
        }
        unitaires = paris.suggestion_unitaires.order_by("revision_acteur_id")
        assert [u.revision_acteur_id for u in unitaires] == ["typo1", "typo2"]
        assert all(u.suggestion_modele == "RevisionActeur" for u in unitaires)
        assert all(u.champs == ["ville"] for u in unitaires)
        assert all(u.valeurs == ["Paris"] for u in unitaires)

        _apply(groupes)

        assert RevisionActeur.objects.get(pk="typo1").ville == "Paris"
        assert RevisionActeur.objects.get(pk="typo2").ville == "Paris"
        assert RevisionActeur.objects.get(pk="typo3").ville == "Laval"
        # Groupes of several acteurs aren't linked to an acteur
        assert all(
            groupe.acteur_id is None and groupe.revision_acteur_id is None
            for groupe in groupes
        )
        # Base acteur untouched
        assert Acteur.objects.get(pk="typo1").ville == "Pâris"

    def test_parent_uses_parent_revision_acteur(self, acteurs, df_typo):
        groupes = suggestion_groupes_prepare(
            df_typo, COHORTS.VILLES_TYPO, est_parent_map={"typo3": True}
        )
        modeles = {
            unitaire["identifiant_unique"]: unitaire["modele"]
            for groupe in groupes
            for unitaire in groupe["unitaires"]
        }
        assert modeles == {
            "typo1": "RevisionActeur",
            "typo2": "RevisionActeur",
            "typo3": "ParentRevisionActeur",
        }

    def test_dry_run_writes_nothing(self, acteurs, df_typo):
        from data.models.suggestion import SuggestionCohorte

        assert not enrich_dbt_model_to_suggestion_groupes(
            df=df_typo,
            cohort=COHORTS.VILLES_TYPO,
            identifiant_action="test_dry_run",
            dry_run=True,
        )
        assert not SuggestionCohorte.objects.filter(
            identifiant_action="test_dry_run"
        ).exists()


@pytest.mark.django_db
class TestEnrichSuggestionGroupesCodePostal:
    @pytest.fixture
    def df_cp(self):
        return pd.DataFrame(
            {
                COLS.ACTEUR_ID: ["cp1", "cp2", "cp3"],
                COLS.CODE_POSTAL: ["1000", "1000", "75001"],
                COLS.SUGGEST_CODE_POSTAL: ["01000", "01000", "75001"],
            }
        )

    @pytest.fixture
    def acteurs(self, df_cp):
        from unit_tests.qfdmo.acteur_factory import ActeurFactory

        for _, row in df_cp.iterrows():
            ActeurFactory(
                identifiant_unique=row[COLS.ACTEUR_ID],
                code_postal=row[COLS.CODE_POSTAL],
            )

    def test_acteur_cp_applied_on_acteur(self, acteurs, df_cp):
        from qfdmo.models import Acteur, RevisionActeur

        df_cp[COLS.SUGGEST_COHORT] = COHORTS.ACTEUR_CP_TYPO
        groupes = _write_and_get_groupes(df_cp, COHORTS.ACTEUR_CP_TYPO, "test_cp")

        # cp3 is already normalized: nothing to suggest
        assert len(groupes) == 1
        unitaires = groupes[0].suggestion_unitaires.order_by("acteur_id")
        assert [u.acteur_id for u in unitaires] == ["cp1", "cp2"]
        assert all(u.suggestion_modele == "Acteur" for u in unitaires)

        _apply(groupes)

        assert Acteur.objects.get(pk="cp1").code_postal == "01000"
        assert Acteur.objects.get(pk="cp2").code_postal == "01000"
        assert not RevisionActeur.objects.filter(pk__in=["cp1", "cp2"]).exists()

    def test_revision_acteur_cp_applied_on_revision(self, acteurs, df_cp):
        from qfdmo.models import RevisionActeur

        df_cp[COLS.SUGGEST_COHORT] = COHORTS.REVISION_ACTEUR_CP_TYPO
        groupes = _write_and_get_groupes(
            df_cp, COHORTS.REVISION_ACTEUR_CP_TYPO, "test_revision_cp"
        )
        assert all(
            u.suggestion_modele == "RevisionActeur"
            for u in groupes[0].suggestion_unitaires.all()
        )

        _apply(groupes)

        assert RevisionActeur.objects.get(pk="cp1").code_postal == "01000"


@pytest.mark.django_db
class TestEnrichSuggestionGroupesRgpd:
    @pytest.fixture
    def df_rgpd(self):
        return pd.DataFrame(
            {
                COLS.SUGGEST_COHORT: [COHORTS.RGPD] * 2,
                COLS.ACTEUR_ID: ["rgpd1", "rgpd2"],
                COLS.ACTEUR_STATUT: ["ACTIF"] * 2,
                COLS.ACTEUR_NOMS_ORIGINE: ["nom rgpd1", "nom rgpd2"],
                COLS.ACTEUR_NOM: ["nom rgpd1", "nom rgpd2"],
            }
        )

    @pytest.fixture
    def acteurs(self):
        from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory

        # rgpd1 only in base
        ActeurFactory(identifiant_unique="rgpd1", nom="nom rgpd1")
        # rgpd2 in both base and revision
        ActeurFactory(identifiant_unique="rgpd2", nom="nom rgpd2", commentaires="old")
        RevisionActeurFactory(pk="rgpd2", nom="nom rgpd2")

    def test_rgpd_anonymizes_everywhere_without_creating_revision(
        self, acteurs, df_rgpd
    ):
        from qfdmo.models import Acteur, RevisionActeur

        groupes = _write_and_get_groupes(df_rgpd, COHORTS.RGPD, "test_rgpd")

        # 1 groupe per acteur, 1 unitaire per field and per model
        assert len(groupes) == 2
        champs_anonymises = sorted([*ACTEUR_FIELDS_TO_ANONYMIZE, "commentaires"])
        unitaires_par_acteur = {
            groupe.contexte["identifiant_unique"]: groupe.suggestion_unitaires.all()
            for groupe in groupes
        }
        for identifiant_unique, modeles in [
            ("rgpd1", ["Acteur"]),
            ("rgpd2", ["Acteur", "RevisionActeur"]),
        ]:
            unitaires = unitaires_par_acteur[identifiant_unique]
            assert all(len(u.champs) == 1 for u in unitaires)
            for modele in modeles:
                assert (
                    sorted(
                        u.champs[0] for u in unitaires if u.suggestion_modele == modele
                    )
                    == champs_anonymises
                )
            assert {u.suggestion_modele for u in unitaires} == set(modeles)

        _apply(groupes)

        assert not RevisionActeur.objects.filter(pk="rgpd1").exists()
        for instance in [
            Acteur.objects.get(pk="rgpd1"),
            Acteur.objects.get(pk="rgpd2"),
            RevisionActeur.objects.get(pk="rgpd2"),
        ]:
            assert all(
                getattr(instance, field) == value
                for field, value in ACTEUR_FIELDS_TO_ANONYMIZE.items()
            )

        # Comment appended to the existing ones
        commentaires = json.loads(Acteur.objects.get(pk="rgpd2").commentaires)
        assert commentaires[0] == {"message": "old"}
        assert "ANONYMISE POUR RAISON RGPD" in commentaires[1]["message"]


@pytest.mark.django_db
def test_unitaires_par_champ_groups_latitude_longitude():
    unitaires = _unitaires_par_champ(
        "Acteur",
        "a1",
        {"longitude": 2, "nom": "nom", "latitude": 1, "hors_modele_source": "x"},
    )
    assert [(u["champs"], u["valeurs"]) for u in unitaires] == [
        (["nom"], ["nom"]),
        (["latitude", "longitude"], ["1", "2"]),
        (["hors_modele_source"], ["x"]),
    ]


@pytest.mark.django_db
class TestEnrichSuggestionGroupesClosed:
    @pytest.fixture
    def df_not_replaced(self):
        return pd.DataFrame(
            {
                COLS.SUGGEST_COHORT: [COHORTS.CLOSED_NOT_REPLACED_UNITE] * 2,
                COLS.ACTEUR_ID: ["a01", "a02"],
                COLS.ACTEUR_SIRET: ["00000000000001", "00000000000002"],
                COLS.ACTEUR_NOM: ["nom a01", "nom a02"],
                COLS.ACTEUR_STATUT: ["ACTIF"] * 2,
                COLS.ACTEUR_ADRESSE: ["1 rue", "2 rue"],
                COLS.ACTEUR_CODE_POSTAL: ["35001", "35002"],
                COLS.ACTEUR_VILLE: ["Rennes"] * 2,
            }
        )

    @pytest.fixture
    def df_replaced(self):
        return pd.DataFrame(
            {
                COLS.SUGGEST_COHORT: [COHORTS.CLOSED_REP_SAME_SIREN],
                COLS.ACTEUR_ID: ["a1"],
                COLS.ACTEUR_SIRET: ["11111111100001"],
                COLS.ACTEUR_NOM: ["nom a1"],
                COLS.ACTEUR_STATUT: ["ACTIF"],
                COLS.ACTEUR_ADRESSE: ["1 rue"],
                COLS.ACTEUR_CODE_POSTAL: ["35001"],
                COLS.ACTEUR_VILLE: ["Rennes"],
                COLS.SUGGEST_SIRET: ["11111111100002"],
            }
        )

    @pytest.fixture
    def acteurs(self):
        from unit_tests.qfdmo.acteur_factory import ActeurFactory

        for identifiant_unique, siret in [
            ("a01", "00000000000001"),
            ("a02", "00000000000002"),
            ("a1", "11111111100001"),
        ]:
            ActeurFactory(
                identifiant_unique=identifiant_unique,
                siret=siret,
                siren=siret[:9],
            )

    def test_not_replaced(self, acteurs, df_not_replaced):
        from qfdmo.models import ActeurStatus, RevisionActeur

        groupes = _write_and_get_groupes(
            df_not_replaced, COHORTS.CLOSED_NOT_REPLACED_UNITE, "test_not_replaced"
        )
        # 1 groupe per acteur, 1 unitaire per field
        assert len(groupes) == 2
        for groupe in groupes:
            unitaires = groupe.suggestion_unitaires.all()
            assert sorted(u.champs[0] for u in unitaires) == [
                "parent_reason",
                "siret_is_closed",
                "statut",
            ]
            assert all(len(u.champs) == 1 for u in unitaires)
            assert all(u.suggestion_modele == "RevisionActeur" for u in unitaires)

        _apply(groupes)

        closed = RevisionActeur.objects.get(pk="a01")
        assert closed.statut == ActeurStatus.INACTIF
        assert closed.siret_is_closed is True
        assert closed.parent_reason == (
            f"Modifications de l'acteur le {TODAY}: SIRET 00000000000001 détecté"
            " comme fermé dans AE, Pas de remplacement"
        )

    def test_groupe_fks_with_revision_and_parent(self, acteurs, df_not_replaced):
        from unit_tests.qfdmo.acteur_factory import RevisionActeurFactory

        parent = RevisionActeurFactory(identifiant_unique="p01")
        RevisionActeurFactory(identifiant_unique="a01", parent=parent)

        groupes = _write_and_get_groupes(
            df_not_replaced, COHORTS.CLOSED_NOT_REPLACED_UNITE, "test_fks"
        )

        fks = {
            groupe.contexte["identifiant_unique"]: (
                groupe.acteur_id,
                groupe.revision_acteur_id,
                groupe.parent_revision_acteur_id,
            )
            for groupe in groupes
        }
        assert fks == {
            # Revision with a parent: the changes can be reported on it
            "a01": ("a01", "a01", "p01"),
            # No revision
            "a02": ("a02", None, None),
        }

    def test_replaced(self, acteurs, df_replaced):
        from qfdmo.models import Acteur, RevisionActeur

        groupes = _write_and_get_groupes(
            df_replaced, COHORTS.CLOSED_REP_SAME_SIREN, "test_replaced"
        )
        assert len(groupes) == 1
        unitaires = groupes[0].suggestion_unitaires.all()
        assert sorted(u.champs[0] for u in unitaires) == [
            "parent_reason",
            "siren",
            "siret",
            "siret_is_closed",
        ]
        assert all(len(u.champs) == 1 for u in unitaires)

        _apply(groupes)

        assert Acteur.objects.get(pk="a1").siret == "11111111100001"
        revision = RevisionActeur.objects.get(pk="a1")
        assert revision.siret == "11111111100002"
        assert revision.siren == "111111111"
        assert revision.siret_is_closed is False
