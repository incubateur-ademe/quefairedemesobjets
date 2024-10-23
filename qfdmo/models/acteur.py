import random
import string
import uuid
from typing import Any, List, cast

import opening_hours
import orjson
import shortuuid
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.geos.geometry import GEOSGeometry
from django.core.cache import cache
from django.core.files.images import get_image_dimensions
from django.db.models import Exists, Min, OuterRef
from django.db.models.functions import Now
from django.forms import ValidationError, model_to_dict
from django.http import HttpRequest
from django.urls import reverse
from unidecode import unidecode

from qfdmo.models.action import Action, get_action_instances
from qfdmo.models.categorie_objet import SousCategorieObjet
from qfdmo.models.utils import (
    CodeAsNaturalKeyModel,
    NomAsNaturalKeyManager,
    NomAsNaturalKeyModel,
)
from qfdmo.validators import CodeValidator


class ActeurService(CodeAsNaturalKeyModel):
    class Meta:
        ordering = ["libelle"]
        verbose_name = "Service proposé"
        verbose_name_plural = "Services proposés"

    id = models.AutoField(primary_key=True)
    code = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=False,
        help_text=(
            "Ce champ est utilisé lors de l'import de données, il ne doit pas être"
            " mis à jour sous peine de casser l'import de données"
        ),
        validators=[CodeValidator()],
    )
    libelle = models.CharField(max_length=255, blank=True, null=True)
    actions = models.ManyToManyField(Action)

    def __str__(self):
        return f"{self.libelle} ({self.code})"


class ActeurStatus(models.TextChoices):
    ACTIF = "ACTIF", "actif"
    INACTIF = "INACTIF", "inactif"
    SUPPRIME = "SUPPRIME", "supprimé"


class ActeurPublicAccueilli(models.TextChoices):
    PROFESSIONNELS_ET_PARTICULIERS = (
        "Particuliers et professionnels",
        "Particuliers et professionnels",
    )
    PROFESSIONNELS = "Professionnels", "Professionnels"
    PARTICULIERS = "Particuliers", "Particuliers"
    AUCUN = "Aucun", "Aucun"


class ActeurReprise(models.TextChoices):
    UN_POUR_ZERO = "1 pour 0", "1 pour 0"
    UN_POUR_UN = "1 pour 1", "1 pour 1"


class ActeurType(CodeAsNaturalKeyModel):
    _digital_acteur_type_id: int = 0

    class Meta:
        verbose_name = "Type d'acteur"
        verbose_name_plural = "Types d'acteur"

    id = models.AutoField(primary_key=True)
    code = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=False,
        help_text=(
            "Ce champ est utilisé lors de l'import de données, il ne doit pas être"
            " mis à jour sous peine de casser l'import de données"
        ),
        validators=[CodeValidator()],
    )
    libelle = models.CharField(max_length=255, blank=False, null=False, default="?")

    @classmethod
    def get_digital_acteur_type_id(cls) -> int:
        if not cls._digital_acteur_type_id:
            (digital_acteur_type, _) = cls.objects.get_or_create(code="acteur digital")
            cls._digital_acteur_type_id = digital_acteur_type.id
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
    libelle = models.CharField(max_length=255)
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
    type_enseigne = models.BooleanField(
        default=False,
        help_text="Ce label est affiché comme un type d'enseigne, ex : ESS",
    )
    url = models.CharField(max_length=2048, blank=True, null=True)
    logo_file = models.ImageField(
        upload_to="logos", blank=True, null=True, validators=[validate_logo]
    )

    def __str__(self):
        return self.libelle


class DisplayedActeurQuerySet(models.QuerySet):
    def with_reparer(self):
        proposition_service_reparer = DisplayedPropositionService.objects.filter(
            acteur=OuterRef("pk"), action__code="reparer"
        )
        return self.annotate(reparer=Exists(proposition_service_reparer))

    def with_bonus(self):
        bonus_label_qualite = LabelQualite.objects.filter(
            displayedacteur=OuterRef("pk"), bonus=True
        )
        return self.annotate(bonus=Exists(bonus_label_qualite))

    def digital(self):
        return (
            self.filter(acteur_type_id=ActeurType.get_digital_acteur_type_id())
            .annotate(min_action_order=Min("proposition_services__action__order"))
            .order_by("min_action_order", "?")
        )

    def physical(self):
        return self.exclude(acteur_type_id=ActeurType.get_digital_acteur_type_id())

    def in_geojson(self, geojson):
        if not geojson:
            # TODO : test
            return self.physical()

        geometry = GEOSGeometry(geojson)
        return self.physical().filter(location__within=geometry).order_by("?")

    def in_bbox(self, bbox):
        if not bbox:
            # TODO : test
            return self.physical()

        return (
            self.physical()
            .filter(location__within=Polygon.from_bbox(bbox))
            .order_by("?")
        )

    def from_center(self, longitude, latitude):
        reference_point = Point(float(longitude), float(latitude), srid=4326)
        distance_in_degrees = settings.DISTANCE_MAX / 111320

        return (
            self.physical()
            .annotate(distance=Distance("location", reference_point))
            .filter(
                location__dwithin=(
                    reference_point,
                    distance_in_degrees,
                )
            )
            .order_by("distance")
        )


class DisplayedActeurManager(NomAsNaturalKeyManager):
    def get_queryset(self):
        return DisplayedActeurQuerySet(self.model, using=self._db)


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
    labels = models.ManyToManyField(LabelQualite)
    acteur_services = models.ManyToManyField(ActeurService, blank=True)
    siret = models.CharField(max_length=14, blank=True, null=True)
    source = models.ForeignKey(Source, on_delete=models.CASCADE, blank=True, null=True)
    identifiant_externe = models.CharField(max_length=255, blank=True, null=True)
    statut = models.CharField(
        max_length=255,
        default=ActeurStatus.ACTIF,
        choices=ActeurStatus.choices,
        db_default=ActeurStatus.ACTIF,
    )
    naf_principal = models.CharField(max_length=255, blank=True, null=True)
    commentaires = models.TextField(blank=True, null=True)
    cree_le = models.DateTimeField(auto_now_add=True, db_default=Now())
    modifie_le = models.DateTimeField(auto_now=True, db_default=Now())
    horaires_osm = models.CharField(
        blank=True, null=True, validators=[validate_opening_hours]
    )
    horaires_description = models.TextField(blank=True, null=True)

    public_accueilli = models.CharField(
        max_length=255,
        choices=ActeurPublicAccueilli.choices,
        null=True,
        blank=True,
    )
    reprise = models.CharField(
        max_length=255,
        choices=ActeurReprise.choices,
        null=True,
        blank=True,
    )
    exclusivite_de_reprisereparation = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Exclusivité de reprise/réparation",
    )
    uniquement_sur_rdv = models.BooleanField(null=True, blank=True)
    action_principale = models.ForeignKey(
        Action,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    def get_share_url(self, request: HttpRequest, direction: str | None = None) -> str:
        protocol = "https" if request.is_secure() else "http"
        host = request.get_host()
        base_url = f"{protocol}://{host}"
        base_url += reverse("qfdmo:adresse_detail", args=[self.identifiant_unique])

        params = []
        if "carte" in request.GET:
            params.append("carte=1")
        elif "iframe" in request.GET:
            params.append("iframe=1")
        if direction:
            params.append(f"direction={direction}")
        return f"{base_url}?{'&'.join(params)}"

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

    def get_acteur_services(self) -> list[str]:
        return sorted(
            list(
                set(
                    [
                        acteur_service.libelle
                        for acteur_service in self.acteur_services.all()
                        if acteur_service.libelle
                    ]
                )
            )
        )

    def proposition_services_by_direction(self, direction: str | None = None):
        if direction:
            return self.proposition_services.filter(action__directions__code=direction)
        return self.proposition_services.all()

    def has_label_reparacteur(self):
        return self.labels.filter(code="reparacteur").exists()

    def _get_dict_for_clone(self):
        excluded_fields = [
            "identifiant_unique",
            "identifiant_externe",
            "proposition_services",
            "acteur_type",
            "acteur_services",
            "source",
            "labels",
        ]
        acteur_dict = model_to_dict(self, exclude=excluded_fields)
        acteur_dict["acteur_type"] = self.acteur_type
        return {k: v for k, v in acteur_dict.items() if v}


def clean_parent(parent):
    try:
        parent = RevisionActeur.objects.get(identifiant_unique=parent)
    except RevisionActeur.DoesNotExist:
        raise ValidationError("You can't define a Parent which does not exist.")

    if parent and parent.parent:
        raise ValidationError("You can't define a Parent which is already a duplicate.")


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
        (revisionacteur, created) = RevisionActeur.objects.get_or_create(
            identifiant_unique=self.identifiant_unique, defaults=fields
        )
        if created:
            for proposition_service in self.proposition_services.all():  # type: ignore
                revision_proposition_service = (
                    RevisionPropositionService.objects.create(
                        acteur=revisionacteur,
                        action_id=proposition_service.action_id,
                    )
                )
                revision_proposition_service.sous_categories.add(
                    *proposition_service.sous_categories.all()
                )
            for label in self.labels.all():
                revisionacteur.labels.add(label)
            for acteur_service in self.acteur_services.all():
                revisionacteur.acteur_services.add(acteur_service)

        return revisionacteur

    def clean_location(self):
        if self.location is None and self.acteur_type.code != "acteur digital":
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
    parent = models.ForeignKey(
        "self",
        verbose_name="Dédupliqué par",
        help_text="RevisonActeur «chapeau» utilisé pour dédupliquer cet acteur",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="duplicats",
        validators=[clean_parent],
    )

    @property
    def is_parent(self):
        return self.duplicats.exists()

    def save(self, *args, **kwargs):
        # OPTIMIZE: if we need to validate the main action in the service propositions
        # I guess it should be here
        self.set_default_fields_and_objects_before_save()
        self.full_clean()
        return super().save(*args, **kwargs)

    def save_as_parent(self, *args, **kwargs):
        """
        Won't create an Acteur instance
        """
        self.full_clean()
        return super().save(*args, **kwargs)

    def set_default_fields_and_objects_before_save(self):
        if self.is_parent:
            return
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
                        "action_principale",
                        "proposition_services",
                        "acteur_services",
                        "labels",
                        "parent",
                        "is_parent",
                    ],
                ),
                acteur_type=(
                    self.acteur_type
                    if self.acteur_type
                    else ActeurType.objects.get(code="commerce")
                ),
                source=self.source,
                action_principale=self.action_principale,
            )
            self.identifiant_unique = acteur.identifiant_unique
            self.identifiant_externe = acteur.identifiant_externe
            self.source = acteur.source

    def create_parent(self):
        acteur = Acteur.objects.get(pk=self.pk)
        acteur_dict = acteur._get_dict_for_clone()
        self_dict = self._get_dict_for_clone()

        revision_acteur_parent = RevisionActeur(
            identifiant_unique=uuid.uuid4(),
            **(acteur_dict | self_dict),
        )
        revision_acteur_parent.save_as_parent()

        self.parent = revision_acteur_parent
        self.save()
        return revision_acteur_parent

    def __str__(self):
        return (
            f"{self.nom} ({self.identifiant_unique})"
            if self.nom
            else self.identifiant_unique
        )


class DisplayedActeur(BaseActeur):
    objects = DisplayedActeurManager()

    class Meta:
        verbose_name = "ACTEUR de l'EC - AFFICHÉ"
        verbose_name_plural = "ACTEURS de l'EC - AFFICHÉ"

    uuid = models.CharField(max_length=255, default=shortuuid.uuid, editable=False)

    # Table name qfdmo_displayedacteur_sources
    sources = models.ManyToManyField(
        Source,
        blank=True,
        related_name="displayed_acteurs",
    )

    def acteur_actions(self, direction=None):
        ps_action_ids = list(
            {ps.action_id for ps in self.proposition_services.all()}  # type: ignore
        )
        # Cast needed because of the cache
        cached_action_instances = cast(
            List[Action], cache.get_or_set("action_instances", get_action_instances)
        )
        return [
            action
            for action in cached_action_instances
            if (not direction or direction in [d.code for d in action.directions.all()])
            and action.id in ps_action_ids
        ]

    def json_acteur_for_display(
        self,
        direction: str | None = None,
        action_list: str | None = None,
        carte: bool = False,
    ) -> str:
        actions = self.acteur_actions(direction=direction)

        if action_list:
            actions = [a for a in actions if a.code in action_list.split("|")]

        # sort actions
        def sort_key(a):
            if a == self.action_principale:
                return -1

            if carte:
                return (a.order or 0) + (
                    a.groupe_action.order
                    if a.groupe_action and a.groupe_action.order
                    else 0
                ) * 100

            return a.order or 0

        actions = sorted(actions, key=sort_key)

        acteur_dict = {
            "identifiant_unique": self.identifiant_unique,
            "location": orjson.loads(self.location.geojson),
        }

        displayed_action = actions[0] if actions else None
        if displayed_action:
            if carte and (groupe_action := displayed_action.groupe_action):
                displayed_action = groupe_action

            if displayed_action.code == "reparer":
                acteur_dict.update(
                    bonus=getattr(self, "bonus", False),
                    reparer=getattr(self, "reparer", False),
                )

            acteur_dict.update(
                icon=displayed_action.icon, couleur=displayed_action.couleur
            )

        return orjson.dumps(acteur_dict).decode("utf-8")

    def display_postal_address(self) -> bool:
        return bool(
            self.adresse or self.adresse_complement or self.code_postal or self.ville
        )


class DisplayedActeurTemp(BaseActeur):

    uuid = models.CharField(max_length=255, default=shortuuid.uuid, editable=False)

    labels = models.ManyToManyField(
        LabelQualite,
        through="ActeurLabelQualite",
    )

    acteur_services = models.ManyToManyField(
        ActeurService,
        blank=True,
        through="ActeurActeurService",
    )

    # Table name qfdmo_displayedacteurtemp_sources
    sources = models.ManyToManyField(
        Source,
        blank=True,
        through="DisplayedActeurTempSource",
        related_name="displayed_acteur_temps",
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

    class ActeurActeurService(models.Model):
        class Meta:
            db_table = "qfdmo_displayedacteurtemp_acteur_services"

        id = models.BigAutoField(primary_key=True)
        acteur = models.ForeignKey(
            "DisplayedActeurTemp",
            on_delete=models.CASCADE,
            db_column="displayedacteur_id",
        )
        acteur_service = models.ForeignKey(
            ActeurService,
            on_delete=models.CASCADE,
            db_column="acteurservice_id",
        )

    class DisplayedActeurTempSource(models.Model):
        class Meta:
            db_table = "qfdmo_displayedacteurtemp_sources"
            unique_together = ("acteur_id", "source_id")

        id = models.AutoField(primary_key=True)
        acteur = models.ForeignKey(
            "DisplayedActeurTemp",
            on_delete=models.CASCADE,
            db_column="displayedacteur_id",
        )
        source = models.ForeignKey(
            Source,
            on_delete=models.CASCADE,
            related_name="source_id",
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
    sous_categories = models.ManyToManyField(
        SousCategorieObjet,
    )

    def __str__(self):
        return f"{self.action.code}"


class PropositionService(BasePropositionService):
    class Meta:
        verbose_name = "PROPOSITION DE SERVICE - IMPORTÉ"
        verbose_name_plural = "PROPOSITIONS DE SERVICE - IMPORTÉ"
        constraints = [
            models.UniqueConstraint(
                fields=["acteur", "action"],
                name="ps_unique_by_acteur",
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
                fields=["acteur", "action"],
                name="rps_unique_by_revisionacteur",
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
