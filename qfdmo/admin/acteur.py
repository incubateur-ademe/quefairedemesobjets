from typing import Any, List

import orjson
from django import forms
from django.conf import settings
from django.contrib.gis import admin
from django.contrib.gis.forms.fields import PointField
from django.contrib.gis.geos import Point
from django.contrib.postgres.lookups import Unaccent
from django.db.models import Subquery
from django.db.models.functions import Lower
from django.forms import CharField
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from import_export import admin as import_export_admin
from import_export import fields, resources, widgets

from qfdmo.admin.widgets import CategorieChoiceWidget, SousCategorieChoiceWidget
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
    ActeurPublicAccueilli,
    ActeurStatus,
    DisplayedActeur,
    DisplayedPropositionService,
    LabelQualite,
)
from qfdmo.models.categorie_objet import CategorieObjet
from qfdmo.widgets import CustomOSMWidget


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

    filter_horizontal = [
        "sous_categories",
    ]


class RevisionPropositionServiceForm(BasePropositionServiceForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=CategorieObjet.objects.annotate(
            libelle_unaccent=Unaccent(Lower("libelle"))
        ).order_by("libelle_unaccent"),
        widget=CategorieChoiceWidget,
        required=False,
    )
    categories.widget.attrs.update(
        {
            "data-controller": "admin-categorie-widget",
            "data-action": "admin-categorie-widget#syncSousCategorie",
        }
    )

    class Meta:
        fields = "__all__"
        widgets = {"sous_categories": SousCategorieChoiceWidget}


class BasePropositionServiceInline(admin.TabularInline):
    form = BasePropositionServiceForm
    extra = 0
    fields = (
        "action",
        "sous_categories",
    )


class PropositionServiceInline(NotEditableInlineMixin, BasePropositionServiceInline):
    model = PropositionService


class RevisionPropositionServiceInline(BasePropositionServiceInline):
    model = RevisionPropositionService
    form = RevisionPropositionServiceForm
    fields = (
        "action",
        "categories",
        "sous_categories",
    )


class DisplayedPropositionServiceInline(
    NotEditableInlineMixin, BasePropositionServiceInline
):
    model = DisplayedPropositionService


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
        "siren",
        "identifiant_unique",
        "code_postal",
        "ville",
        "adresse",
        "modifie_le",
    )
    search_fields = [
        "code_postal",
        "identifiant_unique",
        "nom__unaccent",
        "siret",
        "siren",
        "ville",
    ]
    search_help_text = (
        "Recherche sur le nom, le code postal, la ville, le siret, le siren ou"
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
        "siren",
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
        "action_principale",
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
    limit = settings.DJANGO_IMPORT_EXPORT_LIMIT

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
        if "limit" in kwargs:
            self.limit = kwargs["limit"]
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
        if self.limit:
            return super().get_queryset()[: self.limit]
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


class RevisionActeurChildInline(NotEditableInlineMixin, admin.TabularInline):
    verbose_name = "Duplicat"
    model = RevisionActeur
    fk_name = "parent"
    fields = ["view_link", "statut"]
    readonly_fields = ["view_link", "statut"]
    can_delete = False
    extra = 0

    def view_link(self, obj):
        if obj.identifiant_unique:
            return format_html(
                '<a href="{}">{} ({})</a>',
                reverse(
                    "admin:qfdmo_revisionacteur_change", args=[obj.identifiant_unique]
                ),
                obj.nom,
                obj.identifiant_unique,
            )
        return None


class RevisionActeurAdmin(import_export_admin.ImportExportMixin, BaseActeurAdmin):
    change_form_template = "admin/revision_acteur/change_form.html"
    gis_widget = CustomOSMWidget
    inlines = []
    save_as = False

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["duplicate_instance"] = True
        return super().changeform_view(request, object_id, form_url, extra_context)

    def get_inline_instances(self, request, revision_acteur=None):
        inlines = []
        if revision_acteur and revision_acteur.is_parent:
            inlines.append(RevisionActeurChildInline(self.model, self.admin_site))
        else:
            inlines.append(
                RevisionPropositionServiceInline(self.model, self.admin_site)
            )
            inlines.append(
                RevisionActeurLabelQualiteInline(self.model, self.admin_site)
            )
        return inlines

    exclude = ["id"]
    resource_classes = [RevisionActeurResource]
    fields = list(BaseActeurAdmin.fields) + ["parent"]
    autocomplete_fields = ["parent"]

    # update readlonly fields following statut of object
    def get_readonly_fields(self, request, revision_acteur=None):
        if revision_acteur and revision_acteur.is_parent:
            return list(super().get_readonly_fields(request, revision_acteur)) + [
                "parent",
                "proposition_services",
                "acteur_services",
                "source",
                "labels",
            ]
        return super().get_readonly_fields(request, revision_acteur)

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )
        if "field_name" in request.GET and request.GET["field_name"] == "parent":
            queryset = queryset.filter(
                # filtrer les acteurs pour n'afficher que ceux qui sont déjà parents
                # identifiant_unique in select distinct(parent_id) from revisionacteur
                identifiant_unique__in=Subquery(
                    RevisionActeur.objects.filter(parent_id__isnull=False)
                    .values("parent_id")
                    .distinct()
                ),
                statut=ActeurStatus.ACTIF,
            )
        return queryset, use_distinct

    def response_change(self, request, revision_acteur):
        if "get_or_create_parent" in request.POST:
            # Cloner l'objet actuel
            parent = revision_acteur.parent or revision_acteur.create_parent()
            return HttpResponseRedirect(
                reverse("admin:qfdmo_revisionacteur_change", args=[parent.pk])
            )
        if "duplicate_instance" in request.POST:
            if not revision_acteur.parent:
                revision_acteur.create_parent()
            revision_acteur = revision_acteur.duplicate()
            return HttpResponseRedirect(
                reverse(
                    "admin:qfdmo_revisionacteur_change",
                    args=[revision_acteur.identifiant_unique],
                )
            )

        return super().response_change(request, revision_acteur)

    def get_form(
        self, request: Any, obj: Any | None = None, change: bool = False, **kwargs: Any
    ) -> Any:
        """
        Display Acteur fields value as help_text
        """
        revision_acteur_form = super().get_form(request, obj, change, **kwargs)
        if obj and obj.is_parent:
            return revision_acteur_form
        if obj and obj.identifiant_unique:
            acteur = Acteur.objects.get(identifiant_unique=obj.identifiant_unique)
            for field_name, form_field in revision_acteur_form.base_fields.items():
                if field_name == "parent":
                    continue
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
                    form_field.help_text = acteur.sorted_acteur_services_libelles

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
                    siren = obj.siren or siret[:9]
                    form_field.help_text += (
                        '<br>ENTREPRISE : <a href="https://'
                        f'annuaire-entreprises.data.gouv.fr/entreprise/{siren}"'
                        ' target="_blank" rel="noreferrer">'
                        f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}"
                        '</a><br>ETABLISSEMENT : <a href="https://'
                        f'annuaire-entreprises.data.gouv.fr/etablissement/{siret}"'
                        ' target="_blank" rel="noreferrer">'
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
                        f'{"+".join(google_adresse)}" target="_blank"'
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
        "acteur__siren",
    ]
    search_help_text = "Recherche sur le nom, le siret ou le siren de l'acteur"

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


class OpenSourceDisplayedActeurResource(resources.ModelResource):
    """
    Only used to export data to open-source in Koumoul
    """

    limit = 0
    offset = 0
    licenses = []

    def __init__(
        self, limit: int = 0, offset: int = 0, licenses: List[str] = [], **kwargs
    ):
        self.limit = limit
        self.offset = offset
        self.licenses = licenses
        super().__init__(**kwargs)

    uuid = fields.Field(column_name="Identifiant", attribute="uuid", readonly=True)
    sources = fields.Field(column_name="Paternité", attribute="sources", readonly=True)

    def dehydrate_sources(self, acteur):
        sources = ["Longue Vie Aux Objets", "ADEME"]
        acteur_sources = acteur.sources.all()
        if self.licenses:
            acteur_sources = acteur_sources.filter(licence__in=self.licenses)
        sources.extend([f"{source.libelle}" for source in acteur_sources])
        seen = set()
        deduplicated_sources = []
        for source in sources:
            if source not in seen:
                deduplicated_sources.append(source)
                seen.add(source)
        return "|".join(deduplicated_sources)

    nom = fields.Field(column_name="Nom", attribute="nom", readonly=True)
    nom_commercial = fields.Field(
        column_name="Nom commercial", attribute="nom_commercial", readonly=True
    )
    siren = fields.Field(column_name="SIREN", attribute="siren", readonly=True)
    siret = fields.Field(column_name="SIRET", attribute="siret", readonly=True)
    description = fields.Field(column_name="Description", attribute="description")
    acteur_type = fields.Field(
        column_name="Type d'acteur",
        attribute="acteur_type",
        widget=widgets.ForeignKeyWidget(ActeurType, field="code"),
        readonly=True,
    )
    url = fields.Field(column_name="Site web", attribute="url", readonly=True)
    telephone = fields.Field(attribute="telephone", column_name="Téléphone")

    def dehydrate_telephone(self, acteur):
        """
        Exclure les numéros de téléphone qui commencent pas 06 ou 07 pour ne pas avoir
        de soucis de mis en ligne d'informations personnelles (cf. RGPD)
        """
        telephone = acteur.telephone
        if telephone and (telephone.startswith("06") or telephone.startswith("07")):
            return None
        # filtrer les téléphones pour les acteur de la source carte-Eco
        if telephone and acteur.sources.filter(code="CartEco - ESS France").exists():
            return None

        return telephone

    adresse = fields.Field(column_name="Adresse", attribute="adresse", readonly=True)
    adresse_complement = fields.Field(
        column_name="Complément d'adresse",
        attribute="adresse_complement",
        readonly=True,
    )
    code_postal = fields.Field(
        column_name="Code postal", attribute="code_postal", readonly=True
    )
    ville = fields.Field(column_name="Ville", attribute="ville", readonly=True)
    latitude = fields.Field(column_name="latitude", attribute="latitude", readonly=True)
    longitude = fields.Field(
        column_name="longitude", attribute="longitude", readonly=True
    )
    labels = fields.Field(
        column_name="Qualités et labels",
        attribute="labels",
        widget=widgets.ManyToManyWidget(LabelQualite, field="code", separator="|"),
    )
    public_accueilli = fields.Field(
        column_name="Public accueilli",
        attribute="public_accueilli",
        readonly=True,
    )
    reprise = fields.Field(column_name="Reprise", attribute="reprise", readonly=True)
    exclusivite_de_reprisereparation = fields.Field(
        column_name="Exclusivité de reprise/réparation",
        attribute="exclusivite_de_reprisereparation",
        readonly=True,
    )
    uniquement_sur_rdv = fields.Field(
        column_name="Uniquement sur RDV", attribute="uniquement_sur_rdv", readonly=True
    )
    acteur_services = fields.Field(
        column_name="Type de services",
        attribute="acteur_services",
        widget=widgets.ManyToManyWidget(ActeurService, field="code", separator="|"),
        readonly=True,
    )
    propositions_services = fields.Field(
        column_name="Propositions de services",
        attribute="propositions_services",
        readonly=True,
    )

    def dehydrate_propositions_services(self, acteur):
        return orjson.dumps(
            [
                {
                    "action": ps.action.code,
                    "sous_categories": [sc.code for sc in ps.sous_categories.all()],
                }
                for ps in acteur.proposition_services.all()
            ]
        ).decode("utf-8")

    modifie_le = fields.Field(
        column_name="Date de dernière modification",
        attribute="modifie_le",
        readonly=True,
        widget=widgets.DateTimeWidget(format="%Y-%m-%d"),
    )

    def get_queryset(self):

        queryset = super().get_queryset()

        queryset = queryset.prefetch_related(
            "sources",
            "labels",
            "proposition_services__sous_categories",
            "proposition_services__action",
        )

        # Only Actif
        queryset = queryset.filter(
            statut=ActeurStatus.ACTIF,
        )
        # Exclude acteurs only professionals
        queryset = queryset.exclude(
            public_accueilli__in=[
                ActeurPublicAccueilli.AUCUN,
                ActeurPublicAccueilli.PROFESSIONNELS,
            ],
        )
        # filter les acteur qui on '_reparation_' dans le champ identifiant_unique
        queryset = queryset.exclude(
            identifiant_unique__icontains="_reparation_",
        )
        # Export only acteurs with expected licenses
        if self.licenses:
            queryset = queryset.filter(sources__licence__in=self.licenses)
        queryset = queryset.distinct()
        queryset = queryset.order_by("uuid")

        if self.limit:
            return queryset[self.offset : self.offset + self.limit]

        return queryset

    class Meta:
        model = DisplayedActeur
        fields = [
            "uuid",
            "sources",
            "nom",
            "nom_commercial",
            "siren",
            "siret",
            "description",
            "acteur_type",
            "url",
            "telephone",
            "adresse",
            "adresse_complement",
            "code_postal",
            "ville",
            "latitude",
            "longitude",
            "labels",
            "public_accueilli",
            "reprise",
            "exclusivite_de_reprisereparation",
            "uniquement_sur_rdv",
            "modifie_le",
            "acteur_services",
            "propositions_services",
        ]


class DisplayedActeurAdmin(import_export_admin.ExportMixin, BaseActeurAdmin):
    change_form_template = "admin/displayed_acteur/change_form.html"
    gis_widget = CustomOSMWidget
    base_fields = list(BaseActeurAdmin.fields)
    base_fields.remove("source")
    base_fields.insert(1, "sources")
    base_fields.insert(0, "uuid")
    readonly_fields = list(BaseActeurAdmin.readonly_fields)
    readonly_fields.insert(0, "uuid")
    fields = base_fields

    inlines = [
        DisplayedPropositionServiceInline,
        DisplayedActeurLabelQualiteInline,
    ]
    modifiable = False
    resource_classes = [DisplayedActeurResource]

    def get_readonly_fields(self, request, obj=None):
        if settings.DEBUG:
            return list(super().get_readonly_fields(request, obj))
        return [f.name for f in self.model._meta.fields if f.name != "location"]

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class CodeLibelleModelAdmin(admin.ModelAdmin):
    list_display = ("libelle", "code")
    search_fields = ["libelle", "code"]
    search_help_text = "Recherche sur le libellé ou le code"

    # le champ code ne doit pas être modifiable
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["code"]
        return []


admin.site.register(Acteur, ActeurAdmin)
admin.site.register(ActeurService, CodeLibelleModelAdmin)
admin.site.register(ActeurType, CodeLibelleModelAdmin)
admin.site.register(DisplayedActeur, DisplayedActeurAdmin)
admin.site.register(PropositionService, PropositionServiceAdmin)
admin.site.register(RevisionActeur, RevisionActeurAdmin)
admin.site.register(RevisionPropositionService, RevisionPropositionServiceAdmin)
admin.site.register(Source, CodeLibelleModelAdmin)
admin.site.register(LabelQualite, CodeLibelleModelAdmin)
