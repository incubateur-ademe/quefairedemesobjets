from django.contrib.gis import admin
from django.utils.html import format_html

from data.models import Suggestion, SuggestionCohorte


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


class SuggestionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "cohorte",
        "statut",
        "contexte",
        "changements",
    ]
    list_filter = ["suggestion_cohorte"]

    def cohorte(self, obj):
        coh = obj.suggestion_cohorte
        return format_html(f"{coh.identifiant_action}<br/>{coh.identifiant_execution}")

    def acteur_link_html(self, id):
        return f"""<a target='_blank'
        href='/admin/qfdmo/displayedacteur/{id}/change/'>{id}</a>"""

    def changements(self, obj):
        data = obj.suggestion
        return format_html(
            f"""
            <b>cluster_id:</b><br/>
            <ul><li>{data[0]["cluster_id"]}</li></ul>
            <b>acteurs:</b><br/><ul>
            {''.join([
                '<li>'+self.acteur_link_html(x["identifiant_unique"])+'</li>'
                for x in data
            ])}<br/>
            </ul>
            """
        )


admin.site.register(SuggestionCohorte, SuggestionCohorteAdmin)
admin.site.register(Suggestion, SuggestionAdmin)
