from django.contrib.gis import admin
from django.urls import reverse
from django.utils.html import format_html

from qfdmo.models import (
    ActeurService,
    ActeurType,
    Action,
    CategorieObjet,
    LVAOBase,
    LVAOBaseRevision,
    PropositionService,
    ReemploiActeur,
    SousCategorieObjet,
)


class SousCategorieAdmin(admin.ModelAdmin):
    list_display = ("nom", "categorie", "code")
    search_fields = [
        "categorie__nom",
        "code",
        "nom",
    ]


class LVAOBaseRevisionAdmin(admin.ModelAdmin):
    list_display = ("nom", "url")
    search_fields = [
        "nom",
        "url",
        "nom_commercial",
        "nom_officiel",
        "siret",
        "identifiant_externe",
    ]


class LVAOBaseRevisionInline(admin.StackedInline):
    model = LVAOBaseRevision
    extra = 0


class LVAOBaseAdmin(admin.ModelAdmin):
    list_display = ("nom", "identifiant_unique")
    search_fields = [
        "nom",
        "identifiant_unique",
    ]
    inlines = [
        LVAOBaseRevisionInline,
    ]


class PropositionServiceInline(admin.TabularInline):
    model = PropositionService
    extra = 0

    @admin.display(description="Sous Categorie")
    def sous_categories_links(self, instance):
        links = []
        for sous_category in instance.sous_categories.all():
            url = reverse(
                "admin:qfdmo_souscategorieobjet_change", args=[sous_category.id]
            )
            links.append(format_html('<a href="{}">{}</a>', url, sous_category))
        return format_html(", ".join(links))

    exclude = ("sous_categories",)
    readonly_fields = (
        "action",
        "acteur_service",
        "sous_categories_links",
    )


class ReemploiActeurAdmin(admin.GISModelAdmin):
    inlines = [
        PropositionServiceInline,
    ]
    list_display = ("nom", "siret", "identifiant_unique", "code_postal", "ville")
    search_fields = [
        "code_postal",
        "identifiant_unique",
        "nom",
        "siret",
        "ville",
    ]
    ordering = ("nom",)


admin.site.register(SousCategorieObjet, SousCategorieAdmin)
admin.site.register(CategorieObjet)
admin.site.register(Action)
admin.site.register(ActeurService)
admin.site.register(ActeurType)
admin.site.register(LVAOBase, LVAOBaseAdmin)
admin.site.register(LVAOBaseRevision, LVAOBaseRevisionAdmin)
admin.site.register(ReemploiActeur, ReemploiActeurAdmin)
