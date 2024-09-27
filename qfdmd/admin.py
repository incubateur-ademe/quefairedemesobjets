from django.contrib.gis import admin

from qfdmd.models import Produit
from qfdmo.admin.acteur import NotEditableInlineMixin


class ProduitAdmin(NotEditableInlineMixin, admin.ModelAdmin):
    list_display = ("id", "libelle")
    search_fields = [
        "id",
    ]


admin.site.register(Produit, ProduitAdmin)
