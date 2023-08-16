from django.contrib.gis import admin

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

    fields = (
        "action",
        "acteur_service",
        "sous_categories",
    )

    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return False
        return super().has_change_permission(request, obj)


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
