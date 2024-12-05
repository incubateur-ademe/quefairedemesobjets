from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from qfdmd.models import Lien, Produit, Suggestion, Synonyme
from qfdmo.admin.acteur import NotEditableInlineMixin


class SynonymeResource(resources.ModelResource):
    class Meta:
        model = Synonyme


class SynonymeInline(admin.StackedInline):
    model = Synonyme
    extra = 1


class LienInline(admin.StackedInline):
    model = Lien.produits.through
    extra = 1


class ProduitInline(admin.StackedInline):
    model = Produit.liens.through
    extra = 1


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    autocomplete_fields = ["produit"]


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ("nom", "id", "synonymes_existants")
    search_fields = ["nom__unaccent", "id", "synonymes_existants__unaccent"]
    # ajout des filtres de recherche sur bdd et code
    list_filter = ["bdd", "code"]
    inlines = [SynonymeInline, LienInline]


@admin.register(Lien)
class LienAdmin(NotEditableInlineMixin, admin.ModelAdmin):
    list_display = ("titre_du_lien", "url", "description")
    inlines = [ProduitInline]


@admin.register(Synonyme)
class SynonymeAdmin(NotEditableInlineMixin, ImportExportModelAdmin, admin.ModelAdmin):
    resource_classes = [SynonymeResource]
    search_fields = ["nom__unaccent"]
    list_display = ("nom", "produit", "slug")
