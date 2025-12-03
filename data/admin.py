import logging

from django.contrib import admin, messages
from django.db.models import Count
from django.template.loader import render_to_string
from django.utils.html import format_html
from djangoql.admin import DjangoQLSearchMixin
from djangoql.schema import DjangoQLSchema, IntField, StrField

from core.admin import NotEditableMixin, NotSelfDeletableMixin, QuerysetFilterAdmin
from data.models.suggestion import (
    Suggestion,
    SuggestionCohorte,
    SuggestionGroupe,
    SuggestionLog,
    SuggestionStatut,
    SuggestionUnitaire,
)

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


class SuggestionCohorteAdmin(DjangoQLSearchMixin, NotEditableMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = [
        "__str__",
        "statut",
        "metadonnees",
    ]

    search_fields = ["metadata", "identifiant_action", "identifiant_execution"]
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


class SuggestionAdmin(NotSelfDeletableMixin, QuerysetFilterAdmin):
    class SuggestionCohorteFilter(admin.RelatedFieldListFilter):
        def field_choices(self, field, request, model_admin):
            return field.get_choices(include_blank=False, ordering=("-cree_le",))

    search_fields = ["contexte", "suggestion", "metadata"]
    list_display = [
        "id",
        "cohorte",
        "enrich_statut",
        "donnees_initiales",
        "changements_suggeres",
    ]
    readonly_fields = ["cree_le", "modifie_le"]
    list_filter = [
        ("suggestion_cohorte", SuggestionCohorteFilter),
        ("statut", admin.ChoicesFieldListFilter),
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
    # fields = ("statut", "acteur", "revision_acteur", "contexte", "metadata")
    extra = 0
    can_delete = False
    can_add = False
    can_change = False
    can_view = True


@admin.register(SuggestionGroupe)
class SuggestionGroupeAdmin(
    DjangoQLSearchMixin, NotEditableMixin, NotSelfDeletableMixin, QuerysetFilterAdmin
):
    actions = [mark_as_rejected, mark_as_toproceed]

    class SuggestionGroupeQLSchema(DjangoQLSchema):
        def get_fields(self, model):
            """Surcharge pour exposer les relations et champs personnalisés."""
            fields = super().get_fields(model)

            if model == SuggestionGroupe:
                return [
                    field
                    for field in fields
                    if field not in ["suggestion_unitaires_count"]
                ] + [IntField(name="suggestion_unitaires_count")]

            # Force string field for champs and valeurs in SuggestionUnitaire
            if model == SuggestionUnitaire:
                return [
                    field for field in fields if field not in ["champs", "valeurs"]
                ] + [StrField(name="champs"), StrField(name="valeurs")]
            return fields

    djangoql_completion_enabled_by_default = True
    djangoql_schema = SuggestionGroupeQLSchema

    class SuggestionCohorteFilter(admin.RelatedFieldListFilter):
        def field_choices(self, field, request, model_admin):
            return field.get_choices(include_blank=False, ordering=("-cree_le",))

    search_fields = ["contexte", "metadata"]
    list_display = [
        "groupe_de_suggestions",
    ]
    list_display_links = None
    readonly_fields = ["cree_le", "modifie_le"]
    inlines = [SuggestionUnitaireInline]
    list_filter = [
        ("suggestion_cohorte", SuggestionCohorteFilter),
        ("statut", admin.ChoicesFieldListFilter),
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related(
            "suggestion_unitaires",
            "acteur",
            "revision_acteur",
            "revision_acteur__parent",
        ).annotate(suggestion_unitaires_count=Count("suggestion_unitaires"))

    def changelist_view(self, request, extra_context=None):
        self.csrf_token = request.META.get("CSRF_COOKIE")
        return super().changelist_view(request, extra_context)

    def groupe_de_suggestions(self, obj):
        template_name = "data/_partials/suggestion_groupe_details.html"
        return render_to_string(template_name, obj.serialize().to_dict())


@admin.register(SuggestionUnitaire)
class SuggestionUnitaireAdmin(
    DjangoQLSearchMixin,
    NotEditableMixin,
    NotSelfDeletableMixin,
    QuerysetFilterAdmin,
):
    djangoql_completion_enabled_by_default = False

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
        "raison",
        "parametres",
        "suggestion_modele",
        "champs",
        "valeurs",
        "metadata",
    ]
    readonly_fields = ["cree_le", "modifie_le"]
    list_filter = [
        ("suggestion_groupe__suggestion_cohorte", SuggestionCohorteFilter),
        ("statut", admin.ChoicesFieldListFilter),
    ]


admin.site.register(SuggestionCohorte, SuggestionCohorteAdmin)
admin.site.register(Suggestion, SuggestionAdmin)
