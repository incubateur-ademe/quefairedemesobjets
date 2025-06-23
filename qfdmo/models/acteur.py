import json
import logging
import random
import re
import string
import uuid
from copy import deepcopy
from typing import Any, List, cast

import opening_hours
import orjson
import shortuuid
from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.geos.geometry import GEOSGeometry
from django.core.cache import cache
from django.core.files.images import get_image_dimensions
from django.db.models import (
    Case,
    CheckConstraint,
    Count,
    Exists,
    Min,
    OuterRef,
    Q,
    Value,
    When,
)
from django.forms import ValidationError, model_to_dict
from django.http import HttpRequest
from django.urls import reverse
from django.utils.functional import cached_property
from unidecode import unidecode

from core.constants import DIGITAL_ACTEUR_CODE
from core.models.mixin import TimestampedModel
from core.utils import LazyEncoder
from core.validators import EmptyEmailValidator
from dags.sources.config.shared_constants import (
    EMPTY_ACTEUR_FIELD,
    REPRISE_1POUR0,
    REPRISE_1POUR1,
)
from qfdmo.models.action import Action, get_action_instances
from qfdmo.models.categorie_objet import SousCategorieObjet

# Explicit imports from models config, action, categories, utils
# and not from qfdmo.models are required here to prevent circular
# dependency import error.
from qfdmo.models.config import CarteConfig, GroupeActionConfig
from qfdmo.models.utils import (
    CodeAsNaturalKeyModel,
    string_remove_substring_via_normalization,
)
from qfdmo.validators import CodeValidator

logger = logging.getLogger(__name__)

DEFAULT_SOURCE_CODE = "communautelvao"


class ActeurService(CodeAsNaturalKeyModel):
    class Meta:
        ordering = ["libelle"]
        verbose_name = "Service proposé"
        verbose_name_plural = "Services proposés"
        constraints = [
            CheckConstraint(
                check=Q(code__regex=CodeValidator.regex),
                name="acteur_service_code_format",
            ),
        ]

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
    UNKNOWN = "", ""


class ActeurReprise(models.TextChoices):
    UN_POUR_ZERO = REPRISE_1POUR0, "1 pour 0"
    UN_POUR_UN = REPRISE_1POUR1, "1 pour 1"
    UNKNOWN = "", ""


class ActeurType(CodeAsNaturalKeyModel):
    class Meta:
        verbose_name = "Type d'acteur"
        verbose_name_plural = "Types d'acteur"
        constraints = [
            CheckConstraint(
                check=Q(code__regex=CodeValidator.regex), name="acteur_type_code_format"
            ),
        ]

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
        constraints = [
            CheckConstraint(
                check=Q(code__regex=CodeValidator.regex), name="source_code_format"
            ),
        ]

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

    @property
    def logo_file_absolute_url(self) -> str:
        if not self.logo_file:
            return ""

        return f"{settings.BASE_URL}{self.logo_file.url}"


def validate_opening_hours(value):
    if value and not opening_hours.validate(value):
        raise ValidationError(
            ("%(value)s is not an valid opening hours"),
            params={"value": value},
        )


class LabelQualite(CodeAsNaturalKeyModel):
    class Meta:
        verbose_name = "Label qualité"
        verbose_name_plural = "Labels qualité"

    id = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=255, unique=True)
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


class DisplayedActeurManager(models.Manager):
    def get_queryset(self):
        return DisplayedActeurQuerySet(self.model, using=self._db)

    def get_by_natural_key(self, uuid):
        return self.get(
            uuid=uuid,
        )


class BaseActeur(TimestampedModel):
    class Meta:
        abstract = True

    nom = models.CharField(max_length=255, blank=False, null=False, db_index=True)
    description = models.TextField(blank=True, default="", db_default="")
    identifiant_unique = models.CharField(
        max_length=255, unique=True, primary_key=True, blank=True, db_index=True
    )
    acteur_type = models.ForeignKey(ActeurType, on_delete=models.CASCADE)
    adresse = models.CharField(max_length=255, blank=True, default="", db_default="")
    adresse_complement = models.CharField(
        max_length=255, blank=True, default="", db_default=""
    )
    code_postal = models.CharField(
        max_length=10, blank=True, default="", db_default="", db_index=True
    )
    ville = models.CharField(
        max_length=255, blank=True, default="", db_default="", db_index=True
    )
    url = models.CharField(max_length=2048, blank=True, default="", db_default="")
    email = models.EmailField(blank=True, default="", db_default="")
    location = models.PointField(blank=True, null=True)
    telephone = models.CharField(max_length=255, blank=True, default="", db_default="")
    nom_commercial = models.CharField(
        max_length=255, blank=True, default="", db_default=""
    )
    nom_officiel = models.CharField(
        max_length=255, blank=True, default="", db_default=""
    )
    labels = models.ManyToManyField(LabelQualite)
    acteur_services = models.ManyToManyField(ActeurService, blank=True)
    siren = models.CharField(
        max_length=9, blank=True, default="", db_default="", db_index=True
    )
    siret = models.CharField(
        max_length=14, blank=True, default="", db_default="", db_index=True
    )
    # To backfill SIRET status into our DB from AE and avoid having to evaluate
    # AE's DB at runtime (which has 40M rows), also helping with Django admin info
    siret_is_closed = models.BooleanField(
        default=None,  # by default we can't assume a SIRET is opened
        null=True,
        blank=True,
        verbose_name="SIRET fermé",
        help_text="Indique si le SIRET est fermé ou non dans l'Annuaire Entreprises",
    )
    source = models.ForeignKey(Source, on_delete=models.CASCADE, blank=True, null=True)
    identifiant_externe = models.CharField(
        max_length=255, blank=True, default="", db_default=""
    )
    statut = models.CharField(
        max_length=255,
        default=ActeurStatus.ACTIF,
        choices=ActeurStatus.choices,
        db_default=ActeurStatus.ACTIF,
    )
    naf_principal = models.CharField(
        max_length=255, blank=True, default="", db_default=""
    )
    commentaires = models.TextField(blank=True, default="", db_default="")
    horaires_osm = models.CharField(
        blank=True, default="", db_default="", validators=[validate_opening_hours]
    )
    horaires_description = models.TextField(blank=True, default="", db_default="")

    public_accueilli = models.CharField(
        max_length=255,
        choices=ActeurPublicAccueilli.choices,
        default=ActeurPublicAccueilli.UNKNOWN,
        blank=True,
    )
    reprise = models.CharField(
        max_length=255,
        choices=ActeurReprise.choices,
        default=ActeurReprise.UNKNOWN,
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

    @property
    def numero_et_complement_de_rue(self) -> str | None:
        """Extrait le numéro de rue (et complément si présent)
        d'une adresse. Le complément est important car il peut
        servir à distinguer des adresses différentes lors de
        tâche telle le clustering (ex: "1" vs. "1 b").

        TODO: il y a surement des améliorations à apporter,
        notamment en étendant les différents possibilités de
        compléments, mais avec le risque d'effets de bord.

        Par exemple si on inclus les compléments de [a-z],
        risque de confondre z de "15 z.i." (zone industrielle)
        avec le complément.

        La fonction est une 1ère version conservatrice qu'il
        faudra revisiter données à l'appui, et potentiellement
        basculer en LLM en background processing si c'est trop
        complexe à gérer
        """
        adr = self.adresse
        if not adr:
            return None
        # Mise en miniscule pour simplifier les regex sachant qu'on
        # voulait le faire au final pour plus d'uniformité
        match = re.match(r"^[\s]*([\d]+ ?(?:bis|a|b|c)?)\b", adr.lower())
        if not match:
            return None

        # On essaye de faire un peu de normalisation en
        # séparant le numéro du complément
        result = match.group(0).strip()
        match = re.search(r"(\d+)([a-z]+)", result)
        if match:
            result = f"{match.group(1)} {match.group(2)}"
        # Remplacement du bis en b au cas où on a les 2 versions
        # dans la data
        return result.replace("bis", "b")

    @property
    def code_departement(self) -> str | None:
        """Extrait le code départemental du code postal"""
        cp = self.code_postal
        if not cp:
            return None
        cp = str(cp).strip()
        return None if not cp or len(cp) != 5 else cp[:2]

    @property
    def combine_adresses(self) -> str | None:
        """Combine les valeurs de tous les champs adresses,
        utile notamment pour le clustering car les sources mélangent
        un peut tout à travers ces champs et on veut tout regrouper
        pour augmenter les chances de similarité (sachant qu'on
        peut utiliser à posteriori fonctions de normalisation qui suppriment
        les mots en doublons et augmentent encore la similarité)"""
        result = (
            f"{(self.adresse or '').strip()} {(self.adresse_complement or '').strip()}"
        ).strip()
        return result or None

    @property
    def nom_sans_combine_adresses(self) -> str | None:
        """Retourne le nom sans les mots présents
        dans l'adresse ou le complément de rue, ceci
        pour faciliter le clustering quand un nom répète
        des éléments de l'adresse ce qui vient baisser le
        score de similarité.

        Si après suppression de l'adresse/complément
        il ne reste plus rien, on retourne None ce qui
        permet à ce champ d'être utilisé dans les
        critères d'inclusion/exclusion
        """
        return string_remove_substring_via_normalization(
            self.nom, self.combine_adresses
        )

    @property
    def combine_noms(self) -> str | None:
        """Même idée que combine_adresses mais pour les noms"""
        result = (
            (self.nom or "").strip()
            + " "
            + (self.nom_commercial or "").strip()
            + " "
            + (self.nom_officiel or "").strip()
        ).strip()
        return result or None

    @property
    def nom_sans_ville(self) -> str | None:
        """Retourne le nom sans la ville pour faciliter le clustering
        ex: DECATHLON {VILLE} -> DECATHLON. Pour étendre la portée
        de la fonction on passe par un état normalisé à la volée, mais
        au final on retourne un nom construit à partir de l'original"""
        return string_remove_substring_via_normalization(self.nom, self.ville)

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

    @classmethod
    def get_fields_for_clone(cls):
        return {field.name for field in cls._meta.get_fields()} - {
            "identifiant_unique",
            "identifiant_externe",
            "proposition_services",
            "acteur_services",
            "labels",
        }

    def commentaires_ajouter(self, added):
        """Historically this field has been defined as TextField
        but has contained a mix of free text and JSON data, hence
        method to help append data in a JSON format"""
        existing = self.commentaires

        # If empty we overwrite
        if existing is None or existing.strip() == "":
            self.commentaires = json.dumps([{"message": added}])
        else:
            try:
                # If not empty, trying to parse as JSON
                existing_data = json.loads(existing)
                if not isinstance(existing_data, list):
                    raise NotImplementedError(
                        "Cas de commentaires JSON non-liste pas prévu"
                    )
            except (json.JSONDecodeError, ValueError):
                # If existing not JSON we turn it into a list
                existing_data = [{"message": existing}]

            # Appending new data
            existing_data.append({"message": added})
            self.commentaires = json.dumps(existing_data)

        self.save()

    def instance_copy(
        self,
        overriden_fields={
            "identifiant_unique": None,
            "identifiant_externe": None,
            "source": None,
        },
    ):
        if isinstance(self, RevisionActeur) and self.is_parent:
            raise Exception("Impossible de dupliquer un acteur parent")

        if isinstance(self, RevisionActeur):
            acteur = Acteur.objects.get(identifiant_unique=self.identifiant_unique)
            acteur.instance_copy(overriden_fields=overriden_fields)

        new_instance = deepcopy(self)

        for field, value in overriden_fields.items():
            setattr(new_instance, field, value)

        new_instance.save()
        new_instance.labels.set(self.labels.all())
        new_instance.acteur_services.set(self.acteur_services.all())

        # recreate proposition_services for the new revision_acteur
        for proposition_service in self.proposition_services.all():
            new_proposition_service = proposition_service.__class__.objects.create(
                acteur=new_instance,
                action=proposition_service.action,
            )
            new_proposition_service.sous_categories.set(
                proposition_service.sous_categories.all()
            )
        return new_instance

    def _generate_identifiant_externe_if_missing(self):
        if not self.identifiant_externe:
            self.identifiant_externe = "".join(
                random.choices(string.ascii_uppercase, k=12)
            )

    def generate_source_if_missing(self):
        if self.source is None:
            self.source = Source.objects.get_or_create(code=DEFAULT_SOURCE_CODE)[0]

    def generate_identifiant_unique_if_missing(self):
        if not self.identifiant_unique:
            source_stub = unidecode(self.source.code.lower()).replace(" ", "_")
            self.identifiant_unique = source_stub + "_" + str(self.identifiant_externe)

    def __str__(self):
        return self.nom


def clean_parent(parent):
    try:
        parent = RevisionActeur.objects.get(identifiant_unique=parent)
    except RevisionActeur.DoesNotExist:
        raise ValidationError("You can't define a Parent which does not exist.")

    if parent and parent.parent:
        raise ValidationError("You can't define a Parent which is already a duplicate.")


class Acteur(BaseActeur):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source_id", "identifiant_externe"],
                condition=Q(statut=ActeurStatus.ACTIF),
                name="acteur_unique_by_source_and_external_id",
            )
        ]

        verbose_name = "ACTEUR de l'EC - IMPORTÉ"
        verbose_name_plural = "ACTEURS de l'EC - IMPORTÉ"

    @property
    def change_url(self):
        # quote() taken from django source
        # https://github.com/django/django/blob/6cfe00ee438111af38f1e414bd01976e23b39715/django/contrib/admin/models.py#L243
        return reverse(
            "admin:qfdmo_acteur_change", args=[quote(self.identifiant_unique)]
        )

    def get_or_create_revision(self):
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
        self._generate_identifiant_externe_if_missing()
        self.generate_source_if_missing()
        self.generate_identifiant_unique_if_missing()


# TODO: améliorer ci-dessous avec un gestionnaire de cache
# pour l'ensemble des propriétés calculées de type enfants/parents,
# y inclure la refacto de is_parent
PARENTS_CACHE = None


def parents_cache_get():
    global PARENTS_CACHE
    if PARENTS_CACHE is None:
        PARENTS_CACHE = {
            "nombre_enfants": dict(
                RevisionActeur.objects.filter(parent__isnull=False)
                .values_list("parent")
                .annotate(count=Count("identifiant_unique"))
            )
        }
    return PARENTS_CACHE


def parents_cache_invalidate():
    global PARENTS_CACHE
    PARENTS_CACHE = None


class RevisionActeur(BaseActeur):
    parent_model_name = "RevisionActeurParent"

    class Meta:
        verbose_name = "ACTEUR de l'EC - CORRIGÉ"
        verbose_name_plural = "ACTEURS de l'EC - CORRIGÉ"

    parent = models.ForeignKey(
        "RevisionActeurParent",
        verbose_name="Dédupliqué par",
        help_text="RevisionActeur «chapeau» utilisé pour dédupliquer cet acteur",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="duplicats",
        validators=[clean_parent],
    )
    parent_reason = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_default="",
        help_text="Raison du rattachement au parent",
    )

    @property
    def is_parent(self):
        return self.pk and self.duplicats.exists()

    nom = models.CharField(max_length=255, blank=True, default="", db_default="")
    acteur_type = models.ForeignKey(
        ActeurType, on_delete=models.CASCADE, blank=True, null=True
    )
    email = models.CharField(
        max_length=254,
        blank=True,
        default="",
        db_default="",
        validators=[EmptyEmailValidator()],
    )

    @property
    def change_url(self):
        return reverse(
            "admin:qfdmo_revisionacteur_change", args=[quote(self.identifiant_unique)]
        )

    @property
    def nombre_enfants(self) -> int:
        """Calcul le nombre d'enfants dont le parent_id
        pointent vers l'identifiant_unique de cet acteur"""
        return parents_cache_get()["nombre_enfants"].get(self.identifiant_unique, 0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_parent = self.parent

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

        if self.parent != self._original_parent and self._original_parent:
            if not self._original_parent.is_parent:
                self._original_parent.delete()

        # Dès qu'on fait des changements de révisions, quels qu'ils soient,
        # on force le recalcul du nombre d'enfants
        # TODO: améliorer cette logique en:
        # - centralisant toutes les propriétés calculés enfants/parents dans 1 cache
        # - en invalidant le cache uniquement si changements impactants ci-dessus
        parents_cache_invalidate()
        return super_result

    def save_as_parent(self, *args, **kwargs):
        """
        Won't create an Acteur instance
        """
        self.source = None
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
                "parent_reason",
                "is_parent",
            ],
        )

        default_acteur_fields = {
            k: "" if v == EMPTY_ACTEUR_FIELD else v
            for k, v in default_acteur_fields.items()
        }

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

        computed_fields = {
            field: getattr(self, field) or getattr(acteur, field)
            for field in Acteur.get_fields_for_clone()
        }

        revision_acteur_parent = RevisionActeur(
            identifiant_unique=uuid.uuid4(),
            **computed_fields,
        )
        revision_acteur_parent.save_as_parent()

        self.parent = revision_acteur_parent
        self.save()
        return revision_acteur_parent

    def duplicate(
        self,
        fields_to_reset={
            "identifiant_unique": None,
            "identifiant_externe": None,
            "source": None,
        },
    ):
        if self.is_parent:
            raise Exception("Impossible de dupliquer un acteur parent")

        revision_acteur = deepcopy(self)

        acteur = Acteur.objects.get(identifiant_unique=self.identifiant_unique)

        fields_to_ignore = [
            "labels",
            "acteur_services",
            "proposition_services",
            "parent",
            "parent_reason",
        ]

        for field, value in fields_to_reset.items():
            setattr(revision_acteur, field, value)
        for field in revision_acteur._meta.fields:
            if (
                not getattr(revision_acteur, field.name)
                and field.name not in fields_to_reset.keys()
                and field.name not in fields_to_ignore
            ):
                setattr(revision_acteur, field.name, getattr(acteur, field.name))
        revision_acteur.save()
        revision_acteur.labels.set(self.labels.all())
        revision_acteur.acteur_services.set(self.acteur_services.all())

        # recreate proposition_services for the new revision_acteur
        for proposition_service in self.proposition_services.all():
            revision_proposition_service = RevisionPropositionService.objects.create(
                acteur=revision_acteur,
                action=proposition_service.action,
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


class RevisionActeurParent(RevisionActeur):
    class Meta:
        proxy = True
        verbose_name = "Parent"
        verbose_name_plural = "Parents"


"""
Model to display all acteurs in admin
"""


class VueActeur(BaseActeur):
    class Meta:
        managed = False
        verbose_name = "ACTEUR de l'EC - Vue sur l'acteur"
        verbose_name_plural = "ACTEURS de l'EC - Vues sur tous les acteurs"

    uuid = models.CharField(max_length=255, default=shortuuid.uuid, editable=False)

    parent = models.ForeignKey(
        "self",
        verbose_name="Dédupliqué par",
        help_text="Acteur «chapeau» utilisé pour dédupliquer cet acteur",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="duplicats",
        validators=[clean_parent],
    )

    @property
    def is_parent(self):
        return self.pk and self.duplicats.exists()


class DisplayedActeur(BaseActeur):
    objects = DisplayedActeurManager()

    def natural_key(self):
        return (self.uuid,)

    class Meta:
        verbose_name = "ACTEUR de l'EC - AFFICHÉ"
        verbose_name_plural = "ACTEURS de l'EC - AFFICHÉ"

    uuid = models.CharField(
        max_length=255, default=shortuuid.uuid, editable=False, db_index=True
    )

    # Table name qfdmo_displayedacteur_sources
    sources = models.ManyToManyField(
        Source,
        blank=True,
        related_name="displayed_acteurs",
    )

    @property
    def change_url(self):
        return reverse(
            "admin:qfdmo_displayedacteur_change", args=[quote(self.identifiant_unique)]
        )

    # La propriété au sein du Displayed se base sur Revision
    # car c'est la seule façon de récupérer les enfants (n'existe pas
    # dans Displayed) car on en a besoin pour le clustering (fonction
    # qui se nourrit de la table Displayed, et on a pas envie de complexifier
    # encore davantage le code de clustering)
    # TODO: il faudrait dégager la table Displayed, en faire une vue, pour de
    # fait avoir 1 seul table d'état (revision) et donc on aurait plus ces soucis
    # de devoir piocher à droit/gauche pour reconstruire un état cohérent
    @property
    def nombre_enfants(self) -> int:
        """Calcul le nombre d'enfants dont le parent_id
        pointent vers l'identifiant_unique de cet acteur"""
        return parents_cache_get()["nombre_enfants"].get(self.identifiant_unique, 0)

    def get_absolute_url(self):
        return reverse("qfdmo:acteur-detail", args=[self.uuid])

    def acteur_actions(
        self, direction=None, actions_codes=None, sous_categorie_id=None
    ):
        pss = self.proposition_services.all()
        # Cast needed because of the cache
        cached_action_instances = cast(
            List[Action], cache.get_or_set("_action_instances", get_action_instances)
        )

        if sous_categorie_id:
            pss = pss.filter(sous_categories__id__in=[sous_categorie_id])
        if direction:
            pss = pss.filter(action__directions__code__in=[direction])
        if actions_codes:
            pss = pss.filter(action__code__in=actions_codes.split("|"))

        action_ids_to_display = pss.values_list("action__id", flat=True)
        return [
            action
            for action in cached_action_instances
            if action.id in action_ids_to_display
        ]

    @property
    def json_ld(self):
        data = {
            "@context": "https://schema.org",
            "@type": "Place",
            "geo": {
                "@type": "GeoCoordinates",
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
            "name": self.libelle,
        }
        if self.should_display_adresse:
            data.update(
                address={
                    "@type": "PostalAddress",
                    "addressLocality": self.ville,
                    "streetAddress": self.adresse,
                    "postalCode": self.code_postal,
                }
            )

        indent = 4 if settings.DEBUG else None
        return json.dumps(
            data,
            ensure_ascii=False,
            cls=LazyEncoder,
            indent=indent,
            sort_keys=True,
        )

    def json_acteur_for_display(
        self,
        direction: str | None = None,
        action_list: str | None = None,
        carte: bool = False,
        carte_config: CarteConfig = None,
        sous_categorie_id: str | None = None,
    ) -> str:
        # TODO: refacto jinja: once the shared/results.html template
        # will be migrated to django template, this method should
        # live in a template_tags instead.
        actions = self.acteur_actions(
            direction=direction,
            actions_codes=action_list,
            sous_categorie_id=sous_categorie_id,
        )

        def sort_actions_by_action_principale_and_order(a):
            if a == self.action_principale:
                return -1

            base_order = a.order or 0
            if carte and a.groupe_action:
                base_order += (a.groupe_action.order or 0) * 100
            return base_order

        acteur_dict = {
            "uuid": self.uuid,
            "location": orjson.loads(self.location.geojson),
        }

        if not actions:
            # TODO: explain why we need to decode here
            return orjson.dumps(acteur_dict).decode("utf-8")

        action_to_display = sorted(
            actions, key=sort_actions_by_action_principale_and_order
        )[0]

        if carte and action_to_display.groupe_action:
            action_to_display = action_to_display.groupe_action

        acteur_dict.update(
            icon=action_to_display.icon,
            couleur=action_to_display.couleur,
        )

        if carte_config:
            queryset = Q()
            if action_to_display:
                queryset &= Q(groupe_action__actions__code__in=[action_to_display]) | Q(
                    groupe_action__actions__code=None
                )

            if self.acteur_type:
                queryset &= Q(acteur_type=self.acteur_type) | Q(acteur_type=None)

            try:
                groupe_action_config = carte_config.groupe_action_configs.get(queryset)
                if groupe_action_config.icon:
                    # Property is camelcased as it is used in javascript
                    acteur_dict.update(iconFile=groupe_action_config.icon.url)
                    # In this case, a svg file uploaded by a user is used
                    # in place of the DSFR's icon code.
                    del acteur_dict["icon"]

            except GroupeActionConfig.DoesNotExist:
                pass

        if carte and action_to_display.code == "reparer":
            acteur_dict.update(
                bonus=getattr(self, "bonus", False),
                reparer=getattr(self, "reparer", False),
                fillBackground=True,
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
        return self.action.code


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


class VuePropositionService(BasePropositionService):
    class Meta:
        verbose_name = "Vue sur la proposition de service"
        verbose_name_plural = "Vue sur toutes les propositions de service"
        managed = False

    id = models.CharField(primary_key=True)

    acteur = models.ForeignKey(
        VueActeur,
        on_delete=models.CASCADE,
        null=False,
        related_name="proposition_services",
    )


class DisplayedPropositionServiceManager(models.Manager):
    def get_by_natural_key(self, acteur_natural_key, action_natural_key):
        return self.get(
            acteur=DisplayedActeur.objects.get_by_natural_key(*acteur_natural_key),
            action=Action.objects.get_by_natural_key(*action_natural_key),
        )


class DisplayedPropositionService(BasePropositionService):
    objects = DisplayedPropositionServiceManager()

    class Meta:
        verbose_name = "Proposition de service - AFFICHÉ"
        verbose_name_plural = "Proposition de service - AFFICHÉ"

    id = models.CharField(primary_key=True)
    acteur = models.ForeignKey(
        DisplayedActeur,
        on_delete=models.CASCADE,
        null=False,
        related_name="proposition_services",
    )

    def natural_key(self):
        return (self.acteur.natural_key(), self.action.natural_key())

    natural_key.dependencies = ["qfdmo.displayedacteur"]


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
