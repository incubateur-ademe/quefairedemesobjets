from django.contrib import admin

from qfdmo.models import (
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


admin.site.register(SousCategorieObjet, SousCategorieAdmin)
admin.site.register(CategorieObjet)
admin.site.register(Action)
admin.site.register(EntiteService)
admin.site.register(EntiteType)
