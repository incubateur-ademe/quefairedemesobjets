import pytest
from data.models.suggestion import (
    SuggestionAction,
    SuggestionCohorte,
    SuggestionCohorteStatut,
    SuggestionStatut,
)
from django.contrib.auth.models import User
from unit_tests.data.models.suggestion_factory import (
    SuggestionCohorteFactory,
    SuggestionGroupeFactory,
    SuggestionUnitaireFactory,
)
from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory


@pytest.fixture
def user():
    return User.objects.create_user(username="reviewer", is_superuser=True)


@pytest.fixture
def groupe():
    groupe = SuggestionGroupeFactory(
        suggestion_cohorte=SuggestionCohorteFactory(
            type_action=SuggestionAction.SOURCE_MODIFICATION
        )
    )
    acteur = ActeurFactory()
    revision_acteur = RevisionActeurFactory()
    for modele in ["Acteur", "RevisionActeur"]:
        for champs in [["nom"], ["latitude", "longitude"]]:
            SuggestionUnitaireFactory(
                suggestion_groupe=groupe,
                suggestion_modele=modele,
                champs=champs,
                acteur=acteur if modele == "Acteur" else None,
                revision_acteur=revision_acteur if modele == "RevisionActeur" else None,
            )
    return groupe


class TestSetGroupesStatut:
    @pytest.mark.django_db
    def test_decision_is_traced_on_groupe_and_unitaires(self, groupe, user):
        groupe.suggestion_cohorte.set_groupes_statut(
            [groupe.id], SuggestionStatut.ATRAITER, user=user
        )

        groupe.refresh_from_db()
        assert groupe.statut == SuggestionStatut.ATRAITER
        assert groupe.decision_par == user
        assert groupe.decision_le is not None
        for su in groupe.suggestion_unitaires.all():
            assert su.statut == SuggestionStatut.ATRAITER
            assert su.decision_par == user
            assert su.decision_le is not None

    @pytest.mark.django_db
    def test_avalider_clears_decision(self, groupe, user):
        cohorte = groupe.suggestion_cohorte
        cohorte.set_groupes_statut([groupe.id], SuggestionStatut.REJETEE, user=user)
        cohorte.set_groupes_statut([groupe.id], SuggestionStatut.AVALIDER)

        groupe.refresh_from_db()
        assert groupe.statut == SuggestionStatut.AVALIDER
        assert groupe.decision_par is None
        assert groupe.decision_le is None
        assert not groupe.suggestion_unitaires.exclude(
            statut=SuggestionStatut.AVALIDER
        ).exists()

    @pytest.mark.django_db
    def test_processing_statut_keeps_decision(self, groupe, user):
        cohorte = groupe.suggestion_cohorte
        cohorte.set_groupes_statut([groupe.id], SuggestionStatut.ATRAITER, user=user)
        cohorte.set_groupes_statut([groupe.id], SuggestionStatut.SUCCES)

        groupe.refresh_from_db()
        assert groupe.statut == SuggestionStatut.SUCCES
        assert groupe.decision_par == user


class TestSetLignesStatut:
    @pytest.mark.django_db
    def test_only_the_ligne_unitaires_are_updated(self, groupe, user):
        count = groupe.suggestion_cohorte.set_lignes_statut(
            groupe, [["latitude", "longitude"]], SuggestionStatut.ATRAITER, user=user
        )

        assert count == 2
        statuts = {
            tuple(su.champs): su.statut for su in groupe.suggestion_unitaires.all()
        }
        assert statuts == {
            ("nom",): SuggestionStatut.AVALIDER,
            ("latitude", "longitude"): SuggestionStatut.ATRAITER,
        }
        groupe.refresh_from_db()
        assert groupe.statut == SuggestionStatut.AVALIDER


class TestCohorteStatut:
    @pytest.mark.parametrize(
        "groupe_statuts,expected",
        [
            (set(), None),
            ({"AVALIDER", "SUCCES"}, SuggestionCohorteStatut.AVALIDER),
            ({"ATRAITER", "REJETEE"}, SuggestionCohorteStatut.ENCOURS),
            ({"ENCOURS", "SUCCES"}, SuggestionCohorteStatut.ENCOURS),
            ({"SUCCES", "ERREUR", "REJETEE"}, SuggestionCohorteStatut.SUCCES),
        ],
    )
    def test_compute_cohorte_statut(self, groupe_statuts, expected):
        assert SuggestionCohorte._compute_cohorte_statut(groupe_statuts) == expected

    @pytest.mark.django_db
    def test_recompute_cohorte_statut(self):
        cohorte = SuggestionCohorteFactory()
        SuggestionGroupeFactory(
            suggestion_cohorte=cohorte, statut=SuggestionStatut.SUCCES
        )
        SuggestionGroupeFactory(
            suggestion_cohorte=cohorte, statut=SuggestionStatut.REJETEE
        )

        cohorte.recompute_cohorte_statut()

        cohorte.refresh_from_db()
        assert cohorte.statut == SuggestionCohorteStatut.SUCCES
