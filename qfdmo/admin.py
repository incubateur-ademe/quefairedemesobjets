from django.contrib import admin

from qfdmo.models import (
    ActeurService,
    ActeurType,
    Action,
    CategorieObjet,
    LVAOBase,
    LVAOBaseRevision,
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


class LVAOBaseAdmin(admin.ModelAdmin):
    list_display = ("nom", "identifiant_unique")
    search_fields = [
        "nom",
        "identifiant_unique",
    ]


admin.site.register(SousCategorieObjet, SousCategorieAdmin)
admin.site.register(CategorieObjet)
admin.site.register(Action)
admin.site.register(ActeurService)
admin.site.register(ActeurType)
admin.site.register(LVAOBase, LVAOBaseAdmin)
admin.site.register(LVAOBaseRevision, LVAOBaseRevisionAdmin)
