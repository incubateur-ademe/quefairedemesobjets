import json
import logging
import random
import re
import string
import uuid
from copy import deepcopy
from typing import Any, List, cast
from urllib.parse import urlencode

import opening_hours
import shortuuid
from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.geos.geometry import GEOSGeometry
from django.contrib.gis.measure import D
from django.core.cache import cache
from django.core.files.images import get_image_dimensions
from django.core.validators import RegexValidator
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

from core.constants import DIGITAL_ACTEUR_CODE
from core.models.mixin import TimestampedModel
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
from qfdmo.models.geo import EPCI
from qfdmo.models.utils import (
    CodeAsNaturalKeyModel,
    compute_identifiant_unique,
    string_remove_substring_via_normalization,
)
from qfdmo.validators import CodeValidator

logger = logging.getLogger(__name__)

DEFAULT_SOURCE_CODE = "communautelvao"


def generate_short_uuid():
    """Wrapper function for shortuuid.uuid to avoid migration issues"""
    return shortuuid.uuid()


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


class DepartementOrNumValidator(RegexValidator):
    # soit 2A, 2B, ou un entier
    regex = r"^2A$|^2B$|^[0-9]+$"
    message = (
        "Le champ `value` doit être le numéro d'un département ou le nombre de"
        " kilomètres d'un périmètre pour la réalisation d'un service à domicile."
    )
    code = "invalid_code"


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

    def __str__(self):
        return self.libelle


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
    if value and value == EMPTY_ACTEUR_FIELD:
        return
    if value and not opening_hours.validate(value):
        raise ValidationError(
            ("%(value)s is not an valid opening hours"),
            params={"value": value},
        )


class LabelQualite(CodeAsNaturalKeyModel):
    class Meta:
        verbose_name = "Label qualité"
        verbose_name_plural = "Labels qualité"
        ordering = ["order"]

    order = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
    )

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
    afficher = models.BooleanField(
        default=True,
        help_text="Affiche le label côté frontend, notamment dans les fiches acteur",
    )
    filtre = models.BooleanField(
        default=False,
        help_text="Affiche le label dans la modale de filtres affichée sur"
        " la carte ou le mode liste",
    )
    filtre_label = models.CharField(
        blank=True,
        help_text="Configure le label affiché dans le champ de formulaire"
        " dans le panel de filtres sur la carte ou le mode liste",
    )
    filtre_texte_d_aide = models.CharField(
        blank=True,
        help_text="Configure le texte d'aide affiché dans le champ de formulaire"
        " dans le panel de filtres sur la carte ou le mode liste",
    )
    logo_filtre = models.FileField(
        upload_to="labels",
        blank=True,
        null=True,
        verbose_name="Logo pour les filtres (SVG recommandé)",
        help_text="Logo affiché dans le panneau de filtres de la carte. "
        "Format SVG recommandé pour une qualité optimale. "
        "Utilisé dans : modale de filtres côté utilisateur.",
    )
    logo_file = models.ImageField(
        upload_to="logos",
        blank=True,
        null=True,
        validators=[validate_logo],
        verbose_name="Logo pour carte et open data (PNG 32x32px)",
        help_text="Version miniature du logo : PNG 32x32 pixels maximum, 50 Ko max. "
        "Utilisé dans : fiches acteurs sur la carte, export open data API. "
        "Contraintes strictes : exactement 32x32 pixels.",
    )
    bonus = models.BooleanField(
        default=False, help_text="Ouvre les droits à un bonus financier"
    )
    type_enseigne = models.BooleanField(
        default=False,
        help_text="Ce label est affiché comme un type d'enseigne, ex : ESS",
    )
    url = models.CharField(max_length=2048, blank=True, null=True)

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

    def with_displayable_labels(self):
        """
        Prefetch labels ordered by bonus (desc) and type_enseigne.
        This allows the acteur_label template tag to simply take the first label.

        Returns a queryset with displayable_labels_ordered attribute on each acteur.
        """
        from django.db.models import Prefetch

        ordered_labels = Prefetch(
            "labels",
            queryset=LabelQualite.objects.filter(afficher=True).order_by(
                "-bonus", "type_enseigne"
            ),
            to_attr="displayable_labels_ordered",
        )
        return self.prefetch_related(ordered_labels)

    def digital(self):
        # 1. Get ordered primary keys
        # List here ensures queryset is not re-evaluated, causing
        # a re-ordering and key error in the return below
        pks = list(
            self.filter(acteur_type__code=DIGITAL_ACTEUR_CODE)
            .annotate(min_action_order=Min("proposition_services__action__order"))
            .values("min_action_order", "pk")
            .order_by("min_action_order", "?")
            .values_list("pk", flat=True)[:100]
        )
        # 2. Fetch digital acteurs and preserver ordering.
        ordered_pks = {pk: index for index, pk in enumerate(pks)}
        instances = list(self.filter(pk__in=pks))
        return sorted(instances, key=lambda x: ordered_pks[x.pk])

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

    def from_center(self, longitude, latitude, distance_max):
        reference_point = Point(float(longitude), float(latitude), srid=4326)
        self._has_distance_field = True

        return (
            self.physical()
            .filter(
                location__dwithin=(
                    reference_point,
                    D(m=distance_max),
                )
            )
            .annotate(distance=Distance("location", reference_point))
            .order_by("distance")
        )


class LatLngPropertiesMixin(models.Model):
    location: models.PointField

    @property
    def latitude(self):
        return self.location.y if self.location else None

    @property
    def longitude(self):
        return self.location.x if self.location else None

    class Meta:
        abstract = True


class BaseActeur(TimestampedModel):
    class LieuPrestation(models.TextChoices):
        A_DOMICILE = "A_DOMICILE", "À domicile"
        SUR_PLACE = "SUR_PLACE", "Sur place"
        SUR_PLACE_OU_A_DOMICILE = "SUR_PLACE_OU_A_DOMICILE", "Sur place ou à domicile"

    class Meta:
        abstract = True

    nom = models.CharField(max_length=255, blank=False, null=False, db_index=True)
    description = models.TextField(blank=True, default="", db_default="")
    identifiant_unique = models.CharField(
        max_length=255,
        unique=True,
        primary_key=True,
        blank=True,
        db_index=True,
        editable=False,
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
    location = models.PointField(blank=True, null=True, geography=True)
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
    consignes_dacces = models.TextField(
        verbose_name="Consignes d'accès",
        blank=True,
        default="",
        db_default="",
    )
    lieu_prestation = models.CharField(
        max_length=255,
        choices=LieuPrestation.choices,
        default=LieuPrestation.SUR_PLACE,
        blank=True,
        null=True,
    )

    @property
    def service_a_domicile(self):
        if not self.lieu_prestation:
            return {}
        return {
            "lieu_prestation": self.lieu_prestation,
            "perimetre_adomicile": [
                {
                    "type": perimetre.type,
                    "valeur": perimetre.valeur,
                }
                for perimetre in self.perimetre_adomiciles.all()
            ],
        }

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
        return self.ordered_labels_by_bonus_and_type_enseigne.filter(type_enseigne=True)

    @cached_property
    def labels_without_enseigne_display(self):
        return self.ordered_labels_by_bonus_and_type_enseigne.exclude(
            type_enseigne=True
        )

    @cached_property
    def ordered_labels_by_bonus_and_type_enseigne(self):
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
        # Work with prefetched data to avoid N+1 queries
        return any(label.afficher and label.bonus for label in self.labels.all())

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
            "perimetre_adomiciles",
            "suggestion_groupes",
            "suggestion_unitaires",
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
            if not self.source:
                raise ValueError("Source is required to generate identifiant_unique")
            self.identifiant_unique = compute_identifiant_unique(
                self.source.code, self.identifiant_externe
            )

    def __str__(self):
        return self.nom


def clean_parent(parent):
    try:
        parent = RevisionActeur.objects.get(identifiant_unique=parent)
    except RevisionActeur.DoesNotExist:
        raise ValidationError("You can't define a Parent which does not exist.")

    if parent and parent.parent:
        raise ValidationError("You can't define a Parent which is already a duplicate.")


class Acteur(BaseActeur, LatLngPropertiesMixin):
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


class BasePerimetreADomicile(models.Model):
    class Meta:
        abstract = True
        verbose_name = "Périmètre à domicile"
        verbose_name_plural = "Périmètres à domicile"

    class Type(models.TextChoices):
        DEPARTEMENTAL = "DEPARTEMENTAL", "Départemental"
        KILOMETRIQUE = "KILOMETRIQUE", "Kilométrique"
        FRANCE_METROPOLITAINE = (
            "FRANCE_METROPOLITAINE",
            "France métropolitaine (Corse incluse)",
        )
        DROM_TOM = "DROM_TOM", "DROM TOM"

    acteur = models.ForeignKey(
        Acteur, on_delete=models.CASCADE, related_name="perimetre_adomiciles"
    )
    type = models.CharField(
        choices=Type.choices,
        default=Type.KILOMETRIQUE,
    )
    # Char is needed because Corsica codes are 2A and 2B
    valeur = models.CharField(
        blank=True,
        validators=[
            DepartementOrNumValidator(),
        ],
    )


class PerimetreADomicile(BasePerimetreADomicile):
    pass


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


class RevisionActeur(BaseActeur, LatLngPropertiesMixin):
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
    def is_parent(self):
        return self.pk and self.duplicats.exists()

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

        # Appliquer la valeur par défaut pour statut avant full_clean()
        # car Django n'applique pas automatiquement les valeurs par défaut avant la
        # validation
        if not self.statut:
            self.statut = ActeurStatus.ACTIF

        acteur = self.set_default_fields_and_objects_before_save()
        self.full_clean()
        creating = self._state.adding  # Before calling save
        if creating:
            # We keep acteur's lieu_prestation because it goes with perimetre_adomicile
            self.lieu_prestation = acteur.lieu_prestation
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
            for perimetre_adomicile in acteur.perimetre_adomiciles.all():
                RevisionPerimetreADomicile.objects.create(
                    acteur=self,
                    type=perimetre_adomicile.type,
                    valeur=perimetre_adomicile.valeur,
                )

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
        # Appliquer la valeur par défaut pour statut avant full_clean()
        # car Django n'applique pas automatiquement les valeurs par défaut avant la
        # validation
        if not self.statut:
            self.statut = ActeurStatus.ACTIF
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
                "perimetre_adomicile",
                "parent",
                "parent_reason",
                "is_parent",
                "location",
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
                "location": self.location,
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


class RevisionPerimetreADomicile(BasePerimetreADomicile):
    acteur = models.ForeignKey(
        RevisionActeur, on_delete=models.CASCADE, related_name="perimetre_adomiciles"
    )


"""
Model to display all acteurs in admin
"""


class FinalActeurManager(models.Manager):
    def get_active_parents(self):
        return self.get_queryset().filter(
            statut=ActeurStatus.ACTIF,
            source_id__isnull=True,
        )


class DisplayedActeurManager(FinalActeurManager, models.Manager):
    def get_queryset(self):
        return DisplayedActeurQuerySet(self.model, using=self._db)

    def get_by_natural_key(self, uuid):
        return self.get(
            uuid=uuid,
        )


class FinalActeur(BaseActeur):
    class Meta:
        abstract = True

    objects = FinalActeurManager()

    uuid = models.CharField(
        max_length=255, default=generate_short_uuid, editable=False, db_index=True
    )
    code_commune_insee = models.CharField(
        max_length=10, blank=True, default="", db_index=True
    )

    epci = models.ForeignKey(EPCI, on_delete=models.CASCADE, blank=True, null=True)


class VueActeur(FinalActeur):
    class Meta:
        verbose_name = "ACTEUR de l'EC - Vue sur l'acteur"
        verbose_name_plural = "ACTEURS de l'EC - Vues sur tous les acteurs"

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

    # Table name qfdmo_vueacteur_sources
    sources = models.ManyToManyField(
        Source,
        blank=True,
        related_name="vue_acteurs",
    )

    # Readonly fields
    revision_existe = models.BooleanField(
        default=False, editable=False, verbose_name="Une correction existe"
    )
    est_parent = models.BooleanField(
        default=False, editable=False, verbose_name="L'acteur est un parent"
    )
    liste_enfants = models.JSONField(
        default=None,
        editable=False,
        null=True,
        verbose_name="La liste des enfants de l'acteur parent",
    )
    nombre_enfants = models.IntegerField(
        default=None,
        editable=False,
        null=True,
        verbose_name="Le nombre d'enfants de l'acteur parent",
    )
    est_dans_carte = models.BooleanField(
        default=False, editable=False, verbose_name="L'acteur est affiché dans la carte"
    )
    est_dans_opendata = models.BooleanField(
        default=False,
        editable=False,
        verbose_name="L'acteur est dans le partage opendata",
    )
    latitude = models.FloatField(
        default=0.0, editable=False, null=True, verbose_name="La latitude de l'acteur"
    )
    longitude = models.FloatField(
        default=0.0, editable=False, null=True, verbose_name="La longitude de l'acteur"
    )

    @property
    def is_parent(self):
        return self.pk and self.duplicats.exists()


class VuePerimetreADomicile(BasePerimetreADomicile):
    acteur = models.ForeignKey(
        VueActeur, on_delete=models.CASCADE, related_name="perimetre_adomiciles"
    )


class DisplayedActeur(FinalActeur, LatLngPropertiesMixin):
    objects = DisplayedActeurManager()

    def natural_key(self):
        return (self.uuid,)

    class Meta:
        verbose_name = "ACTEUR de l'EC - AFFICHÉ"
        verbose_name_plural = "ACTEURS de l'EC - AFFICHÉ"
        indexes = [
            # Composite index for common spatial + status queries
            models.Index(
                fields=["statut", "acteur_type_id"],
                name="da_statut_type_idx",
            ),
            # Spatial index is already created by GeoDjango for location field
            # Adding a functional index would require a migration with raw SQL
        ]

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

    @cached_property
    def suggestion_form_url(self):
        query_params = {
            "Nom": self.nom,
            "Ville": self.ville,
            "Adresse": self.adresse,
        }
        querystring = urlencode(query_params)
        return f"{reverse('qfdmo:update-suggestion-form')}?{querystring}"

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

    def action_to_display(
        self,
        direction: str | None = None,
        action_list: str | None = None,
        sous_categorie_id: int | None = None,
        carte: bool = True,
    ) -> Action | None:
        actions = self.acteur_actions(
            direction=direction,
            actions_codes=action_list,
            sous_categorie_id=sous_categorie_id,
        )

        if not actions:
            return None

        def sort_actions_by_action_principale_and_order(a):
            if a == self.action_principale:
                return -1

            base_order = a.order or 0
            if carte and a.groupe_action:
                base_order += (a.groupe_action.order or 0) * 100
            return base_order

        return sorted(actions, key=sort_actions_by_action_principale_and_order)[0]

    def get_absolute_url(self):
        return reverse("qfdmo:acteur-detail", args=[self.uuid])

    @property
    def full_url(self):
        return f"{settings.BASE_URL}{self.get_absolute_url()}"

    def acteur_actions(
        self, direction=None, actions_codes=None, sous_categorie_id=None
    ):
        # Cast needed because of the cache
        cached_action_instances = cast(
            List[Action], cache.get_or_set("_action_instances", get_action_instances)
        )

        # Work with prefetched data in memory to avoid N+1 queries
        # Access all() to use prefetched data
        pss = list(self.proposition_services.all())

        # Filter in Python instead of database to leverage prefetch
        if sous_categorie_id:
            pss = [
                ps
                for ps in pss
                if any(sc.id == sous_categorie_id for sc in ps.sous_categories.all())
            ]

        if direction:
            pss = [
                ps
                for ps in pss
                if any(d.code == direction for d in ps.action.directions.all())
            ]

        if actions_codes:
            action_codes_list = actions_codes.split("|")
            pss = [ps for ps in pss if ps.action.code in action_codes_list]

        # Extract action IDs from filtered proposition services
        action_ids_to_display = {ps.action_id for ps in pss}

        return [
            action
            for action in cached_action_instances
            if action.id in action_ids_to_display
        ]

    @property
    def json_ld(self):
        # Prevent a circular dependency error
        from core.utils import LazyEncoder

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

    def get_share_url(self, request: HttpRequest, direction: str | None = None) -> str:
        protocol = "https" if request.is_secure() else "http"
        host = request.get_host()
        base_url = f"{protocol}://{host}{self.get_absolute_url()}"

        params = []
        if "carte" in request.GET:
            params.append("carte=1")
        if direction:
            params.append(f"direction={direction}")
        return f"{base_url}?{'&'.join(params)}"

    @cached_property
    def should_display_adresse(self) -> bool:
        return not self.is_digital and bool(
            self.adresse or self.adresse_complement or self.code_postal or self.ville
        )


class DisplayedPerimetreADomicile(BasePerimetreADomicile):
    acteur = models.ForeignKey(
        DisplayedActeur, on_delete=models.CASCADE, related_name="perimetre_adomiciles"
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
        indexes = [
            models.Index(fields=["acteur", "action"], name="dps_acteur_action_idx"),
        ]

    id = models.CharField(primary_key=True)
    acteur = models.ForeignKey(
        DisplayedActeur,
        on_delete=models.CASCADE,
        null=False,
        related_name="proposition_services",
    )

    def generate_id_if_missing(self) -> None:
        """
        Generate and set the ID for this DisplayedPropositionService instance
        if it is missing.

        This method is intended for use in contexts where the instance is created
        outside of the normal dbt clustering process, such as when loading fixtures
        for tests. It ensures that the ID is correctly initialized,
        mimicking the logic used during clustering.
        """
        if not self.id:
            self.id = uuid.uuid4()

    def natural_key(self):
        return (self.acteur.natural_key(), self.action.natural_key())

    natural_key.dependencies = ["qfdmo.displayedacteur"]
