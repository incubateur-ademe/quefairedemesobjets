from abc import abstractmethod

from django.contrib import admin, messages
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect, reverse
from django.utils.html import format_html
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin

from qfdmd.models import Lien, Produit, Suggestion, Synonyme


class LienResource(resources.ModelResource):
    class Meta:
        model = Lien


class KoumoulModelResource(resources.ModelResource):
    """Base class to map Django model fields to Koumoul columns for export."""

    koumoul_mapping: dict[str, str] = {}

    def get_export_fields(self, *args, **kwargs):
        """Update column names based on koumoul_mapping."""
        fields = super().get_export_fields(*args, **kwargs)
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
    infotri = fields.Field(
        column_name="Infotri",
    )

    def dehydrate_infotri(self, instance):
        if instance.infotri:
            return "oui"
        return "non"

    class Meta:
        model = Produit
        name = "Import/export de tous les champs Produit"


class SynonymeResource(resources.ModelResource):
    infotri = fields.Field(
        column_name="Infotri",
    )

    def dehydrate_infotri(self, instance):
        if instance.produit.infotri:
            return "oui"
        return "non"

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
    autocomplete_fields = ["produit"]
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


class WagtailRedirectMixin:
    """Mixin to redirect to Wagtail admin if the object has a next_wagtail_page.

    Note: This mixin does not inherit from ABC to avoid metaclass conflicts when
    used with Django's admin.ModelAdmin (which has its own metaclass). The
    @abstractmethod decorator still indicates that get_wagtail_page must be
    implemented by subclasses.
    """

    @abstractmethod
    def get_wagtail_page(self, obj):
        pass

    def change_view(self, request, object_id, form_url="", extra_context=None):
        obj = self.get_object(request, object_id)
        force_display_change = "force" in request.GET

        if obj and not force_display_change:
            try:
                wagtail_page = self.get_wagtail_page(obj)
                if wagtail_page:
                    django_admin_url = (
                        f"{request.path}?force=true"
                        if not request.GET
                        else f"{request.path}?{request.GET.urlencode()}&force=true"
                    )

                    messages.info(
                        request,
                        format_html(
                            "Vous avez été redirigé vers la page suivante car elle"
                            " n'est plus éditable dans Django Admin. "
                            f"<a style='color:white;' href='{django_admin_url}'>"
                            "<u>Cliquez ici pour revenir à Django Admin</u></a>."
                        ),
                    )
                    return redirect(
                        reverse("wagtailadmin_pages:edit", args=[wagtail_page.page.id])
                    )
            except Produit.next_wagtail_page.RelatedObjectDoesNotExist:
                pass

        return self.changeform_view(request, object_id, form_url, extra_context)


@admin.register(Produit)
class ProduitAdmin(
    WagtailRedirectMixin,
    MoveFieldsToFirstPositionMixin,
    ImportExportModelAdmin,
    admin.ModelAdmin,
):
    resource_classes = [ProduitResource, KoumoulProduitResource]
    list_display = ("nom", "id", "display_sous_categories", "modifie_le")
    search_fields = ["nom__unaccent", "id", "synonymes_existants__unaccent"]
    # ajout des filtres de recherche sur bdd et code
    list_filter = ["bdd", "code"]
    fields_to_display_in_first_position = ["nom"]
    inlines = [SynonymeInline, LienInline]
    exclude = ("infotri",)
    ordering = ["-modifie_le"]
    readonly_fields = ["display_sous_categories"]

    def get_wagtail_page(self, obj):
        return obj.next_wagtail_page

    def display_sous_categories(self, obj):
        """Display sous_categories with links to their admin pages."""
        if obj.pk is None:
            return "-"

        sous_categories = obj.sous_categories.all()
        if not sous_categories:
            return "-"

        links = []
        for sc in sous_categories:
            url = reverse(
                "admin:qfdmo_souscategorieobjet_change",
                args=[sc.pk],
            )
            links.append(f'<a href="{url}">{sc.libelle}</a>')

        return format_html("<br>".join(links))

    display_sous_categories.short_description = "Sous-catégories"


@admin.register(Lien)
class LienAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = LienResource
    list_display = ("titre_du_lien", "url", "description")
    search_fields = ["titre_du_lien__unaccent", "url", "description__unaccent"]
    inlines = [ProduitInline]


@admin.register(Synonyme)
class SynonymeAdmin(
    WagtailRedirectMixin,
    MoveFieldsToFirstPositionMixin,
    ImportExportModelAdmin,
    admin.ModelAdmin,
):
    resource_classes = [SynonymeResource]
    search_fields = ["nom__unaccent"]
    readonly_fields = ["slug"]
    list_display = ("nom", "produit", "slug", "modifie_le")
    list_filter = [("picto", admin.EmptyFieldListFilter), "pin_on_homepage"]
    autocomplete_fields = ["produit"]
    fields_to_display_in_first_position = ["nom", "produit"]
    ordering = ["-modifie_le"]

    def get_wagtail_page(self, obj):
        # First check if the synonyme has a direct redirection
        try:
            return obj.next_wagtail_page
        except Synonyme.next_wagtail_page.RelatedObjectDoesNotExist:
            pass

        # Otherwise, try to redirect via the produit
        try:
            return obj.produit.next_wagtail_page
        except Produit.next_wagtail_page.RelatedObjectDoesNotExist:
            return None
