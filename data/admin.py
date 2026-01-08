import logging

from django.contrib import admin, messages
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.template.loader import render_to_string
from django.utils.html import format_html
from djangoql.admin import DjangoQLSearchMixin
from djangoql.schema import BoolField, DjangoQLSchema, IntField, StrField

from core.admin import NotEditableMixin, NotSelfDeletableMixin
from data.models.suggestion import (
    Suggestion,
    SuggestionCohorte,
    SuggestionGroupe,
    SuggestionLog,
    SuggestionStatut,
    SuggestionUnitaire,
)
from data.views import serialize_suggestion_groupe

NB_SUGGESTIONS_DISPLAYED_WHEN_DELETING = 100

logger = logging.getLogger(__name__)


def dict_to_html_table(data: dict):
    table = "<table class'table-metadata'>"
    for key in sorted(data.keys()):
        if isinstance(data[key], dict):
            value = dict_to_html_table(data[key])
        elif isinstance(data[key], list):
            value = "</td><td>".join([str(item) for item in data[key]])
        else:
            value = data[key]
        table += f"<tr><td>{key}</td><td>{value}</td></tr>"
    table += "</table>"
    return table


class SuggestionLogInline(admin.TabularInline):
    model = SuggestionLog
    fields = (
        "identifiant_unique",
        "niveau_de_log",
        "fonction_de_transformation",
        "origine_colonnes",
        "origine_valeurs",
        "destination_colonnes",
        "message",
    )
    extra = 0
    can_delete = False
    can_add = False
    can_change = False
    can_view = True


class SuggestionQLSchemaMixin(DjangoQLSchema):
    """Force JSON fields to be string fields for text search"""

    def get_fields(self, model):
        """Override to force JSON fields as string fields for text search."""
        fields = super().get_fields(model)
        result = []
        for field in fields:
            # Get field name (field can be a string or a Field object)
            field_name = field if isinstance(field, str) else field.name

            # Check if the field is a JSONField in the model
            model_field = model._meta.get_field(field_name)
            if model_field and (
                isinstance(model_field, models.JSONField)
                or isinstance(model_field, ArrayField)
            ):
                field = StrField(name=field_name)
            result.append(field)
        return result


class SuggestionCohorteAdmin(DjangoQLSearchMixin, NotEditableMixin, admin.ModelAdmin):
    class SuggestionCohorteQLSchema(SuggestionQLSchemaMixin):
        pass

    djangoql_completion_enabled_by_default = True
    djangoql_schema = SuggestionCohorteQLSchema

    list_display = [
        "__str__",
        "statut",
        "metadonnees",
    ]

    search_fields = ["id", "metadata", "identifiant_action", "identifiant_execution"]
    list_filter = [
        ("statut", admin.ChoicesFieldListFilter),
        ("type_action", admin.ChoicesFieldListFilter),
    ]
    inlines = [SuggestionLogInline]

    def metadonnees(self, obj):
        return format_html(dict_to_html_table(obj.metadata or {}))

    def get_deleted_objects(self, objs, request):
        """
        Override the Objetcs to delete while removing a SuggestionCohorte because
        in some cases, the list is huge and it is not possible to display it.
        """
        (deletable_objects, model_count, perms_needed, protected) = (
            super().get_deleted_objects(objs, request)
        )
        display_warning = False
        display_deletable_objects = []
        for obj in deletable_objects:
            if (
                isinstance(obj, list | tuple)
                and len(obj) > NB_SUGGESTIONS_DISPLAYED_WHEN_DELETING
            ):
                obj = obj[:NB_SUGGESTIONS_DISPLAYED_WHEN_DELETING]
                display_warning = True
            display_deletable_objects.append(obj)
        if display_warning:
            messages.warning(
                request,
                "Attention : la suppression de cette cohorte entraînera également "
                "la suppression de nombreuses suggestions associées. "
                "Celle-ci ne sont pas toutes listées ici.",
            )

        return display_deletable_objects, model_count, perms_needed, protected


def _manage_suggestion_cohorte_statut(cohorte_ids: list[int]):
    for suggestion_cohorte in SuggestionCohorte.objects.filter(id__in=cohorte_ids):
        # On vérifie si toutes les suggestions de la cohorte sont rejetées
        if Suggestion.objects.filter(
            suggestion_cohorte=suggestion_cohorte,
            statut=SuggestionStatut.AVALIDER,
        ).exists():
            suggestion_cohorte.statut = SuggestionStatut.ENCOURS
        else:
            suggestion_cohorte.statut = SuggestionStatut.SUCCES
        suggestion_cohorte.save()


@admin.action(description="REJETER les suggestions selectionnées")
def mark_as_rejected(self, request, queryset):
    distinct_suggestion_cohorte_ids = queryset.values_list(
        "suggestion_cohorte_id", flat=True
    )
    distinct_suggestion_cohorte_ids = list(set(distinct_suggestion_cohorte_ids))
    queryset.update(statut=SuggestionStatut.REJETEE)
    _manage_suggestion_cohorte_statut(distinct_suggestion_cohorte_ids)
    self.message_user(
        request, f"Les {queryset.count()} suggestions sélectionnées ont été refusées"
    )


@admin.action(description="VALIDER les suggestions selectionnées")
def mark_as_toproceed(self, request, queryset):
    distinct_suggestion_cohorte_ids = queryset.values_list(
        "suggestion_cohorte_id", flat=True
    )
    distinct_suggestion_cohorte_ids = list(set(distinct_suggestion_cohorte_ids))
    queryset.update(statut=SuggestionStatut.ATRAITER)
    _manage_suggestion_cohorte_statut(distinct_suggestion_cohorte_ids)
    self.message_user(
        request,
        f"Les {queryset.count()} suggestions sélectionnées ont été mises à jour"
        " avec le statut «À traiter»",
    )


class SuggestionAdmin(DjangoQLSearchMixin, NotSelfDeletableMixin):
    class SuggestionQLSchema(SuggestionQLSchemaMixin):
        pass

    djangoql_completion_enabled_by_default = True
    djangoql_schema = SuggestionQLSchema

    class SuggestionCohorteFilter(admin.RelatedFieldListFilter):
        def field_choices(self, field, request, model_admin):
            # Filtrer uniquement les cohortes qui ont des suggestions
            cohorte_model = field.related_model
            cohortes_avec_suggestions = (
                cohorte_model.objects.filter(suggestions__isnull=False)
                .distinct()
                .order_by("-cree_le")
            )
            return [(cohorte.pk, str(cohorte)) for cohorte in cohortes_avec_suggestions]

    search_fields = ["id", "contexte", "suggestion", "metadata"]
    list_display = [
        "id",
        "cohorte",
        "enrich_statut",
        "donnees_initiales",
        "changements_suggeres",
    ]
    readonly_fields = ["cree_le", "modifie_le"]
    list_filter = [
        ("statut", admin.ChoicesFieldListFilter),
        ("suggestion_cohorte", SuggestionCohorteFilter),
    ]
    actions = [mark_as_rejected, mark_as_toproceed]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("suggestion_cohorte")

    def cohorte(self, obj):
        coh = obj.suggestion_cohorte
        return format_html(str(coh).replace(" -- ", "<br/>"))

    def acteur_link_html(self, id):
        return format_html(
            '<a target="_blank" href="/admin/qfdmo/displayedacteur/{}/change/">{}</a>',
            id,
            id,
        )

    def changements_suggeres(self, obj):
        return obj.display_suggestion_details

    def donnees_initiales(self, obj):
        return obj.display_contexte_details

    def enrich_statut(self, obj):
        if (
            obj.statut == SuggestionStatut.ERREUR
            and obj.metadata
            and "error" in obj.metadata
        ):
            return format_html(
                '<span style="color: red;">{}</span><br>{}',
                obj.get_statut_display(),
                obj.metadata["error"],
            )
        return obj.get_statut_display()


class SuggestionUnitaireInline(admin.TabularInline):
    model = SuggestionUnitaire
    extra = 0
    can_delete = False
    can_add = False
    can_change = False
    can_view = True


def _update_or_copy_suggestion_unitaires(suggestion_groupe):
    revision = suggestion_groupe.revision_acteur
    suggestion_unitaires = suggestion_groupe.suggestion_unitaires.all()
    # get all SuggestionUnitaire for the SuggestionGroupe using the Acteur model
    suggestion_unitaires_acteur = [
        suggestion_unitaire
        for suggestion_unitaire in suggestion_unitaires
        if suggestion_unitaire.suggestion_modele == "Acteur"
    ]
    # for each SuggestionUnitaire for the Acteur model,
    # we check if there is a SuggestionUnitaire for the RevisionActeur model
    # with the same champs and the same values
    # Then we update or create the SuggestionUnitaire for the RevisionActeur
    for suggestion_unitaire_acteur in suggestion_unitaires_acteur:
        # get the SuggestionUnitaire for the RevisionActeur model
        # with the same champs and the same values if exists
        suggestion_unitaire_revision = next(
            (
                su
                for su in suggestion_unitaires
                if su.suggestion_modele == "RevisionActeur"
                and su.revision_acteur == revision
                and su.champs == suggestion_unitaire_acteur.champs
            ),
            None,
        )
        if suggestion_unitaire_revision:
            # if exists, we update the SuggestionUnitaire
            suggestion_unitaire_revision.valeurs = suggestion_unitaire_acteur.valeurs
        else:
            # if not exists, we create the SuggestionUnitaire
            suggestion_unitaire_revision = suggestion_unitaire_acteur
            suggestion_unitaire_revision.id = None
            suggestion_unitaire_revision.revision_acteur = revision
            suggestion_unitaire_revision.suggestion_modele = "RevisionActeur"
        suggestion_unitaire_revision.save()


@admin.action(description="Appliquer les suggestions au parent")
def apply_suggestions_to_parent(self, request, queryset):
    for suggestion_groupe in queryset:
        # Only for SuggestionGroupe with parent
        if (
            suggestion_groupe.revision_acteur_id
            and suggestion_groupe.acteur_id != suggestion_groupe.revision_acteur_id
        ):
            _update_or_copy_suggestion_unitaires(suggestion_groupe)

    self.message_user(
        request, f"Les {queryset.count()} suggestions sélectionnées ont été appliquées"
    )


@admin.action(description="Appliquer les suggestions au correction de l'acteur")
def apply_suggestions_to_revision(self, request, queryset):
    for suggestion_groupe in queryset:
        # Only for SuggestionGroupe with parent
        if (
            suggestion_groupe.revision_acteur_id
            and suggestion_groupe.acteur_id == suggestion_groupe.revision_acteur_id
        ):
            _update_or_copy_suggestion_unitaires(suggestion_groupe)

    self.message_user(
        request, f"Les {queryset.count()} suggestions sélectionnées ont été appliquées"
    )


@admin.register(SuggestionGroupe)
class SuggestionGroupeAdmin(
    DjangoQLSearchMixin, NotEditableMixin, NotSelfDeletableMixin
):
    actions = [
        mark_as_rejected,
        mark_as_toproceed,
        apply_suggestions_to_parent,
        apply_suggestions_to_revision,
    ]

    class SuggestionGroupeQLSchema(SuggestionQLSchemaMixin):
        def get_fields(self, model):
            """Override to expose relations and custom fields."""
            fields = super().get_fields(model)

            # Works with with_suggestion_unitaire_count set in get_queryset
            if model == SuggestionGroupe:
                return (
                    [
                        field
                        for field in fields
                        if field not in ["suggestion_unitaires_count"]
                    ]
                    + [IntField(name="suggestion_unitaires_count")]
                    + [BoolField(name="has_parent")]
                )

            return fields

    djangoql_completion_enabled_by_default = True
    djangoql_schema = SuggestionGroupeQLSchema

    class SuggestionCohorteFilter(admin.RelatedFieldListFilter):
        def field_choices(self, field, request, model_admin):
            # Filtrer uniquement les cohortes qui ont des suggestions
            cohorte_model = field.related_model
            cohortes_avec_suggestions = (
                cohorte_model.objects.filter(suggestion_groupes__isnull=False)
                .distinct()
                .order_by("-cree_le")
            )
            return [(cohorte.pk, str(cohorte)) for cohorte in cohortes_avec_suggestions]

    search_fields = ["id", "contexte", "metadata"]
    list_display = [
        "groupe_de_suggestions",
    ]
    list_display_links = None
    readonly_fields = ["cree_le", "modifie_le"]
    inlines = [SuggestionUnitaireInline]
    list_filter = [
        ("statut", admin.ChoicesFieldListFilter),
        ("suggestion_cohorte", SuggestionCohorteFilter),
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return (
            queryset.prefetch_related(
                "suggestion_unitaires",
                "acteur",
                "revision_acteur",
            )
            .with_suggestion_unitaire_count()
            .with_has_parent()
        )

    def groupe_de_suggestions(self, obj):
        template_name = "data/_partials/suggestion_groupe_details.html"
        return render_to_string(template_name, serialize_suggestion_groupe(obj))


@admin.register(SuggestionUnitaire)
class SuggestionUnitaireAdmin(
    DjangoQLSearchMixin,
    NotEditableMixin,
    NotSelfDeletableMixin,
):
    class SuggestionUnitaireQLSchema(SuggestionQLSchemaMixin):
        pass

    djangoql_completion_enabled_by_default = True
    djangoql_schema = SuggestionUnitaireQLSchema

    class SuggestionCohorteFilter(admin.RelatedFieldListFilter):
        def field_choices(self, field, request, model_admin):
            return field.get_choices(include_blank=False, ordering=("-cree_le",))

    list_display = [
        "suggestion_groupe",
        "suggestion_groupe__suggestion_cohorte",
        "statut",
        "acteur",
        "revision_acteur",
        "ordre",
        "raison",
        "parametres",
        "suggestion_modele",
        "champs",
        "valeurs",
    ]

    search_fields = [
        "id",
        "raison",
        "parametres",
        "suggestion_modele",
        "champs",
        "valeurs",
    ]
    readonly_fields = ["cree_le", "modifie_le"]
    list_filter = [
        ("statut", admin.ChoicesFieldListFilter),
        ("suggestion_groupe__suggestion_cohorte", SuggestionCohorteFilter),
    ]


admin.site.register(SuggestionCohorte, SuggestionCohorteAdmin)
admin.site.register(Suggestion, SuggestionAdmin)
