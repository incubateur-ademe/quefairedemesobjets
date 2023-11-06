import json
import random
import string

from django.contrib.gis.db import models
from django.db import connection
from django.forms import ValidationError, model_to_dict
from django.template.loader import render_to_string

from qfdmo.models.action import Action
from qfdmo.models.categorie_objet import SousCategorieObjet
from qfdmo.models.utils import NomAsNaturalKeyModel


class ActeurService(NomAsNaturalKeyModel):
    class Meta:
        verbose_name = "Service proposé"
        verbose_name_plural = "Services proposés"

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)
    lvao_id = models.IntegerField(blank=True, null=True)
    actions = models.ManyToManyField(Action)

    def serialize(self):
        return model_to_dict(self, exclude=["actions"])


class ActeurStatus(models.TextChoices):
    ACTIF = "ACTIF", "actif"
    INACTIF = "INACTIF", "inactif"
    SUPPRIME = "SUPPRIME", "supprimé"


class CorrectionActeurStatus(models.TextChoices):
    ACTIF = "ACTIF", "Actif"
    IGNORE = "IGNORE", "Ignoré"
    PAS_DE_MODIF = "PAS_DE_MODIF", "Pas de modification"
    ACCEPTE = "ACCEPTE", "Accepté"
    REJETE = "REJETE", "Rejeté"


class ActeurType(NomAsNaturalKeyModel):
    class Meta:
        verbose_name = "Type d'acteur"
        verbose_name_plural = "Types d'acteur"

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)
    nom_affiche = models.CharField(max_length=255, blank=False, null=False, default="?")
    lvao_id = models.IntegerField(blank=True, null=True)

    def serialize(self):
        return model_to_dict(self)


class Source(NomAsNaturalKeyModel):
    class Meta:
        verbose_name = "Source de données"
        verbose_name_plural = "Sources de données"

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True)
    logo = models.CharField(max_length=255, blank=True, null=True)
    afficher = models.BooleanField(default=True)
    url = models.CharField(max_length=2048, blank=True, null=True)

    def serialize(self):
        return model_to_dict(self)


class BaseActeur(NomAsNaturalKeyModel):
    class Meta:
        abstract = True

    nom = models.CharField(max_length=255, blank=False, null=False)
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
    # FIXME : multi_base could be removed ?
    multi_base = models.BooleanField(default=False)
    nom_commercial = models.CharField(max_length=255, blank=True, null=True)
    nom_officiel = models.CharField(max_length=255, blank=True, null=True)
    # FIXME : manuel could be removed ?
    manuel = models.BooleanField(default=False)
    # FIXME : Could be replace to a many-to-many relationship with a label table ?
    label_reparacteur = models.BooleanField(default=False)
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

    @property
    def latitude(self):
        return self.location.y if self.location else None

    @property
    def longitude(self):
        return self.location.x if self.location else None

    @property
    def nom_affiche(self):
        return self.nom_commercial or self.nom

    @property
    def is_digital(self) -> bool:
        return bool(self.acteur_type and self.acteur_type.nom == "acteur digital")

    def serialize(self, format: None | str = None) -> dict | str:
        self_as_dict = model_to_dict(
            self, exclude=["location", "proposition_services", "acteur_type", "source"]
        )
        if self.acteur_type:
            self_as_dict["acteur_type"] = self.acteur_type.serialize()
        if self.source:
            self_as_dict["source"] = self.source.serialize()
        if self.location:
            self_as_dict["location"] = json.loads(self.location.geojson)
        proposition_services = self.proposition_services.all()  # type: ignore
        self_as_dict["proposition_services"] = []
        for proposition_service in proposition_services:
            self_as_dict["proposition_services"].append(proposition_service.serialize())
        if format == "json":
            return json.dumps(self_as_dict)
        return self_as_dict

    def acteur_services(self) -> list[ActeurService]:
        return list(set([ps.acteur_service for ps in self.proposition_services.all()]))


class Acteur(BaseActeur):
    class Meta:
        verbose_name = "ACTEUR de l'EC - IMPORTÉ"
        verbose_name_plural = "ACTEURS de l'EC - IMPORTÉ"

    def get_or_create_revision(self):
        fields = model_to_dict(
            self,
            fields=[
                "multi_base",
                "label_reparacteur",
                "manuel",
                "statut",
            ],
        )
        (revision_acteur, created) = RevisionActeur.objects.get_or_create(
            identifiant_unique=self.identifiant_unique, defaults=fields
        )
        if created:
            for proposition_service in self.proposition_services.all():  # type: ignore
                revision_proposition_service = (
                    RevisionPropositionService.objects.create(
                        revision_acteur=revision_acteur,
                        action_id=proposition_service.action_id,
                        acteur_service_id=proposition_service.acteur_service_id,
                    )
                )
                revision_proposition_service.sous_categories.add(
                    *proposition_service.sous_categories.all()
                )

        return revision_acteur

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
            self.source = Source.objects.get_or_create(nom="equipe")[0]
        if not self.identifiant_unique:
            self.identifiant_unique = (
                self.source.nom.lower() + "_" + str(self.identifiant_externe)
            )


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
                    exclude=["id", "acteur_type", "source", "proposition_services"],
                ),
                acteur_type=self.acteur_type
                if self.acteur_type
                else ActeurType.objects.get(nom="commerce"),
                source=self.source,
            )
            self.identifiant_unique = acteur.identifiant_unique
            self.identifiant_externe = acteur.identifiant_externe
            self.source = acteur.source

    def __str__(self):
        return self.nom or self.identifiant_unique


class FinalActeur(BaseActeur):
    class Meta:
        managed = False
        db_table = "qfdmo_finalacteur"
        verbose_name = "ACTEUR de l'EC - AFFICHÉ"
        verbose_name_plural = "ACTEURS de l'EC - AFFICHÉ"

    @classmethod
    def refresh_view(cls):
        with connection.cursor() as cursor:
            cursor.execute(
                """
REFRESH MATERIALIZED VIEW CONCURRENTLY qfdmo_finalacteur;
REFRESH MATERIALIZED VIEW CONCURRENTLY qfdmo_finalpropositionservice;
REFRESH MATERIALIZED VIEW CONCURRENTLY qfdmo_finalpropositionservice_sous_categories;
                """
            )

    def acteur_actions(self, direction=None):
        collected_action = [
            ps.action
            for ps in self.proposition_services.all()  # type: ignore
            if direction is None
            or direction in [d.nom for d in ps.action.directions.all()]
        ]
        collected_action = list(set(collected_action))
        collected_action.sort(key=lambda x: x.order)
        return collected_action

    def render_as_card(self, direction: str | None = None) -> str:
        return render_to_string(
            "qfdmo/acteur_as_card.html", {"acteur": self, "direction": direction}
        )

    def serialize(
        self,
        format: None | str = None,
        render_as_card: bool = False,
        direction: str | None = None,
    ) -> dict | str:
        super_serialized = super().serialize(format=None)
        super_serialized["actions"] = [  # type: ignore
            action.serialize() for action in self.acteur_actions(direction=direction)
        ]
        if render_as_card:
            super_serialized["render_as_card"] = self.render_as_card(  # type: ignore
                direction=direction
            )

        if format == "json":
            return json.dumps(super_serialized)
        return super_serialized


class CorrectionActeur(BaseActeur):
    class Meta:
        verbose_name = "Proposition de correction d'un acteur"
        verbose_name_plural = "Propositions de correction des acteurs"

    id = models.AutoField(primary_key=True)
    identifiant_unique = models.CharField(max_length=255)
    source = models.CharField(max_length=255)
    resultat_brute_source = models.JSONField()
    acteur_type = models.ForeignKey(
        ActeurType, on_delete=models.CASCADE, null=True, blank=True, default=None
    )
    final_acteur = models.ForeignKey(
        FinalActeur,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="corrections",
        to_field="identifiant_unique",
    )
    correction_statut = models.CharField(
        max_length=255,
        default=CorrectionActeurStatus.ACTIF,
        choices=CorrectionActeurStatus.choices,
    )

    # FIXME : could be tested
    def __str__(self):
        return self.identifiant_unique

    def accepted_by_default(self):
        return self.correction_statut in [
            CorrectionActeurStatus.ACCEPTE,
            CorrectionActeurStatus.ACTIF,
        ]

    def rejected_by_default(self):
        return self.correction_statut in [CorrectionActeurStatus.REJETE]

    def ignored_by_default(self):
        return self.correction_statut in [CorrectionActeurStatus.IGNORE]


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
        # FIXME missing unique constraint

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

    revision_acteur = models.ForeignKey(
        RevisionActeur,
        to_field="identifiant_unique",
        on_delete=models.CASCADE,
        null=False,
        related_name="proposition_services",
    )

    def __str__(self):
        return f"{self.revision_acteur} - {super().__str__()}"


class FinalPropositionService(BasePropositionService):
    class Meta:
        managed = False
        db_table = "qfdmo_finalpropositionservice"
        verbose_name = "Proposition de service"
        verbose_name_plural = "Proposition de service"

    acteur = models.ForeignKey(
        FinalActeur,
        on_delete=models.CASCADE,
        null=False,
        related_name="proposition_services",
    )
