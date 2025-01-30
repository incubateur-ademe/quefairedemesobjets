from django.contrib.gis import admin
from django.utils.html import format_html

from data.models import Suggestion, SuggestionCohorte
from data.models.suggestion import SuggestionStatut


def dict_to_html_table(data):
    table = "<table class'table-metadata'>"
    for key in sorted(data.keys()):
        value = data[key]
        table += f"<tr><td>{key}</td><td>{value}</td></tr>"
    table += "</table>"
    return table


class SuggestionCohorteAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "identifiant_action",
        "identifiant_execution",
        "statut",
        "metadonnees",
    ]

    def metadonnees(self, obj):
        return format_html(dict_to_html_table(obj.metadata or {}))


@admin.action(description="REJETER les suggestions selectionnées")
def mark_as_rejected(self, request, queryset):
    queryset.update(statut=SuggestionStatut.REJETEE)
    self.message_user(request, "Les suggestions sélectionnées ont été refusées")


@admin.action(description="VALIDER les suggestions selectionnées")
def mark_as_toproceed(self, request, queryset):
    queryset.update(statut=SuggestionStatut.ATRAITER)
    self.message_user(
        request,
        "Les suggestions sélectionnées ont été mises à jour"
        " avec le statut «À traiter»",
    )


class SuggestionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "cohorte",
        "statut",
        "donnees_initiales",
        "changements_suggerés",
    ]
    list_filter = ["suggestion_cohorte", "statut"]
    actions = [mark_as_rejected, mark_as_toproceed]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("suggestion_cohorte")

    def cohorte(self, obj):
        coh = obj.suggestion_cohorte
        return format_html(f"{coh.identifiant_action}<br/>{coh.identifiant_execution}")

    def acteur_link_html(self, id):
        return f"""<a target='_blank'
        href='/admin/qfdmo/displayedacteur/{id}/change/'>{id}</a>"""

    def changements_suggerés(self, obj):
        return obj.display_suggestion_details

    def donnees_initiales(self, obj):
        return obj.display_contexte_details


admin.site.register(SuggestionCohorte, SuggestionCohorteAdmin)
admin.site.register(Suggestion, SuggestionAdmin)
