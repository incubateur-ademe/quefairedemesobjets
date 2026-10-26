import pytest
from data.models.suggestion import (
    SuggestionAction,
    SuggestionCohorte,
    SuggestionCohorteStatut,
    SuggestionGroupe,
    SuggestionLog,
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
def groupe_with_unitaires():
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


class TestSuggestionCohorte:
    @pytest.mark.parametrize(
        "type_action, expected_result",
        [
            (SuggestionAction.SOURCE_AJOUT, True),
            (SuggestionAction.SOURCE_MODIFICATION, True),
            (SuggestionAction.SOURCE_SUPPRESSION, True),
            (SuggestionAction.CLUSTERING, False),
            ("other_action", False),
        ],
    )
    def test_is_source_type(self, type_action, expected_result):
        instance = SuggestionCohorte(type_action=type_action)

        assert instance.is_source_type is expected_result

    @pytest.mark.parametrize(
        "type_action, expected_result",
        [
            (SuggestionAction.CLUSTERING, True),
            (SuggestionAction.SOURCE_AJOUT, False),
            (SuggestionAction.SOURCE_MODIFICATION, False),
            (SuggestionAction.SOURCE_SUPPRESSION, False),
            ("other_action", False),
        ],
    )
    def test_is_clustering_type(self, type_action, expected_result):
        instance = SuggestionCohorte(type_action=type_action)

        assert instance.is_clustering_type is expected_result

    def test_execution_datetime_formats_iso_datetime_in_identifiant_execution(self):
        instance = SuggestionCohorte(
            identifiant_execution="run_2025-01-02T03:04:05_extra"
        )

        assert instance.execution_datetime == "02/01/2025 03:04"

    def test_execution_datetime_returns_original_when_no_datetime_found(self):
        instance = SuggestionCohorte(identifiant_execution="no_date_here")

        assert instance.execution_datetime == "no_date_here"

    def test_str_includes_id_action_and_formatted_execution_datetime(self):
        instance = SuggestionCohorte(
            identifiant_action="my_action",
            identifiant_execution="run_2025-01-02T03:04:05_extra",
        )
        # Simule un objet sauvegardé avec un id
        instance.id = 1

        assert str(instance) == "1 - my_action -- 02/01/2025 03:04"

    @pytest.mark.django_db
    def test_set_groupes_statut_decision_is_traced(self, groupe_with_unitaires, user):
        groupe = groupe_with_unitaires
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
    def test_set_groupes_statut_avalider_clears_decision(
        self, groupe_with_unitaires, user
    ):
        groupe = groupe_with_unitaires
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
    def test_set_groupes_statut_processing_keeps_decision(
        self, groupe_with_unitaires, user
    ):
        groupe = groupe_with_unitaires
        cohorte = groupe.suggestion_cohorte
        cohorte.set_groupes_statut([groupe.id], SuggestionStatut.ATRAITER, user=user)
        cohorte.set_groupes_statut([groupe.id], SuggestionStatut.SUCCES)

        groupe.refresh_from_db()
        assert groupe.statut == SuggestionStatut.SUCCES
        assert groupe.decision_par == user

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

    @pytest.mark.django_db
    def test_source_cohortes_only_includes_source_types_with_groupes(self):
        ajout = SuggestionCohorteFactory(
            identifiant_action="dag_ajout",
            type_action=SuggestionAction.SOURCE_AJOUT,
        )
        SuggestionGroupeFactory(suggestion_cohorte=ajout)
        modification = SuggestionCohorteFactory(
            identifiant_action="dag_modification",
            type_action=SuggestionAction.SOURCE_MODIFICATION,
        )
        SuggestionGroupeFactory(suggestion_cohorte=modification)
        SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                identifiant_action="dag_clustering",
                type_action=SuggestionAction.CLUSTERING,
            )
        )
        SuggestionCohorteFactory(
            identifiant_action="dag_vide",
            type_action=SuggestionAction.SOURCE_AJOUT,
        )

        cohortes = SuggestionCohorte.objects.source_cohortes()

        assert cohortes.count() == 2
        assert {cohorte.identifiant_action for cohorte in cohortes} == {
            "dag_ajout",
            "dag_modification",
        }

    @pytest.mark.django_db
    def test_logs_queryset_sorted_by_gravity(self):
        cohorte = SuggestionCohorteFactory(type_action=SuggestionAction.SOURCE_AJOUT)
        for niveau in ["ERROR", "WARNING", "WARNING", "INFO"]:
            SuggestionLog.objects.create(
                suggestion_cohorte=cohorte,
                niveau_de_log=niveau,
                fonction_de_transformation="f",
                message=niveau,
            )

        levels = list(cohorte.logs_queryset([]).values_list("niveau_de_log", flat=True))

        assert levels == ["ERROR", "WARNING", "WARNING", "INFO"]

    @pytest.mark.django_db
    def test_logs_queryset_filters_by_level(self):
        cohorte = SuggestionCohorteFactory(type_action=SuggestionAction.SOURCE_AJOUT)
        for niveau in ["ERROR", "WARNING", "WARNING", "INFO"]:
            SuggestionLog.objects.create(
                suggestion_cohorte=cohorte,
                niveau_de_log=niveau,
                fonction_de_transformation="f",
                message=niveau,
            )

        assert cohorte.logs_queryset(["WARNING"]).count() == 2


@pytest.mark.django_db
class TestSuggestionGroupe:
    def test_str_without_acteur_returns_identifiant_action(self):
        cohorte = SuggestionCohorteFactory(identifiant_action="my_action")
        groupe = SuggestionGroupe(suggestion_cohorte=cohorte)

        assert str(groupe) == "my_action"

    def test_str_with_acteur_appends_identifiant_unique(self):
        cohorte = SuggestionCohorteFactory(identifiant_action="my_action")
        acteur = ActeurFactory(identifiant_unique="ID123")
        groupe = SuggestionGroupeFactory(suggestion_cohorte=cohorte, acteur=acteur)

        assert str(groupe) == "my_action - ID123"

    def test_set_lignes_statut_only_updates_ligne_unitaires(
        self, groupe_with_unitaires, user
    ):
        groupe = groupe_with_unitaires
        count = groupe.set_lignes_statut(
            [["latitude", "longitude"]], SuggestionStatut.ATRAITER, user=user
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


@pytest.mark.django_db
class TestSuggestionGroupeSuggestionsCanBeAppliedToParent:
    @pytest.mark.parametrize(
        "type_action",
        [
            SuggestionAction.SOURCE_AJOUT.value,
            SuggestionAction.SOURCE_MODIFICATION.value,
            SuggestionAction.SOURCE_SUPPRESSION.value,
        ],
    )
    def test_returns_true_for_source_action_with_parent_revision_acteur(
        self, type_action
    ):
        parent_revision_acteur = RevisionActeurFactory()
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(type_action=type_action),
            parent_revision_acteur=parent_revision_acteur,
        )

        assert suggestion_groupe.suggestions_can_be_applied_to_parent() is True

    @pytest.mark.parametrize(
        "type_action",
        [
            SuggestionAction.SOURCE_AJOUT.value,
            SuggestionAction.SOURCE_MODIFICATION.value,
            SuggestionAction.SOURCE_SUPPRESSION.value,
        ],
    )
    def test_returns_false_for_source_action_without_parent_revision_acteur(
        self, type_action
    ):
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(type_action=type_action),
            parent_revision_acteur=None,
        )

        assert suggestion_groupe.suggestions_can_be_applied_to_parent() is False

    @pytest.mark.parametrize(
        "type_action",
        [
            SuggestionAction.CLUSTERING.value,
            SuggestionAction.CRAWL_URLS.value,
            SuggestionAction.ENRICH_ACTEURS_CLOSED.value,
            SuggestionAction.ENRICH_ACTEURS_RGPD.value,
            "other_action",
        ],
    )
    def test_returns_false_for_non_source_action_with_parent_revision_acteur(
        self, type_action
    ):
        parent_revision_acteur = RevisionActeurFactory()
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(type_action=type_action),
            parent_revision_acteur=parent_revision_acteur,
        )

        assert suggestion_groupe.suggestions_can_be_applied_to_parent() is False

    @pytest.mark.parametrize(
        "type_action",
        [
            SuggestionAction.CLUSTERING.value,
            SuggestionAction.CRAWL_URLS.value,
            SuggestionAction.ENRICH_ACTEURS_CLOSED.value,
            SuggestionAction.ENRICH_ACTEURS_RGPD.value,
            "other_action",
        ],
    )
    def test_returns_false_for_non_source_action_without_parent_revision_acteur(
        self, type_action
    ):
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(type_action=type_action),
            parent_revision_acteur=None,
        )

        assert suggestion_groupe.suggestions_can_be_applied_to_parent() is False


@pytest.mark.django_db
class TestSuggestionGroupeSuggestionsCanBeAppliedToCorrection:
    @pytest.mark.parametrize(
        "type_action, expected_result",
        [
            (SuggestionAction.SOURCE_AJOUT.value, True),
            (SuggestionAction.SOURCE_MODIFICATION.value, True),
            (SuggestionAction.SOURCE_SUPPRESSION.value, True),
            (SuggestionAction.CLUSTERING.value, False),
            (SuggestionAction.CRAWL_URLS.value, False),
            (SuggestionAction.ENRICH_ACTEURS_CLOSED.value, False),
            (SuggestionAction.ENRICH_ACTEURS_RGPD.value, False),
            ("other_action", False),
        ],
    )
    def test_returns_expected_result_for_type_action(
        self, type_action, expected_result
    ):
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(type_action=type_action),
        )

        assert (
            suggestion_groupe.suggestions_can_be_applied_to_correction()
            is expected_result
        )

    @pytest.mark.parametrize(
        "type_action, expected_result",
        [
            (SuggestionAction.SOURCE_AJOUT.value, True),
            (SuggestionAction.SOURCE_MODIFICATION.value, True),
            (SuggestionAction.SOURCE_SUPPRESSION.value, True),
            (SuggestionAction.CLUSTERING.value, False),
            ("other_action", False),
        ],
    )
    def test_result_is_independent_of_parent_revision_acteur(
        self, type_action, expected_result
    ):
        acteur = ActeurFactory()
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique
        )
        parent_revision_acteur = RevisionActeurFactory()
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(type_action=type_action),
            acteur=acteur,
            revision_acteur=revision_acteur,
            parent_revision_acteur=parent_revision_acteur,
        )

        assert (
            suggestion_groupe.suggestions_can_be_applied_to_correction()
            is expected_result
        )


@pytest.mark.django_db
class TestSuggestionGroupeApply:
    @pytest.fixture
    def suggestion_groupe_source_ajout(self):
        """Fixture for a SuggestionGroupe with type_action SOURCE_AJOUT"""
        from unit_tests.qfdmo.acteur_factory import ActeurTypeFactory, SourceFactory

        # Use a digital acteur_type to avoid the need for location
        ActeurTypeFactory(code="acteur_digital")
        SourceFactory()
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_AJOUT,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom", "identifiant_unique"],
            valeurs=["Nouveau Acteur", "test_acteur_001"],
        )
        return suggestion_groupe

    @pytest.fixture
    def suggestion_groupe_source_modification(self):
        """Fixture pour un SuggestionGroupe avec type_action SOURCE_MODIFICATION"""
        acteur = ActeurFactory(nom="Ancien nom", code_postal="75001")
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION,
            ),
            acteur=acteur,
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom", "code_postal"],
            valeurs=["Nouveau nom", "75002"],
            acteur=acteur,
        )
        return suggestion_groupe

    @pytest.fixture
    def suggestion_groupe_source_modification_with_revision(self):
        """Fixture pour un SuggestionGroupe avec Acteur et RevisionActeur"""
        acteur = ActeurFactory(nom="Ancien nom", code_postal="75001")
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique, nom="Revision nom"
        )
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION,
            ),
            acteur=acteur,
            revision_acteur=revision_acteur,
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom Acteur"],
            acteur=acteur,
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="RevisionActeur",
            champs=["nom"],
            valeurs=["Nouveau nom Revision"],
            revision_acteur=revision_acteur,
        )
        return suggestion_groupe

    def test_apply_raises_error_when_no_acteur_suggestion_unitaires(self):
        """
        Test that apply() raises an error if there are no Acteur suggestion unitaires
        """
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_AJOUT,
            ),
        )
        # No SuggestionUnitary with suggestion_modele="Acteur"

        with pytest.raises(ValueError, match="No acteur suggestion unitaires found"):
            suggestion_groupe.apply()

    def test_apply_source_modification_with_revision_creates_revision(
        self, suggestion_groupe_source_modification_with_revision
    ):
        """Test that apply() creates/updates a RevisionActeur for SOURCE_MODIFICATION"""
        acteur = suggestion_groupe_source_modification_with_revision.acteur
        revision_acteur = (
            suggestion_groupe_source_modification_with_revision.revision_acteur
        )

        assert acteur.nom == "Ancien nom"
        assert revision_acteur.nom == "Revision nom"

        suggestion_groupe_source_modification_with_revision.apply()

        # Verify that the Acteur has been updated
        acteur.refresh_from_db()
        assert acteur.nom == "Nouveau nom Acteur"

        # Verify that the RevisionActeur has been updated
        revision_acteur.refresh_from_db()
        assert revision_acteur.nom == "Nouveau nom Revision"

    def test_apply_does_nothing_for_non_source_actions(self):
        """Test that apply() does nothing for actions that are not SOURCE_*"""
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.CLUSTERING,
            ),
        )

        # apply() should not raise an error but do nothing
        suggestion_groupe.apply()
