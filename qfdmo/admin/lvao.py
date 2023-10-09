from django.contrib.gis import admin

from qfdmo.models import LVAOBase, LVAOBaseRevision


class LVAOBaseRevisionAdmin(admin.ModelAdmin):
    list_display = ("nom", "url", "lvao_revision_id")
    ordering = ("lvao_revision_id",)
    search_fields = (
        "nom",
        "url",
        "lvao_revision_id",
        "nom_commercial",
        "nom_officiel",
        "siret",
        "identifiant_externe",
    )
    readonly_fields = ("lvao_base",)


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


admin.site.register(LVAOBase, LVAOBaseAdmin)
admin.site.register(LVAOBaseRevision, LVAOBaseRevisionAdmin)
