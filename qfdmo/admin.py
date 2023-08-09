from django.contrib import admin

from qfdmo.models import (
    ActeurReemploi,
    ActeurReemploiRevision,
    Action,
    CategorieObjet,
    EntiteService,
    EntiteType,
    SousCategorieObjet,
)


class SousCategorieAdmin(admin.ModelAdmin):
    list_display = ("nom", "categorie", "code")
    search_fields = [
        "categorie__nom",
        "code",
        "nom",
    ]


class ActeurReemploiRevisionAdmin(admin.ModelAdmin):
    list_display = ("nom", "url")
    search_fields = [
        "nom",
        "url",
        "nom_commercial",
        "nom_officiel",
        "siret",
        "identifiant_externe",
    ]


class ActeurReemploiAdmin(admin.ModelAdmin):
    list_display = ("nom", "identifiant_unique")
    search_fields = [
        "nom",
        "identifiant_unique",
    ]


admin.site.register(SousCategorieObjet, SousCategorieAdmin)
admin.site.register(CategorieObjet)
admin.site.register(Action)
admin.site.register(EntiteService)
admin.site.register(EntiteType)
admin.site.register(ActeurReemploi, ActeurReemploiAdmin)
admin.site.register(ActeurReemploiRevision, ActeurReemploiRevisionAdmin)
