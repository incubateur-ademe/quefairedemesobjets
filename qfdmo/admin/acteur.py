from typing import Any

from django import forms
from django.conf import settings
from django.contrib.gis import admin
from django.contrib.gis.forms.fields import PointField
from django.contrib.gis.geos import Point
from django.contrib.postgres.lookups import Unaccent
from django.db.models.functions import Lower
from django.forms import CharField
from django.http import HttpRequest
from import_export import admin as import_export_admin
from import_export import fields, resources, widgets

from qfdmo.models import (
    Acteur,
    ActeurService,
    ActeurType,
    Action,
    PropositionService,
    RevisionActeur,
    RevisionPropositionService,
    Source,
    SousCategorieObjet,
)
from qfdmo.models.acteur import (
    DisplayedActeur,
    DisplayedPropositionService,
    LabelQualite,
)
from qfdmo.widget import CustomOSMWidget


class NotEditableInlineMixin:
    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class ActeurLabelQualiteInline(admin.StackedInline):
    model = Acteur.labels.through
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RevisionActeurLabelQualiteInline(admin.StackedInline):
    model = RevisionActeur.labels.through
    extra = 0


class DisplayedActeurLabelQualiteInline(admin.StackedInline):
    model = DisplayedActeur.labels.through
    extra = 0

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class BasePropositionServiceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "action" in self.fields:
            self.fields["action"].queryset = Action.objects.annotate(
                libelle_unaccent=Unaccent(Lower("libelle")),
            ).order_by("libelle_unaccent")
        if "sous_categories" in self.fields:
            self.fields["sous_categories"].queryset = (
                SousCategorieObjet.objects.annotate(
                    libelle_unaccent=Unaccent(Lower("libelle")),
                ).order_by("libelle_unaccent")
            )


class InlinePropositionServiceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "sous_categories" in self.fields:
            self.fields["sous_categories"].queryset = (
                SousCategorieObjet.objects.annotate(
                    libelle_unaccent=Unaccent(Lower("libelle")),
                    categorie_libelle_unaccent=Unaccent(Lower("categorie__libelle")),
                ).order_by("categorie_libelle_unaccent", "libelle_unaccent")
            )


class BasePropositionServiceInline(admin.TabularInline):
    form = InlinePropositionServiceForm
    extra = 0

    fields = (
        "action",
        "sous_categories",
    )

    filter_vertical = ("sous_categories",)


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


class BaseActeurForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "source" in self.fields:
            self.fields["source"].queryset = Source.objects.all().order_by("libelle")


class BaseActeurAdmin(admin.GISModelAdmin):
    form = BaseActeurForm
    gis_widget = CustomOSMWidget
    inlines = [
        PropositionServiceInline,
    ]
    filter_horizontal = ("labels",)
    list_display = (
        "nom",
        "siret",
        "identifiant_unique",
        "code_postal",
        "ville",
        "adresse",
        "modifie_le",
    )
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
        "horaires_osm",
        "horaires_description",
        "public_accueilli",
        "reprise",
        "exclusivite_de_reprisereparation",
        "uniquement_sur_rdv",
        "statut",
        "commentaires",
        "cree_le",
        "modifie_le",
        "acteur_services",
    )

    readonly_fields = [
        "cree_le",
        "modifie_le",
    ]

    ordering = ("-modifie_le",)

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
        widget=widgets.ForeignKeyWidget(ActeurType, field="code"),
    )
    source = fields.Field(
        column_name="source",
        attribute="source",
        widget=widgets.ForeignKeyWidget(Source, field="code"),
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
    inlines = list(BaseActeurAdmin.inlines) + [ActeurLabelQualiteInline]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields if f.name != "location"]

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class RevisionActeurResource(ActeurResource):
    class Meta:
        model = RevisionActeur


class RevisionActeurAdmin(import_export_admin.ImportExportMixin, BaseActeurAdmin):
    save_as = True
    gis_widget = CustomOSMWidget
    inlines = [RevisionPropositionServiceInline, RevisionActeurLabelQualiteInline]

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

                if field_name == "acteur_services":
                    form_field.help_text = acteur.get_acteur_services()

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
                if field_name == "siret" and (
                    siret := obj.siret or acteur.siret
                ):  # and siret is not null
                    siren = siret[:9]
                    form_field.help_text += (
                        '<br>ENTREPRISE : <a href="https://'
                        f'annuaire-entreprises.data.gouv.fr/entreprise/{siren}"'
                        ' target="_blank" rel="noopener" rel="noreferrer">'
                        f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}"
                        '</a><br>ETABLISSEMENT : <a href="https://'
                        f'annuaire-entreprises.data.gouv.fr/etablissement/{siret}"'
                        ' target="_blank" rel="noopener" rel="noreferrer">'
                        "https://annuaire-entreprises.data.gouv.fr/etablissement/"
                        f"{siret}</a>"
                    )
                if field_name == "ville" and form_field:  # ville  est pas null
                    google_adresse = [
                        obj.nom_commercial
                        or acteur.nom_commercial
                        or obj.nom
                        or acteur.nom
                        or "",
                        obj.adresse or acteur.adresse,
                        obj.adresse_complement or acteur.adresse_complement,
                        obj.code_postal or acteur.code_postal,
                        obj.ville or acteur.ville,
                    ]
                    google_adresse = [
                        g.strip() for g in google_adresse if g and g.strip()
                    ]
                    form_field.help_text += (
                        '<br><a href="https://google.com/maps/search/'
                        f'{"+".join(google_adresse)}" target="_blank" rel="noopener"'
                        ' rel="noreferrer">Voir l\'adresse sur Google Maps</a>'
                    )

        return revision_acteur_form


class BasePropositionServiceAdmin(admin.GISModelAdmin):
    form = BasePropositionServiceForm


class BasePropositionServiceResource(resources.ModelResource):
    delete = fields.Field(widget=widgets.BooleanWidget())

    action = fields.Field(
        column_name="action_id",
        attribute="action",
        widget=widgets.ForeignKeyWidget(Action, field="code"),
    )
    acteur_service = fields.Field(
        column_name="acteur_service_id",
        attribute="acteur_service",
        widget=widgets.ForeignKeyWidget(ActeurService, field="code"),
    )
    sous_categories = fields.Field(
        column_name="sous_categories",
        attribute="sous_categories",
        widget=widgets.ManyToManyWidget(
            SousCategorieObjet, field="code", separator="|"
        ),
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


class DisplayedActeurResource(ActeurResource):
    class Meta:
        model = DisplayedActeur


class DisplayedActeurAdmin(import_export_admin.ExportMixin, BaseActeurAdmin):
    change_form_template = "admin/displayed_acteur/change_form.html"
    gis_widget = CustomOSMWidget
    inlines = [
        DisplayedPropositionServiceInline,
        DisplayedActeurLabelQualiteInline,
    ]
    modifiable = False
    resource_classes = [DisplayedActeurResource]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields if f.name != "location"]

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class CodeLibelleModelAdmin(admin.ModelAdmin):
    list_display = ("libelle", "code")
    search_fields = ["libelle", "code"]
    search_help_text = "Recherche sur le libellé ou le code"


admin.site.register(Acteur, ActeurAdmin)
admin.site.register(ActeurService, CodeLibelleModelAdmin)
admin.site.register(ActeurType, CodeLibelleModelAdmin)
admin.site.register(DisplayedActeur, DisplayedActeurAdmin)
admin.site.register(PropositionService, PropositionServiceAdmin)
admin.site.register(RevisionActeur, RevisionActeurAdmin)
admin.site.register(RevisionPropositionService, RevisionPropositionServiceAdmin)
admin.site.register(Source, CodeLibelleModelAdmin)
admin.site.register(LabelQualite, CodeLibelleModelAdmin)
