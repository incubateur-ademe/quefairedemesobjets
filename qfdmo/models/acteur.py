import json
import random
import string
from typing import Any

import opening_hours
import orjson
from django.contrib.gis.db import models
from django.core.files.images import get_image_dimensions
from django.forms import ValidationError, model_to_dict
from django.http import HttpRequest
from django.urls import reverse
from unidecode import unidecode

from qfdmo.models.action import Action, CachedDirectionAction
from qfdmo.models.categorie_objet import SousCategorieObjet
from qfdmo.models.utils import CodeAsNaturalKeyModel, NomAsNaturalKeyModel


class ActeurService(NomAsNaturalKeyModel):
    class Meta:
        verbose_name = "Service proposé"
        verbose_name_plural = "Services proposés"

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)
    libelle = models.CharField(max_length=255, blank=True, null=True)
    lvao_id = models.IntegerField(blank=True, null=True)
    actions = models.ManyToManyField(Action)

    def serialize(self):
        return model_to_dict(self, exclude=["actions"])


class ActeurStatus(models.TextChoices):
    ACTIF = "ACTIF", "actif"
    INACTIF = "INACTIF", "inactif"
    SUPPRIME = "SUPPRIME", "supprimé"


class ActeurType(NomAsNaturalKeyModel):
    _digital_acteur_type_id: int = 0

    class Meta:
        verbose_name = "Type d'acteur"
        verbose_name_plural = "Types d'acteur"

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)
    code_import = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        help_text=(
            "This field is used to manage the import of data."
            " Any update can break the import data process"
        ),
    )
    libelle = models.CharField(max_length=255, blank=False, null=False, default="?")
    lvao_id = models.IntegerField(blank=True, null=True)

    def serialize(self):
        return model_to_dict(self)

    @classmethod
    def get_digital_acteur_type_id(cls) -> int:
        if not cls._digital_acteur_type_id:
            cls._digital_acteur_type_id = cls.objects.get(nom="acteur digital").id
        return cls._digital_acteur_type_id


def validate_logo(value: Any):
    if value:
        # Check file size
        if value.size > 50 * 1024:
            raise ValidationError("Logo size should be less than 50 KB.")

        # Check file format
        width, height = get_image_dimensions(value)
        if width != 32 or height != 32:
            raise ValidationError("Logo dimensions should be 32x32 pixels.")


class Source(CodeAsNaturalKeyModel):
    class Meta:
        verbose_name = "Source de données"
        verbose_name_plural = "Sources de données"

    id = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=255, unique=True)
    code = models.CharField(
        max_length=255,
        unique=True,
        help_text=(
            "This field is used to manage the import of data."
            " Any update can break the import data process"
        ),
    )
    afficher = models.BooleanField(default=True)
    url = models.CharField(max_length=2048, blank=True, null=True)
    logo_file = models.ImageField(
        upload_to="logos", blank=True, null=True, validators=[validate_logo]
    )

    def serialize(self):
        return model_to_dict(self)


def validate_opening_hours(value):
    if value and not opening_hours.validate(value):
        raise ValidationError(
            ("%(value)s is not an valid opening hours"),
            params={"value": value},
        )


class LabelQualite(models.Model):
    class Meta:
        verbose_name = "Label qualité"
        verbose_name_plural = "Labels qualité"

    id = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=255, unique=True)
    code = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        help_text=(
            "This field is used to manage the import of data."
            " Any update can break the import data process"
        ),
    )
    afficher = models.BooleanField(default=True)
    bonus = models.BooleanField(
        default=False, help_text="Ouvre les droits à un bonus financier"
    )
    url = models.CharField(max_length=2048, blank=True, null=True)
    logo_file = models.ImageField(
        upload_to="logos", blank=True, null=True, validators=[validate_logo]
    )

    def __str__(self):
        return self.libelle


class BaseActeur(NomAsNaturalKeyModel):
    class Meta:
        abstract = True

    nom = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    identifiant_unique = models.CharField(
        max_length=255, unique=True, primary_key=True, blank=True
    )
    acteur_type = models.ForeignKey(ActeurType, on_delete=models.CASCADE)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    adresse_complement = models.CharField(max_length=255, blank=True, null=True)
    code_postal = models.CharField(max_length=10, blank=True, null=True)
    ville = models.CharField(max_length=255, blank=True, null=True)
    url = models.CharField(max_length=2048, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    location = models.PointField(blank=True, null=True)
    telephone = models.CharField(max_length=255, blank=True, null=True)
    nom_commercial = models.CharField(max_length=255, blank=True, null=True)
    nom_officiel = models.CharField(max_length=255, blank=True, null=True)
    # FIXME : Could be replace to a many-to-many relationship with a label table ?
    labels = models.ManyToManyField(LabelQualite)
    siret = models.CharField(max_length=14, blank=True, null=True)
    source = models.ForeignKey(Source, on_delete=models.CASCADE, blank=True, null=True)
    identifiant_externe = models.CharField(max_length=255, blank=True, null=True)
    statut = models.CharField(
        max_length=255, default=ActeurStatus.ACTIF, choices=ActeurStatus.choices
    )
    naf_principal = models.CharField(max_length=255, blank=True, null=True)
    commentaires = models.TextField(blank=True, null=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)
    horaires_osm = models.CharField(
        blank=True, null=True, validators=[validate_opening_hours]
    )
    horaires_description = models.TextField(blank=True, null=True)

    def share_url(self, request: HttpRequest, direction: str | None = None):
        # url = request.build_absolute_uri("")
        url = "http"
        if request.is_secure():
            url += "s"
        url += "://" + request.get_host()
        url += reverse("qfdmo:adresse_detail", args=[self.identifiant_unique])
        url += "?iframe"
        if direction:
            url += f"&direction={direction}"
        return url

    @property
    def latitude(self):
        return self.location.y if self.location else None

    @property
    def longitude(self):
        return self.location.x if self.location else None

    @property
    def libelle(self):
        return self.nom_commercial or self.nom

    @property
    def is_digital(self) -> bool:
        return self.acteur_type_id == ActeurType.get_digital_acteur_type_id()

    def serialize(self, format: None | str = None) -> dict | str:
        self_as_dict = model_to_dict(
            self,
            exclude=[
                "location",
                "proposition_services",
                "acteur_type",
                "source",
                "labels",
            ],
        )
        if self.acteur_type:
            self_as_dict["acteur_type"] = (
                self.acteur_type.serialize()
            )  # FIXME: to be cached or get only the name
        if self.source:
            self_as_dict["source"] = self.source.serialize()  # FIXME: to be cached
        if self.location:
            self_as_dict["location"] = json.loads(self.location.geojson)
        proposition_services = self.proposition_services.all()  # type: ignore
        self_as_dict["proposition_services"] = []
        for proposition_service in proposition_services:
            self_as_dict["proposition_services"].append(proposition_service.serialize())

        labels = self.labels.all()  # type: ignore
        self_as_dict["labels"] = []
        for proposition_service in labels:
            self_as_dict["labels"].append(proposition_service.serialize())

        if format == "json":
            return json.dumps(self_as_dict)
        return self_as_dict

    def acteur_services(self) -> list[str]:
        # FIXME: just for test (to be removed)
        # return ["relai d'acteur", "lieu trop cool", "ressourcerie", "boutique"]
        return sorted(
            list(
                set(
                    [
                        ps.acteur_service.libelle
                        for ps in self.proposition_services.all()
                        if ps.acteur_service.libelle
                    ]
                )
            )
        )

    def proposition_services_by_direction(self, direction: str | None = None):

        if direction:
            return self.proposition_services.filter(action__directions__nom=direction)
        return self.proposition_services.all()

    def has_label_reparacteur(self):
        return self.labels.filter(code="reparacteur").exists()


class Acteur(BaseActeur):
    class Meta:
        verbose_name = "ACTEUR de l'EC - IMPORTÉ"
        verbose_name_plural = "ACTEURS de l'EC - IMPORTÉ"

    def get_or_create_revision(self):
        # TODO : to be deprecated
        fields = model_to_dict(
            self,
            fields=[
                "statut",
            ],
        )
        (acteur, created) = RevisionActeur.objects.get_or_create(
            identifiant_unique=self.identifiant_unique, defaults=fields
        )
        if created:
            for proposition_service in self.proposition_services.all():  # type: ignore
                revision_proposition_service = (
                    RevisionPropositionService.objects.create(
                        acteur=acteur,
                        action_id=proposition_service.action_id,
                        acteur_service_id=proposition_service.acteur_service_id,
                    )
                )
                revision_proposition_service.sous_categories.add(
                    *proposition_service.sous_categories.all()
                )

        return acteur

    def clean_location(self):
        if self.location is None and self.acteur_type.nom != "acteur digital":
            raise ValidationError(
                {"location": "Location is mandatory when the actor is not digital"}
            )

    def save(self, *args, **kwargs):
        self.set_default_field_before_save()
        self.clean_location()
        return super().save(*args, **kwargs)

    def set_default_field_before_save(self):
        if not self.identifiant_externe:
            self.identifiant_externe = "".join(
                random.choices(string.ascii_uppercase, k=12)
            )
        if self.source is None:
            self.source = Source.objects.get_or_create(code="equipe")[0]
        if not self.identifiant_unique:
            source_stub = unidecode(self.source.code.lower()).replace(" ", "_")
            self.identifiant_unique = source_stub + "_" + str(self.identifiant_externe)


class RevisionActeur(BaseActeur):
    class Meta:
        verbose_name = "ACTEUR de l'EC - CORRIGÉ"
        verbose_name_plural = "ACTEURS de l'EC - CORRIGÉ"

    nom = models.CharField(max_length=255, blank=True, null=True)
    acteur_type = models.ForeignKey(
        ActeurType, on_delete=models.CASCADE, blank=True, null=True
    )

    def save(self, *args, **kwargs):
        self.set_default_fields_and_objects_before_save()
        return super().save(*args, **kwargs)

    def set_default_fields_and_objects_before_save(self):
        acteur_exists = True
        if not self.identifiant_unique or not Acteur.objects.filter(
            identifiant_unique=self.identifiant_unique
        ):
            acteur_exists = False
        if not acteur_exists:
            acteur = Acteur.objects.create(
                **model_to_dict(
                    self,
                    exclude=[
                        "id",
                        "acteur_type",
                        "source",
                        "proposition_services",
                        "labels",
                    ],
                ),
                acteur_type=(
                    self.acteur_type
                    if self.acteur_type
                    else ActeurType.objects.get(nom="commerce")
                ),
                source=self.source,
            )
            self.identifiant_unique = acteur.identifiant_unique
            self.identifiant_externe = acteur.identifiant_externe
            self.source = acteur.source

    def __str__(self):
        return self.nom or self.identifiant_unique


class DisplayedActeur(BaseActeur):
    class Meta:
        verbose_name = "ACTEUR de l'EC - AFFICHÉ"
        verbose_name_plural = "ACTEURS de l'EC - AFFICHÉ"

    def acteur_actions(self, direction=None):
        acteur_actions_by_direction = {}
        ps_action_ids = [
            ps.action_id for ps in self.proposition_services.all()  # type: ignore
        ]
        for d, actions in CachedDirectionAction.get_actions_by_direction().items():
            acteur_actions_by_direction[d] = sorted(
                [action for action in actions if action["id"] in ps_action_ids],
                key=lambda x: x["order"],
            )
        if direction:
            return acteur_actions_by_direction[direction]

        deduplicated_actions = {
            a["id"]: a
            for a in (
                acteur_actions_by_direction["jai"]
                + acteur_actions_by_direction["jecherche"]
            )
        }.values()
        sorted_actions = sorted(
            deduplicated_actions,
            key=lambda x: x["order"],
        )
        return sorted_actions

    def serialize(
        self,
        format: None | str = None,
        direction: str | None = None,
    ) -> dict | str:
        super_serialized = super().serialize(format=None)
        super_serialized["actions"] = self.acteur_actions(direction=direction)

        if format == "json":
            return json.dumps(super_serialized)
        return super_serialized

    def json_acteur_for_display(
        self, direction: str | None = None, action_list: str | None = None
    ) -> str:
        actions = self.acteur_actions(direction=direction)
        acteur_selected_actions = None
        if action_list:
            acteur_selected_actions = [
                a for a in actions if a["nom"] in action_list.split("|")
            ]

        return orjson.dumps(
            {
                "identifiant_unique": self.identifiant_unique,
                "location": orjson.loads(self.location.geojson),
                "actions": actions,
                "acteur_selected_action": (
                    acteur_selected_actions[0]
                    if acteur_selected_actions
                    else actions[0]
                ),
            }
        ).decode("utf-8")


class DisplayedActeurTemp(BaseActeur):

    labels = models.ManyToManyField(
        LabelQualite,
        through="ActeurLabelQualite",
    )

    class ActeurLabelQualite(models.Model):
        class Meta:
            db_table = "qfdmo_displayedacteurtemp_labels"

        id = models.BigAutoField(primary_key=True)
        acteur = models.ForeignKey(
            "DisplayedActeurTemp",
            on_delete=models.CASCADE,
            db_column="displayedacteur_id",
        )
        label = models.ForeignKey(
            LabelQualite,
            on_delete=models.CASCADE,
            db_column="labelqualite_id",
        )


class BasePropositionService(models.Model):
    class Meta:
        abstract = True

    id = models.AutoField(primary_key=True)
    action = models.ForeignKey(
        Action,
        on_delete=models.CASCADE,
        null=False,
    )
    acteur_service = models.ForeignKey(
        ActeurService,
        on_delete=models.CASCADE,
        null=False,
    )
    sous_categories = models.ManyToManyField(
        SousCategorieObjet,
    )

    def __str__(self):
        return f"{self.action.nom} - {self.acteur_service.nom}"

    def serialize(self):
        return {
            "action": self.action.serialize(),
            "acteur_service": self.acteur_service.serialize(),
            "sous_categories": [
                sous_categorie.serialize()
                for sous_categorie in self.sous_categories.all()
            ],
        }


class PropositionService(BasePropositionService):
    class Meta:
        verbose_name = "PROPOSITION DE SERVICE - IMPORTÉ"
        verbose_name_plural = "PROPOSITIONS DE SERVICE - IMPORTÉ"
        constraints = [
            models.UniqueConstraint(
                fields=["acteur", "action", "acteur_service"],
                name="ps_unique_by_acteur_action_service",
            )
        ]

    acteur = models.ForeignKey(
        Acteur,
        to_field="identifiant_unique",
        on_delete=models.CASCADE,
        null=False,
        related_name="proposition_services",
    )

    def __str__(self):
        return f"{self.acteur} - {super().__str__()}"


class RevisionPropositionService(BasePropositionService):
    class Meta:
        verbose_name = "PROPOSITION DE SERVICE - CORRIGÉ"
        verbose_name_plural = "PROPOSITIONS DE SERVICE - CORRIGÉ"
        constraints = [
            models.UniqueConstraint(
                fields=["acteur", "action", "acteur_service"],
                name="rps_unique_by_revisionacteur_action_service",
            )
        ]

    acteur = models.ForeignKey(
        RevisionActeur,
        to_field="identifiant_unique",
        on_delete=models.CASCADE,
        null=False,
        related_name="proposition_services",
    )

    def __str__(self):
        return f"{self.acteur} - {super().__str__()}"


class DisplayedPropositionService(BasePropositionService):
    class Meta:
        verbose_name = "Proposition de service - AFFICHÉ"
        verbose_name_plural = "Proposition de service - AFFICHÉ"

    acteur = models.ForeignKey(
        DisplayedActeur,
        on_delete=models.CASCADE,
        null=False,
        related_name="proposition_services",
    )


class DisplayedPropositionServiceTemp(BasePropositionService):
    acteur = models.ForeignKey(
        DisplayedActeurTemp,
        on_delete=models.CASCADE,
        null=False,
        related_name="proposition_services",
    )

    sous_categories = models.ManyToManyField(
        SousCategorieObjet,
        through="DisplayedPropositionServiceTempSousCategorie",
    )

    class DisplayedPropositionServiceTempSousCategorie(models.Model):
        class Meta:
            db_table = "qfdmo_displayedpropositionservicetemp_sous_categories"
            managed = False

        id = models.BigAutoField(primary_key=True)
        proposition_service = models.ForeignKey(
            "DisplayedPropositionServiceTemp",
            on_delete=models.CASCADE,
            db_column="displayedpropositionservice_id",
        )
        sous_categorie_objet = models.ForeignKey(
            SousCategorieObjet,
            on_delete=models.CASCADE,
            db_column="souscategorieobjet_id",
        )
