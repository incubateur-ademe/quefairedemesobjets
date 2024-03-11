from typing import Any

from django.conf import settings
from django.contrib.gis import admin
from django.contrib.gis.forms.fields import PointField
from django.contrib.gis.geos import Point
from django.forms import CharField
from django.http import HttpRequest
from import_export import admin as import_export_admin
from import_export import fields, resources, widgets

from qfdmo.models import (
    Acteur,
    ActeurService,
    ActeurType,
    Action,
    CorrectionActeur,
    FinalActeur,
    FinalPropositionService,
    PropositionService,
    RevisionActeur,
    RevisionPropositionService,
    Source,
    SousCategorieObjet,
)
from qfdmo.models.acteur import (
    CorrectionEquipeActeur,
    CorrectionEquipePropositionService,
    DisplayedActeur,
    DisplayedPropositionService,
)
from qfdmo.widget import CustomOSMWidget


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
    search_help_text = "Recherche sur le nom ou le nom affiché"


class BasePropositionServiceInline(admin.TabularInline):
    extra = 0

    fields = (
        "action",
        "acteur_service",
        "sous_categories",
    )


class PropositionServiceInline(BasePropositionServiceInline, NotEditableInlineMixin):
    model = PropositionService

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RevisionPropositionServiceInline(BasePropositionServiceInline):
    model = RevisionPropositionService


class CorrectionEquipePropositionServiceInline(BasePropositionServiceInline):
    model = CorrectionEquipePropositionService


class FinalPropositionServiceInline(
    BasePropositionServiceInline, NotEditableInlineMixin
):
    model = FinalPropositionService

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class DisplayedPropositionServiceInline(
    BasePropositionServiceInline, NotEditableInlineMixin
):
    model = DisplayedPropositionService

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None):
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
    search_help_text = (
        "Recherche sur le nom, le code postal, la ville, le siret ou"
        " l'identifiant unique"
    )
    list_filter = ["statut"]
    fields = (
        "identifiant_unique",
        "source",
        "identifiant_externe",
        "nom",
        "nom_commercial",
        "nom_officiel",
        "siret",
        "naf_principal",
        "description",
        "acteur_type",
        "url",
        "email",
        "telephone",
        "adresse",
        "adresse_complement",
        "code_postal",
        "ville",
        "location",
        "horaires",
        "multi_base",
        "manuel",
        "label_reparacteur",
        "statut",
        "commentaires",
        "cree_le",
        "modifie_le",
    )

    readonly_fields = [
        "cree_le",
        "modifie_le",
    ]

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj and "identifiant_unique" not in readonly_fields:
            readonly_fields += ["identifiant_unique"]
        return readonly_fields


class ActeurResource(resources.ModelResource):
    nb_object_max = settings.DJANGO_IMPORT_EXPORT_LIMIT

    delete = fields.Field(widget=widgets.BooleanWidget())
    acteur_type = fields.Field(
        column_name="acteur_type",
        attribute="acteur_type",
        widget=widgets.ForeignKeyWidget(ActeurType, field="nom"),
    )
    source = fields.Field(
        column_name="source",
        attribute="source",
        widget=widgets.ForeignKeyWidget(Source, field="nom"),
    )
    latitude = fields.Field(column_name="latitude", attribute="latitude", readonly=True)
    longitude = fields.Field(
        column_name="longitude", attribute="longitude", readonly=True
    )

    def __init__(self, **kwargs):
        if "nb_object_max" in kwargs:
            self.nb_object_max = kwargs["nb_object_max"]
        super().__init__(**kwargs)

    def for_delete(self, row, instance):
        return self.fields["delete"].clean(row)

    def before_import_row(self, row, row_number=None, **kwargs):
        latitude = row.get("latitude")
        longitude = row.get("longitude")
        if latitude and longitude:
            row["location"] = Point(float(longitude), float(latitude), srid=4326)
        else:
            row["location"] = None

    def get_queryset(self):
        if self.nb_object_max:
            return super().get_queryset()[: self.nb_object_max]
        return super().get_queryset()

    class Meta:
        model = Acteur
        import_id_fields = ["identifiant_unique"]
        store_instance = True
        exclude = [
            "cree_le",
            "modifie_le",
        ]


class ActeurAdmin(import_export_admin.ExportMixin, BaseActeurAdmin):
    change_form_template = "admin/acteur/change_form.html"
    modifiable = False
    ordering = ("nom",)
    resource_classes = [ActeurResource]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields if f.name != "location"]

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class RevisionActeurResource(ActeurResource):
    class Meta:
        model = RevisionActeur


class RevisionActeurAdmin(import_export_admin.ImportExportMixin, BaseActeurAdmin):
    gis_widget = CustomOSMWidget
    inlines = [RevisionPropositionServiceInline]
    exclude = ["id"]
    resource_classes = [RevisionActeurResource]

    def get_form(
        self, request: Any, obj: Any | None = None, change: bool = False, **kwargs: Any
    ) -> Any:
        """
        Display Acteur fields value as help_text
        """
        revision_acteur_form = super().get_form(request, obj, change, **kwargs)
        if obj and obj.identifiant_unique:
            acteur = Acteur.objects.get(identifiant_unique=obj.identifiant_unique)
            for field_name, form_field in revision_acteur_form.base_fields.items():
                acteur_value = getattr(acteur, field_name)
                if acteur_value and isinstance(form_field, PointField):
                    (lon, lat) = acteur_value.coords
                    acteur_value = {
                        "type": "Point",
                        "coordinates": [lon, lat],
                    }
                form_field.help_text = str(acteur_value)
                acteur_value_js = str(acteur_value).replace("'", "\\'")

                if acteur_value and (
                    isinstance(form_field, CharField)
                    or isinstance(form_field, PointField)
                ):
                    form_field.help_text += (
                        '&nbsp;<button type="button" onclick="document.getElementById('
                        f"'id_{field_name}').value = '{acteur_value_js}'"
                        '">copy</button>'
                        '&nbsp;<button type="button" onclick="'
                        f"document.getElementById('id_{field_name}').value = ''"
                        '">reset</button>'
                    )
        return revision_acteur_form


class CorrectionEquipeActeurResource(ActeurResource):
    class Meta:
        model = CorrectionEquipeActeur


class CorrectionEquipeActeurAdmin(
    import_export_admin.ImportExportMixin, BaseActeurAdmin
):
    gis_widget = CustomOSMWidget
    inlines = [CorrectionEquipePropositionServiceInline]
    exclude = ["id"]
    resource_classes = [CorrectionEquipeActeurResource]

    def get_form(
        self, request: Any, obj: Any | None = None, change: bool = False, **kwargs: Any
    ) -> Any:
        """
        Display Acteur fields value as help_text
        """
        correction_equipe_acteur_form = super().get_form(request, obj, change, **kwargs)
        if obj and obj.identifiant_unique:
            acteur = Acteur.objects.get(identifiant_unique=obj.identifiant_unique)
            for (
                field_name,
                form_field,
            ) in correction_equipe_acteur_form.base_fields.items():
                acteur_value = getattr(acteur, field_name)
                if acteur_value and isinstance(form_field, PointField):
                    (lon, lat) = acteur_value.coords
                    acteur_value = {
                        "type": "Point",
                        "coordinates": [lon, lat],
                    }
                form_field.help_text = str(acteur_value)
                acteur_value_js = str(acteur_value).replace("'", "\\'")

                if acteur_value and (
                    isinstance(form_field, CharField)
                    or isinstance(form_field, PointField)
                ):
                    form_field.help_text += (
                        '&nbsp;<button type="button" onclick="document.getElementById('
                        f"'id_{field_name}').value = '{acteur_value_js}'"
                        '">copy</button>'
                        '&nbsp;<button type="button" onclick="'
                        f"document.getElementById('id_{field_name}').value = ''"
                        '">reset</button>'
                    )
        return correction_equipe_acteur_form


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
    import_export_admin.ExportMixin, BasePropositionServiceAdmin
):
    resource_classes = [PropositionServiceResource]
    search_fields = [
        "acteur__nom",
        "acteur__siret",
    ]
    search_help_text = "Recherche sur le nom ou le siret de l'acteur"

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class RevisionPropositionServiceResource(BasePropositionServiceResource):
    acteur = fields.Field(
        column_name="acteur",
        attribute="acteur",
        widget=widgets.ForeignKeyWidget(RevisionActeur, field="identifiant_unique"),
    )

    class Meta:
        model = RevisionPropositionService


class CorrectionEquipePropositionServiceResource(BasePropositionServiceResource):
    correction_equipe_acteur = fields.Field(
        column_name="acteur",
        attribute="correction_equipe_acteur",
        widget=widgets.ForeignKeyWidget(
            CorrectionEquipeActeur, field="identifiant_unique"
        ),
    )

    class Meta:
        model = CorrectionEquipePropositionService


class RevisionPropositionServiceAdmin(
    import_export_admin.ImportExportMixin, BasePropositionServiceAdmin
):
    def sous_categorie_list(self, obj):
        return ", ".join([str(sc) for sc in obj.sous_categories.all()])

    resource_classes = [RevisionPropositionServiceResource]
    list_display = ["__str__", "sous_categorie_list"]
    search_fields = [
        "acteur__nom",
        "acteur__siret",
    ]
    search_help_text = "Recherche sur le nom ou le siret de l'acteur"


class CorrectionEquipePropositionServiceAdmin(
    import_export_admin.ImportExportMixin, BasePropositionServiceAdmin
):
    def sous_categorie_list(self, obj):
        return ", ".join([str(sc) for sc in obj.sous_categories.all()])

    resource_classes = [CorrectionEquipePropositionServiceResource]
    list_display = ["__str__", "sous_categorie_list"]
    search_fields = [
        "correction_equipe_acteur__nom",
        "correction_equipe_acteur__siret",
    ]
    search_help_text = "Recherche sur le nom ou le siret de l'acteur"


class FinalActeurResource(ActeurResource):
    class Meta:
        model = FinalActeur


class FinalActeurAdmin(import_export_admin.ExportMixin, BaseActeurAdmin):
    change_form_template = "admin/final_acteur/change_form.html"
    gis_widget = CustomOSMWidget
    inlines = [
        FinalPropositionServiceInline,
    ]
    modifiable = False
    resource_classes = [FinalActeurResource]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields if f.name != "location"]

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class DisplayedActeurResource(ActeurResource):
    class Meta:
        model = DisplayedActeur


class DisplayedActeurAdmin(import_export_admin.ExportMixin, BaseActeurAdmin):
    change_form_template = "admin/final_acteur/change_form.html"
    gis_widget = CustomOSMWidget
    inlines = [
        DisplayedPropositionServiceInline,
    ]
    modifiable = False
    resource_classes = [DisplayedActeurResource]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields if f.name != "location"]

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class CorrectionActeurAdmin(BaseActeurAdmin):
    gis_widget = CustomOSMWidget
    inlines = []
    list_display = ["__str__", "source", "correction_statut"]
    readonly_fields = ["final_acteur", "cree_le", "modifie_le"]


admin.site.register(Acteur, ActeurAdmin)
admin.site.register(ActeurService)
admin.site.register(ActeurType, ActeurTypeAdmin)
admin.site.register(CorrectionActeur, CorrectionActeurAdmin)
admin.site.register(FinalActeur, FinalActeurAdmin)
admin.site.register(DisplayedActeur, DisplayedActeurAdmin)
admin.site.register(PropositionService, PropositionServiceAdmin)
admin.site.register(RevisionActeur, RevisionActeurAdmin)
admin.site.register(RevisionPropositionService, RevisionPropositionServiceAdmin)
admin.site.register(CorrectionEquipeActeur, CorrectionEquipeActeurAdmin)
admin.site.register(
    CorrectionEquipePropositionService, CorrectionEquipePropositionServiceAdmin
)
admin.site.register(Source)
