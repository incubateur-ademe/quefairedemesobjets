import logging
import random
import string
import uuid
from copy import deepcopy
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
from django.db.models import Case, Exists, Min, OuterRef, Q, Value, When
from django.db.models.functions import Now
from django.forms import ValidationError, model_to_dict
from django.http import HttpRequest
from django.urls import reverse
from django.utils.functional import cached_property
from unidecode import unidecode

from core.constants import DIGITAL_ACTEUR_CODE
from dags.sources.config.shared_constants import REPRISE_1POUR0, REPRISE_1POUR1
from qfdmo.models.action import Action, get_action_instances
from qfdmo.models.categorie_objet import SousCategorieObjet
from qfdmo.models.utils import (
    CodeAsNaturalKeyModel,
    NomAsNaturalKeyManager,
    NomAsNaturalKeyModel,
)
from qfdmo.validators import CodeValidator

logger = logging.getLogger(__name__)

DEFAULT_SOURCE_CODE = "Communauté Longue Vie Aux Objets"


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


class DataLicense(models.TextChoices):
    OPEN_LICENSE = "OPEN_LICENSE", "Licence Ouverte"
    ODBL = "ODBL", "ODBL"
    CC_BY_NC_SA = "CC_BY_NC_SA", "CC-BY-NC-SA"
    NO_LICENSE = "NO_LICENSE", "Pas de licence"


class ActeurPublicAccueilli(models.TextChoices):
    PROFESSIONNELS_ET_PARTICULIERS = (
        "Particuliers et professionnels",
        "Particuliers et professionnels",
    )
    PROFESSIONNELS = "Professionnels", "Professionnels"
    PARTICULIERS = "Particuliers", "Particuliers"
    AUCUN = "Aucun", "Aucun"


class ActeurReprise(models.TextChoices):
    UN_POUR_ZERO = REPRISE_1POUR0, "1 pour 0"
    UN_POUR_UN = REPRISE_1POUR1, "1 pour 1"


class ActeurType(CodeAsNaturalKeyModel):
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
        blank=False,
        null=False,
        help_text=(
            "Ce champ est utilisé lors de l'import de données, il ne doit pas être"
            " mis à jour sous peine de casser l'import de données"
        ),
        validators=[CodeValidator()],
    )
    afficher = models.BooleanField(default=True)
    url = models.CharField(max_length=2048, blank=True, null=True)
    logo_file = models.ImageField(
        upload_to="logos", blank=True, null=True, validators=[validate_logo]
    )
    licence = models.CharField(
        default=DataLicense.NO_LICENSE,
        choices=DataLicense,
        db_default=DataLicense.NO_LICENSE,
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
            self.filter(acteur_type__code=DIGITAL_ACTEUR_CODE)
            .annotate(min_action_order=Min("proposition_services__action__order"))
            .order_by("min_action_order", "?")
        )

    def physical(self):
        return self.exclude(acteur_type__code=DIGITAL_ACTEUR_CODE)

    def in_geojson(self, geojson):
        if not geojson:
            # TODO : test
            return self.physical()

        if type(geojson) is not list:
            geojson = [geojson]

        geometries = [GEOSGeometry(geojson) for geojson in geojson]
        query = Q()
        for geometry in geometries:
            query |= Q(location__within=geometry)

        return self.physical().filter(query).order_by("?")

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
    siren = models.CharField(max_length=9, blank=True, null=True)
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

    @property
    def change_url(self):
        return reverse(
            "admin:qfdmo_displayedacteur_change", args=[self.identifiant_unique]
        )

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
        return self.acteur_type.code == DIGITAL_ACTEUR_CODE

    @cached_property
    def sorted_proposition_services(self):
        proposition_services = (
            self.proposition_services.all()
            .prefetch_related("sous_categories")
            .select_related("action", "action__groupe_action")
        )
        order = ["action__groupe_action__order", "action__order"]

        if action_principale := self.action_principale:
            proposition_services = proposition_services.annotate(
                action_principale=Case(
                    When(action__id=action_principale.id, then=Value(0)),
                    default=Value(1),
                )
            )
            order = ["action_principale", *order]

        return proposition_services.order_by(*order)

    @cached_property
    def sorted_acteur_services_libelles(self) -> list[str]:
        return list(
            self.acteur_services.exclude(libelle=None)
            .order_by("libelle")
            .values_list("libelle", flat=True)
            .distinct()
        )

    @property
    def adresse_display(self):
        parts = []
        fields = ["adresse", "adresse_complement", "code_postal", "ville"]
        for field in fields:
            if part := getattr(self, field):
                parts.append(part)

        return ", ".join(parts)

    @cached_property
    def acteur_services_display(self):
        return ", ".join(self.sorted_acteur_services_libelles)

    @cached_property
    def modifie_le_display(self):
        return self.modifie_le.strftime("%d/%m/%Y")

    @cached_property
    def labels_enseigne_display(self):
        return self.labels_display.filter(type_enseigne=True)

    @cached_property
    def labels_without_enseigne_display(self):
        return self.labels_display.exclude(type_enseigne=True)

    @cached_property
    def labels_display(self):
        """
        On retourne une liste de labels qualité.
        Dans la plupart des cas on ne retournera qu'un label, une future évolution
        va intégrer la gestion des labels multiples.

        La spec suivie est la suivante :
            - Si l'acteur dispose du bonus réparation : on l'affiche
        """
        return self.labels.filter(afficher=True).order_by("-bonus", "type_enseigne")

    @cached_property
    def is_bonus_reparation(self):
        return self.labels.filter(afficher=True, bonus=True).exists()

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

        return revisionacteur

    def clean_location(self):
        if self.location is None and self.acteur_type.code != DIGITAL_ACTEUR_CODE:
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
            self.source = Source.objects.get_or_create(code=DEFAULT_SOURCE_CODE)[0]
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
        return self.pk and self.duplicats.exists()

    def save(self, *args, **kwargs):
        # OPTIMIZE: if we need to validate the main action in the service propositions
        # I guess it should be here
        acteur = self.set_default_fields_and_objects_before_save()
        self.full_clean()
        creating = self._state.adding  # Before calling save
        super_result = super().save(*args, **kwargs)
        if creating and acteur:
            for proposition_service in acteur.proposition_services.all():  # type: ignore
                revision_proposition_service = (
                    RevisionPropositionService.objects.create(
                        acteur=self,
                        action_id=proposition_service.action_id,
                    )
                )
                revision_proposition_service.sous_categories.add(
                    *proposition_service.sous_categories.all()
                )
            for label in acteur.labels.all():
                self.labels.add(label)
            for acteur_service in acteur.acteur_services.all():
                self.acteur_services.add(acteur_service)
        return super_result

    def save_as_parent(self, *args, **kwargs):
        """
        Won't create an Acteur instance
        """
        self.full_clean()
        return super().save(*args, **kwargs)

    def set_default_fields_and_objects_before_save(self) -> Acteur | None:
        if self.is_parent:
            return None

        default_acteur_fields = model_to_dict(
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
        )
        default_acteur_fields.update(
            {
                "acteur_type": self.acteur_type
                or ActeurType.objects.get(code="commerce"),
                "source": self.source,
                "action_principale": self.action_principale,
            }
        )

        (acteur, created) = Acteur.objects.get_or_create(
            identifiant_unique=self.identifiant_unique,
            defaults=default_acteur_fields,
        )
        if created:
            # Ici on ré-écrit les champs qui ont pu être généré automatiquement lors de
            # la création de l'Acteur
            self.identifiant_unique = acteur.identifiant_unique
            self.identifiant_externe = acteur.identifiant_externe
            self.source = acteur.source
        return acteur

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

    def duplicate(self):
        if self.is_parent:
            raise Exception("Impossible de dupliquer un acteur parent")

        revision_acteur = deepcopy(self)

        acteur = Acteur.objects.get(identifiant_unique=self.identifiant_unique)

        fields_to_reset = [
            "identifiant_unique",
            "identifiant_externe",
            "source",
        ]
        fields_to_ignore = [
            "labels",
            "acteur_services",
            "proposition_services",
            "parent",
        ]

        for field in fields_to_reset:
            setattr(revision_acteur, field, None)
        for field in revision_acteur._meta.fields:
            if (
                not getattr(revision_acteur, field.name)
                and field.name not in fields_to_reset
                and field.name not in fields_to_ignore
            ):
                setattr(revision_acteur, field.name, getattr(acteur, field.name))
        revision_acteur.save()
        revision_acteur.labels.set(self.labels.all())
        revision_acteur.acteur_services.set(self.acteur_services.all())

        # recreate proposition_services for the new revision_acteur
        for proposition_service in self.proposition_services.all():
            revision_proposition_service = revision_proposition_service = (
                RevisionPropositionService.objects.create(
                    acteur=revision_acteur,
                    action=proposition_service.action,
                )
            )
            revision_proposition_service.sous_categories.set(
                proposition_service.sous_categories.all()
            )
        return revision_acteur

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

    def get_absolute_url(self):
        return reverse("qfdmo:acteur-detail", args=[self.uuid])

    def acteur_actions(self, direction=None):
        ps_action_ids = list(
            {ps.action_id for ps in self.proposition_services.all()}  # type: ignore
        )
        # Cast needed because of the cache
        cached_action_instances = cast(
            List[Action], cache.get_or_set("_action_instances", get_action_instances)
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

        def sort_actions(a):
            if a == self.action_principale:
                return -1

            base_order = a.order or 0
            if carte and a.groupe_action:
                base_order += (a.groupe_action.order or 0) * 100
            return base_order

        actions = sorted(actions, key=sort_actions)

        acteur_dict = {
            "uuid": self.uuid,
            "location": orjson.loads(self.location.geojson),
        }

        if not actions:
            return orjson.dumps(acteur_dict).decode("utf-8")

        displayed_action = actions[0]

        if carte and displayed_action.groupe_action:
            displayed_action = displayed_action.groupe_action

        acteur_dict.update(icon=displayed_action.icon, couleur=displayed_action.couleur)

        if carte and displayed_action.code == "reparer":
            acteur_dict.update(
                bonus=getattr(self, "bonus", False),
                reparer=getattr(self, "reparer", False),
            )

        return orjson.dumps(acteur_dict).decode("utf-8")

    def get_share_url(self, request: HttpRequest, direction: str | None = None) -> str:
        protocol = "https" if request.is_secure() else "http"
        host = request.get_host()
        base_url = f"{protocol}://{host}{self.get_absolute_url()}"

        params = []
        if "carte" in request.GET:
            params.append("carte=1")
        elif "iframe" in request.GET:
            params.append("iframe=1")
        if direction:
            params.append(f"direction={direction}")
        return f"{base_url}?{'&'.join(params)}"

    @cached_property
    def should_display_adresse(self) -> bool:
        return not self.is_digital and bool(
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

    @cached_property
    def sous_categories_display(self):
        return ", ".join(
            self.sous_categories.order_by("libelle").values_list("libelle", flat=True)
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
