from django.contrib.gis import admin
from qfdmd.models import Produit


class ProduitAdmin(admin.ModelAdmin):
    list_display = ("id", "libelle")
    search_fields = [
        "id",
    ]


admin.site.register(Produit, ProduitAdmin)
