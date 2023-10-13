from django.contrib.gis import admin
from django.http import HttpRequest
from import_export import admin as import_export_admin
from import_export import fields, resources, widgets

from qfdmo.models import (
    Acteur,
    ActeurService,
    ActeurType,
    Action,
    FinalActeur,
    FinalPropositionService,
    PropositionService,
    RevisionActeur,
    RevisionPropositionService,
    SousCategorieObjet,
)
from qfdmo.widget import CustomOSMWidget


class NotEditableMixin(admin.GISModelAdmin):
    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class NotEditableInlineMixin:
    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


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


class PropositionServiceInline(BasePropositionServiceInline, NotEditableInlineMixin):
    model = PropositionService


class RevisionPropositionServiceInline(BasePropositionServiceInline):
    model = RevisionPropositionService


class FinalPropositionServiceInline(
    BasePropositionServiceInline, NotEditableInlineMixin
):
    model = FinalPropositionService

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
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
    acteur_type = fields.Field(
        column_name="acteur_type_id",
        attribute="acteur_type",
        widget=widgets.ForeignKeyWidget(ActeurType, field="nom"),
    )

    def for_delete(self, row, instance):
        return self.fields["delete"].clean(row)

    class Meta:
        model = Acteur


class ActeurAdmin(import_export_admin.ExportMixin, BaseActeurAdmin, NotEditableMixin):
    change_form_template = "admin/acteur/change_form.html"

    ordering = ("nom",)
    resource_classes = [ActeurResource]


class RevisionActeurResource(ActeurResource):
    class Meta:
        model = RevisionActeur


class RevisionActeurAdmin(import_export_admin.ImportExportMixin, BaseActeurAdmin):
    gis_widget = CustomOSMWidget
    inlines = [
        RevisionPropositionServiceInline,
    ]
    exclude = ["id"]
    resource_classes = [RevisionActeurResource]


class BasePropositionServiceAdmin(admin.GISModelAdmin):
    pass


class BasePropositionServiceResource(resources.ModelResource):
    delete = fields.Field(widget=widgets.BooleanWidget())

    action = fields.Field(
        column_name="action_id",
        attribute="action",
        widget=widgets.ForeignKeyWidget(Action, field="nom"),
    )
    acteur_service = fields.Field(
        column_name="acteur_service_id",
        attribute="acteur_service",
        widget=widgets.ForeignKeyWidget(ActeurService, field="nom"),
    )
    # sous_categories = models.ManyToManyField(
    #     SousCategorieObjet,
    # )
    sous_categories = fields.Field(
        column_name="sous_categories",
        attribute="sous_categories",
        widget=widgets.ManyToManyWidget(SousCategorieObjet, field="nom", separator="|"),
    )

    def for_delete(self, row, instance):
        return self.fields["delete"].clean(row)


class PropositionServiceResource(BasePropositionServiceResource):
    acteur = fields.Field(
        column_name="acteur",
        attribute="acteur",
        widget=widgets.ForeignKeyWidget(Acteur, field="identifiant_unique"),
    )

    class Meta:
        model = PropositionService


class PropositionServiceAdmin(
    import_export_admin.ExportMixin, BasePropositionServiceAdmin, NotEditableMixin
):
    resource_classes = [PropositionServiceResource]
    search_fields = [
        "acteur__nom",
        "acteur__siret",
    ]


class RevisionPropositionServiceResource(BasePropositionServiceResource):
    revision_acteur = fields.Field(
        column_name="acteur",
        attribute="revision_acteur",
        widget=widgets.ForeignKeyWidget(RevisionActeur, field="identifiant_unique"),
    )

    class Meta:
        model = RevisionPropositionService


class RevisionPropositionServiceAdmin(
    import_export_admin.ImportExportMixin, BasePropositionServiceAdmin
):
    resource_classes = [RevisionPropositionServiceResource]
    search_fields = [
        "revision_acteur__nom",
        "revision_acteur__siret",
    ]


class FinalActeurAdmin(BaseActeurAdmin, NotEditableMixin):
    gis_widget = CustomOSMWidget
    inlines = [
        FinalPropositionServiceInline,
    ]


admin.site.register(Acteur, ActeurAdmin)
admin.site.register(ActeurService)
admin.site.register(ActeurType, ActeurTypeAdmin)
admin.site.register(FinalActeur, FinalActeurAdmin)
admin.site.register(PropositionService, PropositionServiceAdmin)
admin.site.register(RevisionActeur, RevisionActeurAdmin)
admin.site.register(RevisionPropositionService, RevisionPropositionServiceAdmin)
