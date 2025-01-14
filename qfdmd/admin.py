from django.contrib import admin
from django_extensions.db.fields import ImproperlyConfigured
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from qfdmd.models import CMSPage, Lien, Produit, Suggestion, Synonyme


class LienResource(resources.ModelResource):
    class Meta:
        model = Lien


class KoumoulModelResource(resources.ModelResource):
    """Base class to map Django model fields to Koumoul columns for export."""

    koumoul_mapping: dict[str, str] = {}

    def get_export_fields(self):
        """Update column names based on koumoul_mapping."""
        fields = super().get_export_fields()
        for field in fields:
            field.column_name = self.koumoul_mapping.get(
                field.attribute, field.column_name
            )
        return fields

    def __init__(self, *args, **kwargs):
        """Validate koumoul_mapping and ensure field names are valid."""
        super().__init__(*args, **kwargs)

        if not self.koumoul_mapping:
            error_message = (
                "The mapping between Django model fields and Koumoul fields"
                " is not defined."
            )
            raise ImproperlyConfigured(error_message)

        model_fields = {field.name for field in self._meta.model._meta.get_fields()}
        invalid_fields = [
            field for field in self.koumoul_mapping if field not in model_fields
        ]

        if invalid_fields:
            error_message = (
                "The following fields in koumoul_mapping are not part"
                f" of the model: {', '.join(invalid_fields)}"
            )
            raise ImproperlyConfigured(error_message)

        # Remove fields not in koumoul_mapping
        self.fields = {
            field: self.fields[field]
            for field in self.fields
            if field in self.koumoul_mapping
        }


class KoumoulProduitResource(KoumoulModelResource):
    koumoul_mapping = {
        "id": "ID",
        "nom": "Nom",
        "synonymes_existants": "Synonymes_existants",
        "code": "Code",
        "bdd": "Bdd",
        "comment_les_eviter": "Comment_les_eviter_?",
        "qu_est_ce_que_j_en_fais": "Qu'est-ce_que_j'en_fais_?",
        "que_va_t_il_devenir": "Que_va-t-il_devenir_?",
        "nom_eco_organisme": "nom_eco_organisme",
        "filieres_rep": "filieres_REP",
        "slug": "Slug",
    }

    class Meta:
        model = Produit
        name = "Import/export des champs Koumoul uniquement"


class ProduitResource(resources.ModelResource):
    class Meta:
        model = Produit
        name = "Import/export de tous les champs Produit"


class SynonymeResource(resources.ModelResource):
    class Meta:
        model = Synonyme


class SynonymeInline(admin.StackedInline):
    fields = ("nom",)
    model = Synonyme
    extra = 0


class LienInline(admin.StackedInline):
    autocomplete_fields = ("lien",)
    model = Lien.produits.through
    extra = 0


class ProduitInline(admin.StackedInline):
    model = Produit.liens.through
    extra = 0


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    autocomplete_fields = ["produit"]


class MoveFieldsToFirstPositionMixin:
    def get_fields(self, request, obj=None, **kwargs):
        fields = super().get_fields(request, obj, **kwargs)

        for field in self.fields_to_display_in_first_position:
            if field not in fields:
                raise ImproperlyConfigured(
                    f"{field} is set in "
                    "fields_to_display_in_first_position but does not belong "
                    f"to the model to {self.model} admin model"
                )
            fields.remove(field)

        fields = [*self.fields_to_display_in_first_position, *fields]
        return fields


@admin.register(Produit)
class ProduitAdmin(
    MoveFieldsToFirstPositionMixin, ImportExportModelAdmin, admin.ModelAdmin
):
    resource_classes = [ProduitResource, KoumoulProduitResource]
    list_display = ("nom", "id", "modifie_le")
    search_fields = ["nom__unaccent", "id", "synonymes_existants__unaccent"]
    # ajout des filtres de recherche sur bdd et code
    list_filter = ["bdd", "code"]
    fields_to_display_in_first_position = ["id", "nom"]
    inlines = [SynonymeInline, LienInline]


@admin.register(Lien)
class LienAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = LienResource
    list_display = ("titre_du_lien", "url", "description")
    search_fields = ["titre_du_lien__unaccent", "url", "description__unaccent"]
    inlines = [ProduitInline]


@admin.register(Synonyme)
class SynonymeAdmin(
    MoveFieldsToFirstPositionMixin, ImportExportModelAdmin, admin.ModelAdmin
):
    resource_classes = [SynonymeResource]
    search_fields = ["nom__unaccent"]
    readonly_fields = ["slug"]
    list_display = ("nom", "produit", "slug", "modifie_le")
    list_filter = ["pin_on_homepage"]
    fields_to_display_in_first_position = ["nom", "produit"]


@admin.register(CMSPage)
class CMSPageAdmin(admin.ModelAdmin):
    @property
    def readonly_fields(self):
        fields = [field.name for field in self.model._meta.get_fields()]
        fields.remove("id")
        return fields
