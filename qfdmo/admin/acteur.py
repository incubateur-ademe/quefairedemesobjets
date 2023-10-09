from django.contrib.gis import admin
from django.http import HttpRequest
from import_export import admin as import_export_admin
from import_export import fields, resources, widgets

from qfdmo.models import (
    Acteur,
    ActeurService,
    ActeurType,
    FinalActeur,
    FinalPropositionService,
    PropositionService,
    RevisionActeur,
    RevisionPropositionService,
)
from qfdmo.widget import CustomOSMWidget


class ActeurTypeAdmin(admin.ModelAdmin):
    list_display = ("nom", "nom_affiche")
    search_fields = [
        "nom",
        "nom_affiche",
    ]


class BasePropositionServiceInline(admin.TabularInline):
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


class PropositionServiceInline(BasePropositionServiceInline):
    model = PropositionService

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class RevisionPropositionServiceInline(BasePropositionServiceInline):
    model = RevisionPropositionService


class FinalPropositionServiceInline(BasePropositionServiceInline):
    model = FinalPropositionService

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class NotEditableMixin(admin.GISModelAdmin):
    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class BaseActeurAdmin(admin.GISModelAdmin):
    gis_widget = CustomOSMWidget
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


class ActeurResource(resources.ModelResource):
    delete = fields.Field(widget=widgets.BooleanWidget())
    # sous_categorie = fields.Field(
    #     column_name="sous_categorie_id",
    #     attribute="sous_categorie",
    #     widget=widgets.ForeignKeyWidget(SousCategorieObjet, field="nom"),
    # )

    def for_delete(self, row, instance):
        return self.fields["delete"].clean(row)

    class Meta:
        model = Acteur
        # fields = (
        #     "id",
        #     "nom",
        #     "sous_categorie",
        #     "delete",
        # )


class ActeurAdmin(import_export_admin.ExportMixin, BaseActeurAdmin, NotEditableMixin):
    change_form_template = "admin/acteur/change_form.html"

    ordering = ("nom",)
    resource_classes = [ActeurResource]


class RevisionActeurAdmin(import_export_admin.ImportExportMixin, BaseActeurAdmin):
    gis_widget = CustomOSMWidget
    inlines = [
        RevisionPropositionServiceInline,
    ]
    exclude = ["id"]
    resource_classes = [ActeurResource]


class FinalActeurAdmin(BaseActeurAdmin, NotEditableMixin):
    gis_widget = CustomOSMWidget
    inlines = [
        FinalPropositionServiceInline,
    ]


admin.site.register(ActeurType, ActeurTypeAdmin)
admin.site.register(Acteur, ActeurAdmin)
admin.site.register(RevisionActeur, RevisionActeurAdmin)
admin.site.register(FinalActeur, FinalActeurAdmin)
admin.site.register(ActeurService)
