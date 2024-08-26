import random
import string
from typing import Any

import opening_hours
import orjson
from django.contrib.gis.db import models
from django.core.files.images import get_image_dimensions
from django.db.models.functions import Now
from django.forms import ValidationError, model_to_dict
from django.http import HttpRequest
from django.urls import reverse
from unidecode import unidecode

from qfdmo.models.action import Action, CachedDirectionAction
from qfdmo.models.categorie_objet import SousCategorieObjet
from qfdmo.models.utils import CodeAsNaturalKeyModel, NomAsNaturalKeyModel


class ActeurService(CodeAsNaturalKeyModel):
    class Meta:
        ordering = ["libelle"]
        verbose_name = "Service proposé"
        verbose_name_plural = "Services proposés"

    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=255, unique=True, blank=False, null=False)
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
    code = models.CharField(max_length=255, unique=True, blank=False, null=False)
    libelle = models.CharField(max_length=255, blank=False, null=False, default="?")

    @classmethod
    def get_digital_acteur_type_id(cls) -> int:
        if not cls._digital_acteur_type_id:
            (digital_acteur_type, _) = cls.objects.get_or_create(code="acteur digital")
            print(
                f"digital_acteur_type : {digital_acteur_type.id}"
                f" - {digital_acteur_type.code} - {digital_acteur_type}"
            )
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
        print(f"acteur_type : {self.acteur_type_id} - {self.acteur_type}")
        print(f"get_digital_acteur_type_id : {ActeurType.get_digital_acteur_type_id()}")
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
                    )
                )
                revision_proposition_service.sous_categories.add(
                    *proposition_service.sous_categories.all()
                )

        return acteur

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

    def save(self, *args, **kwargs):
        # OPTIMIZE: if we need to validate the main action in the service propositions
        # I guess it should be here
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
                        "acteur_services",
                        "labels",
                    ],
                ),
                acteur_type=(
                    self.acteur_type
                    if self.acteur_type
                    else ActeurType.objects.get(code="commerce")
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
        ps_action_ids = list(
            {ps.action_id for ps in self.proposition_services.all()}  # type: ignore
        )
        return [
            action
            for action in CachedDirectionAction.get_action_instances()
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
        if carte:

            def sort_key(a):
                return (a.order or 0) + (
                    a.groupe_action.order
                    if a.groupe_action and a.groupe_action.order
                    else 0
                ) * 100

            actions = sorted(actions, key=sort_key)
        else:
            actions = sorted(actions, key=lambda a: a.order or 0)

        # move action_principale as first of the list
        if self.action_principale in actions:
            actions.remove(self.action_principale)
            actions.insert(0, self.action_principale)

        acteur_dict = {
            "identifiant_unique": self.identifiant_unique,
            "location": orjson.loads(self.location.geojson),
        }
        if main_action := actions[0] if actions else None:
            if carte and main_action.groupe_action:
                acteur_dict["icon"] = main_action.groupe_action.icon
                acteur_dict["couleur"] = main_action.groupe_action.couleur
            else:
                acteur_dict["icon"] = main_action.icon
                acteur_dict["couleur"] = main_action.couleur

        return orjson.dumps(acteur_dict).decode("utf-8")


class DisplayedActeurTemp(BaseActeur):
    labels = models.ManyToManyField(
        LabelQualite,
        through="ActeurLabelQualite",
    )

    acteur_services = models.ManyToManyField(
        ActeurService,
        blank=True,
        through="ActeurActeurService",
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
