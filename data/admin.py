import logging

from django.contrib import admin, messages
from django.utils.html import format_html

from core.admin import NotEditableMixin, NotSelfDeletableMixin
from data.models.suggestion import Suggestion, SuggestionCohorte, SuggestionStatut

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


class SuggestionCohorteAdmin(NotEditableMixin, admin.ModelAdmin):
    list_display = [
        "id",
        "__str__",
        "statut",
        "metadonnees",
    ]

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


class SuggestionAdmin(NotSelfDeletableMixin, admin.ModelAdmin):

    class SuggestionCohorteFilter(admin.RelatedFieldListFilter):
        def field_choices(self, field, request, model_admin):
            return field.get_choices(include_blank=False, ordering=("-cree_le",))

    search_fields = ["contexte", "suggestion"]
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


admin.site.register(SuggestionCohorte, SuggestionCohorteAdmin)
admin.site.register(Suggestion, SuggestionAdmin)
