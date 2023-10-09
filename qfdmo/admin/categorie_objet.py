from django.contrib.gis import admin
from django.http.request import HttpRequest
from import_export import admin as import_export_admin
from import_export import fields, resources, widgets

from qfdmo.models import CategorieObjet, Objet, SousCategorieObjet


class SousCategorieInline(admin.TabularInline):
    model = SousCategorieObjet
    extra = 0

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class CategorieAdmin(admin.ModelAdmin):
    search_fields = [
        "nom",
    ]
    inlines = [
        SousCategorieInline,
    ]


class SousCategorieAdmin(admin.ModelAdmin):
    list_display = ("nom", "categorie", "code")
    search_fields = [
        "categorie__nom",
        "code",
        "nom",
    ]


class ObjetResource(resources.ModelResource):
    delete = fields.Field(widget=widgets.BooleanWidget())
    sous_categorie = fields.Field(
        column_name="sous_categorie_id",
        attribute="sous_categorie",
        widget=widgets.ForeignKeyWidget(SousCategorieObjet, field="nom"),
    )

    def for_delete(self, row, instance):
        return self.fields["delete"].clean(row)

    class Meta:
        model = Objet
        fields = (
            "id",
            "nom",
            "sous_categorie",
            "delete",
        )


class ObjetAdmin(import_export_admin.ImportExportModelAdmin):
    list_display = ("nom", "sous_categorie")
    search_fields = [
        "nom",
        "sous_categorie__nom",
    ]
    resource_classes = [ObjetResource]


admin.site.register(CategorieObjet, CategorieAdmin)
admin.site.register(SousCategorieObjet, SousCategorieAdmin)
admin.site.register(Objet, ObjetAdmin)
