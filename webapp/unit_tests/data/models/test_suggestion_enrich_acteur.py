import pytest
from data.models.suggestion import SuggestionAction
from data.views import get_context_from_suggestion_groupe, update_suggestion_groupe
from qfdmo.models.acteur import Acteur, ActeurStatus, RevisionActeur
from unit_tests.data.models.suggestion_factory import (
    SuggestionCohorteFactory,
    SuggestionGroupeFactory,
    SuggestionUnitaireFactory,
)
from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory

CLOSED_CHAMPS_VALEURS = [
    ("statut", ActeurStatus.INACTIF),
    ("siret_is_closed", "True"),
    ("parent_reason", "SIRET fermé"),
]


def _cell(table, row_label, column_key):
    row = next(row for row in table.rows if row.cells[0].html_content == row_label)
    return next(cell for cell in row.cells if cell.column_key == column_key)


@pytest.fixture
def acteur():
    return ActeurFactory(identifiant_unique="A1", statut=ActeurStatus.ACTIF)


@pytest.fixture
def parent():
    return RevisionActeurFactory(identifiant_unique="P1", statut=ActeurStatus.ACTIF)


@pytest.fixture
def revision_acteur(acteur, parent):
    return RevisionActeurFactory(
        identifiant_unique=acteur.identifiant_unique,
        statut=ActeurStatus.ACTIF,
        parent=parent,
    )


@pytest.fixture
def suggestion_groupe_closed(acteur, revision_acteur, parent):
    suggestion_groupe = SuggestionGroupeFactory(
        suggestion_cohorte=SuggestionCohorteFactory(
            type_action=SuggestionAction.ENRICH_ACTEURS_CLOSED,
        ),
        acteur=acteur,
        revision_acteur=revision_acteur,
        parent_revision_acteur=parent,
    )
    for champ, valeur in CLOSED_CHAMPS_VALEURS:
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="RevisionActeur",
            revision_acteur_id=acteur.identifiant_unique,
            champs=[champ],
            valeurs=[valeur],
        )
    return suggestion_groupe


@pytest.mark.django_db
class TestSuggestionGroupeTypeEnrichActeur:
    def test_closed_displayed_like_source_without_tabs(self, suggestion_groupe_closed):
        context = get_context_from_suggestion_groupe(suggestion_groupe_closed)

        assert context["identifiant_unique"] == "A1"
        assert context["parent_revision_acteur"].identifiant_unique == "P1"
        assert not context["suggestion_groupe_type"].display_tab

        table = context["comparison_table"]
        assert [column.key for column in table.columns] == [
            "label",
            "source",
            "correction",
            "parent",
        ]
        assert all(
            cell.column_key not in ["report_revision", "report_parent"]
            for row in table.rows
            for cell in row.cells
        )
        # 1 row per field, in the SuggestionSourceModel order
        assert [row.cells[0].html_content for row in table.rows] == [
            "statut",
            "siret_is_closed",
            "parent_reason",
        ]
        # The suggestion is displayed as a diff in the correction column
        correction = _cell(table, "statut", "correction").fields[0].display_html
        assert correction == '<span class="suggestion-text-added">IN</span>ACTIF'

    def test_edit_on_parent_then_apply(self, suggestion_groupe_closed):
        # Same call as an edition in the parent column of the admin
        _, errors = update_suggestion_groupe(
            suggestion_groupe_closed,
            "ParentRevisionActeur",
            {"statut": ActeurStatus.INACTIF},
            [("statut",)],
        )
        assert errors is None
        assert suggestion_groupe_closed.suggestion_unitaires.filter(
            suggestion_modele="ParentRevisionActeur",
            parent_revision_acteur_id="P1",
            champs=["statut"],
        ).exists()

        suggestion_groupe_closed.apply()

        revision = RevisionActeur.objects.get(pk="A1")
        assert revision.statut == ActeurStatus.INACTIF
        assert revision.siret_is_closed is True
        assert revision.parent_reason == "SIRET fermé"
        assert RevisionActeur.objects.get(pk="P1").statut == ActeurStatus.INACTIF
        # Base acteur untouched
        assert Acteur.objects.get(pk="A1").statut == ActeurStatus.ACTIF

    def test_rgpd_acteur_without_revision(self, acteur):
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.ENRICH_ACTEURS_RGPD,
            ),
            acteur=acteur,
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            acteur_id=acteur.identifiant_unique,
            champs=["nom"],
            valeurs=["ANONYMISE POUR RAISON RGPD"],
        )

        table = get_context_from_suggestion_groupe(suggestion_groupe)[
            "comparison_table"
        ]
        # No parent: no parent columns
        assert "parent" not in [column.key for column in table.columns]
        source = _cell(table, "nom", "source").fields[0].display_html
        assert "ANONYMISE" in source

        suggestion_groupe.apply()

        assert Acteur.objects.get(pk="A1").nom == "ANONYMISE POUR RAISON RGPD"
        assert not RevisionActeur.objects.filter(pk="A1").exists()

    def test_acteur_only_as_parent(self, parent):
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.ENRICH_ACTEURS_CLOSED,
            ),
            parent_revision_acteur=parent,
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="ParentRevisionActeur",
            parent_revision_acteur_id=parent.identifiant_unique,
            champs=["statut"],
            valeurs=[ActeurStatus.INACTIF],
        )

        context = get_context_from_suggestion_groupe(suggestion_groupe)

        assert context["identifiant_unique"] == "P1"
        parent_cell = _cell(context["comparison_table"], "statut", "parent")
        assert parent_cell.fields[0].display_html == (
            '<span class="suggestion-text-added">IN</span>ACTIF'
        )
