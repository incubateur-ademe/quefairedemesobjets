import pytest
from data.admin import (
    HasSuggestionUnitaireWithChampField,
    SuggestionGroupeAdmin,
    apply_suggestions_to_correction,
    apply_suggestions_to_parent,
)
from data.models.suggestion import (
    SuggestionAction,
    SuggestionGroupe,
    SuggestionUnitaire,
)
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from djangoql.exceptions import DjangoQLSchemaError
from unit_tests.data.models.suggestion_factory import (
    SuggestionCohorteFactory,
    SuggestionGroupeFactory,
    SuggestionUnitaireFactory,
)
from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory

NON_SOURCE_TYPE_ACTIONS = [
    SuggestionAction.CLUSTERING.value,
    SuggestionAction.CRAWL_URLS.value,
    SuggestionAction.ENRICH_ACTEURS_CLOSED.value,
    SuggestionAction.ENRICH_ACTEURS_RGPD.value,
    SuggestionAction.ENRICH_ACTEURS_VILLES_TYPO.value,
    SuggestionAction.ENRICH_ACTEURS_VILLES_NEW.value,
    SuggestionAction.ENRICH_ACTEURS_CP_TYPO.value,
    SuggestionAction.ENRICH_REVISION_ACTEURS_CP_TYPO.value,
    "",
]

SOURCE_TYPE_ACTIONS = [
    SuggestionAction.SOURCE_AJOUT.value,
    SuggestionAction.SOURCE_MODIFICATION.value,
    SuggestionAction.SOURCE_SUPPRESSION.value,
]


@pytest.fixture
def admin_instance():
    """Create a SuggestionGroupeAdmin instance"""
    site = AdminSite()
    return SuggestionGroupeAdmin(SuggestionGroupeFactory._meta.model, site)


@pytest.fixture
def request_factory():
    """Factory to create HTTP requests"""
    return RequestFactory()


@pytest.fixture
def mock_request(request_factory):
    """Create a HTTP request mock with message support"""
    request = request_factory.get("/admin/")
    request.user = AnonymousUser()
    setattr(request, "session", "session")
    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)
    return request


@pytest.mark.django_db
class TestApplySuggestionsToParent:
    """Tests for apply_suggestions_to_parent admin action"""

    @pytest.mark.parametrize("type_action", SOURCE_TYPE_ACTIONS)
    def test_creates_one_parent_suggestion_per_acteur_suggestion(
        self, admin_instance, mock_request, type_action
    ):
        """Each Acteur suggestion produces a ParentRevisionActeur suggestion"""
        acteur = ActeurFactory()
        parent = RevisionActeurFactory()
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            parent_revision_acteur=parent,
            suggestion_cohorte=SuggestionCohorteFactory(type_action=type_action),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            acteur=acteur,
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            acteur=acteur,
            champs=["latitude", "longitude"],
            valeurs=["48.56789", "2.56789"],
        )

        queryset = SuggestionGroupe.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_parent(admin_instance, mock_request, queryset)

        parent_suggestions = suggestion_groupe.suggestion_unitaires.filter(
            suggestion_modele="ParentRevisionActeur"
        )
        assert parent_suggestions.count() == 2

        su_nom = parent_suggestions.get(champs=["nom"])
        assert su_nom.valeurs == ["Nouveau nom"]
        assert su_nom.parent_revision_acteur == parent

        su_location = parent_suggestions.get(champs=["latitude", "longitude"])
        assert su_location.valeurs == ["48.56789", "2.56789"]
        assert su_location.parent_revision_acteur == parent

    def test_updates_existing_parent_suggestion_with_matching_champs(
        self, admin_instance, mock_request
    ):
        """An existing matching ParentRevisionActeur is updated, not duplicated"""
        acteur = ActeurFactory()
        parent = RevisionActeurFactory()
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            parent_revision_acteur=parent,
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )
        existing = SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="ParentRevisionActeur",
            parent_revision_acteur=parent,
            champs=["nom"],
            valeurs=["Ancienne valeur"],
        )

        queryset = SuggestionGroupe.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_parent(admin_instance, mock_request, queryset)

        existing.refresh_from_db()
        assert existing.valeurs == ["Nouveau nom"]
        assert existing.parent_revision_acteur == parent
        assert (
            suggestion_groupe.suggestion_unitaires.filter(
                suggestion_modele="ParentRevisionActeur", champs=["nom"]
            ).count()
            == 1
        )

    def test_creates_new_suggestion_when_existing_has_different_champs(
        self, admin_instance, mock_request
    ):
        """A ParentRevisionActeur with different champs is left untouched"""
        acteur = ActeurFactory()
        parent = RevisionActeurFactory()
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            parent_revision_acteur=parent,
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )
        unrelated = SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="ParentRevisionActeur",
            parent_revision_acteur=parent,
            champs=["telephone"],
            valeurs=["0123456789"],
        )

        queryset = SuggestionGroupe.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_parent(admin_instance, mock_request, queryset)

        unrelated.refresh_from_db()
        assert unrelated.valeurs == ["0123456789"]
        assert (
            suggestion_groupe.suggestion_unitaires.filter(
                suggestion_modele="ParentRevisionActeur"
            ).count()
            == 2
        )

    def test_preserves_original_acteur_suggestion(self, admin_instance, mock_request):
        """The original Acteur suggestion is preserved in DB after the action"""
        acteur = ActeurFactory()
        parent = RevisionActeurFactory()
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            parent_revision_acteur=parent,
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        acteur_su = SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )

        queryset = SuggestionGroupe.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_parent(admin_instance, mock_request, queryset)

        assert SuggestionUnitaire.objects.filter(
            id=acteur_su.id, suggestion_modele="Acteur"
        ).exists()

    def test_does_nothing_when_parent_revision_acteur_is_missing(
        self, admin_instance, mock_request
    ):
        """No ParentRevisionActeur suggestion is created without parent"""
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=ActeurFactory(),
            parent_revision_acteur=None,
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )

        queryset = SuggestionGroupe.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_parent(admin_instance, mock_request, queryset)

        assert not suggestion_groupe.suggestion_unitaires.filter(
            suggestion_modele="ParentRevisionActeur"
        ).exists()

    @pytest.mark.parametrize("type_action", NON_SOURCE_TYPE_ACTIONS)
    def test_does_nothing_when_type_action_is_not_source(
        self, admin_instance, mock_request, type_action
    ):
        """No suggestion is created when type_action is not a SOURCE_* one"""
        acteur = ActeurFactory()
        parent = RevisionActeurFactory()
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            parent_revision_acteur=parent,
            suggestion_cohorte=SuggestionCohorteFactory(type_action=type_action),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )

        queryset = SuggestionGroupe.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_parent(admin_instance, mock_request, queryset)

        assert not suggestion_groupe.suggestion_unitaires.filter(
            suggestion_modele="ParentRevisionActeur"
        ).exists()

    def test_ignores_non_acteur_suggestions_as_source(
        self, admin_instance, mock_request
    ):
        """Only Acteur suggestions are used as source for copy"""
        acteur = ActeurFactory()
        parent = RevisionActeurFactory()
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            parent_revision_acteur=parent,
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="RevisionActeur",
            revision_acteur=acteur.get_or_create_revision(),
            champs=["nom"],
            valeurs=["Valeur revision"],
        )

        queryset = SuggestionGroupe.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_parent(admin_instance, mock_request, queryset)

        assert not suggestion_groupe.suggestion_unitaires.filter(
            suggestion_modele="ParentRevisionActeur"
        ).exists()

    def test_processes_each_suggestion_groupe_in_queryset(
        self, admin_instance, mock_request
    ):
        """All eligible SuggestionGroupe in the queryset are processed"""
        sg1 = SuggestionGroupeFactory(
            acteur=ActeurFactory(),
            parent_revision_acteur=RevisionActeurFactory(),
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        sg2 = SuggestionGroupeFactory(
            acteur=ActeurFactory(),
            parent_revision_acteur=RevisionActeurFactory(),
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=sg1,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nom 1"],
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=sg2,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nom 2"],
        )

        queryset = SuggestionGroupe.objects.filter(id__in=[sg1.id, sg2.id])
        apply_suggestions_to_parent(admin_instance, mock_request, queryset)

        assert (
            sg1.suggestion_unitaires.filter(
                suggestion_modele="ParentRevisionActeur"
            ).count()
            == 1
        )
        assert (
            sg2.suggestion_unitaires.filter(
                suggestion_modele="ParentRevisionActeur"
            ).count()
            == 1
        )

    def test_processes_only_eligible_suggestion_groupe_in_mixed_queryset(
        self, admin_instance, mock_request
    ):
        """Only suggestion groupes with parent and SOURCE_* type are processed"""
        eligible = SuggestionGroupeFactory(
            acteur=ActeurFactory(),
            parent_revision_acteur=RevisionActeurFactory(),
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        without_parent = SuggestionGroupeFactory(
            acteur=ActeurFactory(),
            parent_revision_acteur=None,
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=eligible,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Eligible"],
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=without_parent,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Skipped"],
        )

        queryset = SuggestionGroupe.objects.filter(
            id__in=[eligible.id, without_parent.id]
        )
        apply_suggestions_to_parent(admin_instance, mock_request, queryset)

        assert eligible.suggestion_unitaires.filter(
            suggestion_modele="ParentRevisionActeur"
        ).exists()
        assert not without_parent.suggestion_unitaires.filter(
            suggestion_modele="ParentRevisionActeur"
        ).exists()


@pytest.mark.django_db
class TestApplySuggestionsToRevision:
    """Tests for apply_suggestions_to_correction admin action"""

    @pytest.mark.parametrize("type_action", SOURCE_TYPE_ACTIONS)
    def test_creates_one_revision_suggestion_per_acteur_suggestion(
        self, admin_instance, mock_request, type_action
    ):
        """Each Acteur suggestion produces a RevisionActeur suggestion"""
        acteur = ActeurFactory()
        revision_acteur = acteur.get_or_create_revision()
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=revision_acteur,
            suggestion_cohorte=SuggestionCohorteFactory(type_action=type_action),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["latitude", "longitude"],
            valeurs=["48.56789", "2.56789"],
        )

        queryset = SuggestionGroupe.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_correction(admin_instance, mock_request, queryset)

        revision_suggestions = suggestion_groupe.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur"
        )
        assert revision_suggestions.count() == 2

        su_nom = revision_suggestions.get(champs=["nom"])
        assert su_nom.valeurs == ["Nouveau nom"]
        assert su_nom.revision_acteur == revision_acteur

        su_location = revision_suggestions.get(champs=["latitude", "longitude"])
        assert su_location.valeurs == ["48.56789", "2.56789"]
        assert su_location.revision_acteur == revision_acteur

    def test_updates_existing_revision_suggestion_with_matching_champs(
        self, admin_instance, mock_request
    ):
        """An existing matching RevisionActeur is updated, not duplicated"""
        acteur = ActeurFactory()
        revision_acteur = acteur.get_or_create_revision()
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=revision_acteur,
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )
        existing = SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="RevisionActeur",
            revision_acteur=revision_acteur,
            champs=["nom"],
            valeurs=["Ancienne valeur"],
        )

        queryset = SuggestionGroupe.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_correction(admin_instance, mock_request, queryset)

        existing.refresh_from_db()
        assert existing.valeurs == ["Nouveau nom"]
        assert existing.revision_acteur == revision_acteur
        assert (
            suggestion_groupe.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur", champs=["nom"]
            ).count()
            == 1
        )

    def test_creates_new_suggestion_when_existing_has_different_champs(
        self, admin_instance, mock_request
    ):
        """A RevisionActeur with different champs is left untouched"""
        acteur = ActeurFactory()
        revision_acteur = acteur.get_or_create_revision()
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=revision_acteur,
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )
        unrelated = SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="RevisionActeur",
            revision_acteur=revision_acteur,
            champs=["telephone"],
            valeurs=["0123456789"],
        )

        queryset = SuggestionGroupe.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_correction(admin_instance, mock_request, queryset)

        unrelated.refresh_from_db()
        assert unrelated.valeurs == ["0123456789"]
        assert (
            suggestion_groupe.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur"
            ).count()
            == 2
        )

    def test_preserves_original_acteur_suggestion(self, admin_instance, mock_request):
        """The original Acteur suggestion is preserved in DB after the action"""
        acteur = ActeurFactory()
        revision_acteur = acteur.get_or_create_revision()
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=revision_acteur,
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        acteur_su = SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )

        queryset = SuggestionGroupe.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_correction(admin_instance, mock_request, queryset)

        assert SuggestionUnitaire.objects.filter(
            id=acteur_su.id, suggestion_modele="Acteur"
        ).exists()

    def test_falls_back_to_acteur_id_when_no_revision_acteur(
        self, admin_instance, mock_request
    ):
        """Without revision_acteur, revision_acteur_id falls back to acteur_id"""
        acteur = ActeurFactory()
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=None,
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )

        queryset = SuggestionGroupe.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_correction(admin_instance, mock_request, queryset)

        revision_suggestion = suggestion_groupe.suggestion_unitaires.get(
            suggestion_modele="RevisionActeur"
        )
        assert revision_suggestion.revision_acteur_id == acteur.pk
        assert revision_suggestion.valeurs == ["Nouveau nom"]

    @pytest.mark.parametrize("type_action", NON_SOURCE_TYPE_ACTIONS)
    def test_does_nothing_when_type_action_is_not_source(
        self, admin_instance, mock_request, type_action
    ):
        """No suggestion is created when type_action is not a SOURCE_* one"""
        acteur = ActeurFactory()
        revision_acteur = acteur.get_or_create_revision()
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=revision_acteur,
            suggestion_cohorte=SuggestionCohorteFactory(type_action=type_action),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )

        queryset = SuggestionGroupe.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_correction(admin_instance, mock_request, queryset)

        assert not suggestion_groupe.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur"
        ).exists()

    def test_ignores_non_acteur_suggestions_as_source(
        self, admin_instance, mock_request
    ):
        """Only Acteur suggestions are used as source for copy"""
        acteur = ActeurFactory()
        parent = RevisionActeurFactory()
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=acteur.get_or_create_revision(),
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="ParentRevisionActeur",
            parent_revision_acteur=parent,
            champs=["nom"],
            valeurs=["Valeur parent"],
        )

        queryset = SuggestionGroupe.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_correction(admin_instance, mock_request, queryset)

        assert not suggestion_groupe.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur"
        ).exists()

    def test_processes_each_suggestion_groupe_in_queryset(
        self, admin_instance, mock_request
    ):
        """All eligible SuggestionGroupe in the queryset are processed"""
        acteur1 = ActeurFactory()
        acteur2 = ActeurFactory()
        sg1 = SuggestionGroupeFactory(
            acteur=acteur1,
            revision_acteur=acteur1.get_or_create_revision(),
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        sg2 = SuggestionGroupeFactory(
            acteur=acteur2,
            revision_acteur=acteur2.get_or_create_revision(),
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=sg1,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nom 1"],
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=sg2,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nom 2"],
        )

        queryset = SuggestionGroupe.objects.filter(id__in=[sg1.id, sg2.id])
        apply_suggestions_to_correction(admin_instance, mock_request, queryset)

        assert (
            sg1.suggestion_unitaires.filter(suggestion_modele="RevisionActeur").count()
            == 1
        )
        assert (
            sg2.suggestion_unitaires.filter(suggestion_modele="RevisionActeur").count()
            == 1
        )

    def test_processes_only_eligible_suggestion_groupe_in_mixed_queryset(
        self, admin_instance, mock_request
    ):
        """Only suggestion groupes with SOURCE_* type are processed"""
        acteur_eligible = ActeurFactory()
        acteur_skipped = ActeurFactory()
        eligible = SuggestionGroupeFactory(
            acteur=acteur_eligible,
            revision_acteur=acteur_eligible.get_or_create_revision(),
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION.value,
            ),
        )
        skipped = SuggestionGroupeFactory(
            acteur=acteur_skipped,
            revision_acteur=acteur_skipped.get_or_create_revision(),
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.CLUSTERING.value,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=eligible,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Eligible"],
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=skipped,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Skipped"],
        )

        queryset = SuggestionGroupe.objects.filter(id__in=[eligible.id, skipped.id])
        apply_suggestions_to_correction(admin_instance, mock_request, queryset)

        assert eligible.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur"
        ).exists()
        assert not skipped.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur"
        ).exists()


@pytest.mark.django_db
class TestSuggestionGroupeAdminBooleanFilters:
    def test_schema_exposes_has_parent_and_has_correction_fields(self, admin_instance):
        schema = admin_instance.djangoql_schema(SuggestionGroupe)

        field_names = [
            field if isinstance(field, str) else field.name
            for field in schema.get_fields(SuggestionGroupe)
        ]

        assert "has_parent" in field_names
        assert "has_correction" in field_names

    def test_get_queryset_annotates_has_parent_and_has_correction(
        self, admin_instance, mock_request
    ):
        group_with_parent = SuggestionGroupeFactory(
            acteur=ActeurFactory(),
            parent_revision_acteur=RevisionActeurFactory(),
        )
        group_with_correction = SuggestionGroupeFactory(
            acteur=ActeurFactory(),
            revision_acteur=RevisionActeurFactory(),
        )
        SuggestionGroupeFactory(
            acteur=ActeurFactory(),
        )

        queryset = admin_instance.get_queryset(mock_request)

        has_parent_ids = set(
            queryset.filter(has_parent=True).values_list("id", flat=True)
        )
        has_correction_ids = set(
            queryset.filter(has_correction=True).values_list("id", flat=True)
        )

        assert has_parent_ids == {group_with_parent.id}
        assert has_correction_ids == {group_with_correction.id}


@pytest.mark.django_db
class TestHasSuggestionUnitaireWithChampField:
    def test_contains_operator_matches_partial_champ(self):
        matching_group = SuggestionGroupeFactory()
        non_matching_group = SuggestionGroupeFactory()

        SuggestionUnitaireFactory(
            suggestion_groupe=matching_group,
            champs=["nom", "telephone"],
            valeurs=["Nom", "0123456789"],
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=matching_group,
            champs=["field"],
            valeurs=["fake"],
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=non_matching_group,
            champs=["adresse"],
            valeurs=["1 rue de Paris"],
        )

        lookup = HasSuggestionUnitaireWithChampField().get_lookup([], "~", "tele")

        result_ids = set(
            SuggestionGroupe.objects.filter(lookup).values_list("id", flat=True)
        )

        assert result_ids == {matching_group.id}

    def test_does_not_contain_operator_excludes_groups_with_any_matching_unitaire(
        self,
    ):
        matching_group = SuggestionGroupeFactory()
        non_matching_group = SuggestionGroupeFactory()

        SuggestionUnitaireFactory(
            suggestion_groupe=matching_group,
            champs=["nom", "telephone"],
            valeurs=["Nom", "0123456789"],
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=matching_group,
            champs=["field"],
            valeurs=["fake"],
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=non_matching_group,
            champs=["adresse"],
            valeurs=["1 rue de Paris"],
        )

        lookup = HasSuggestionUnitaireWithChampField().get_lookup([], "!~", "tele")

        result_ids = set(
            SuggestionGroupe.objects.filter(lookup).values_list("id", flat=True)
        )

        assert result_ids == {non_matching_group.id}

    def test_only_contains_operators_are_allowed(self):
        with pytest.raises(
            DjangoQLSchemaError, match='only supports "~" and "!~" operators'
        ):
            HasSuggestionUnitaireWithChampField().get_lookup([], "=", "nom")
