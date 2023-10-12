import json

from django.contrib.gis.db import models
from django.db import connection
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.forms import model_to_dict
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


class SourceDonnee(NomAsNaturalKeyModel):
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
    # FIXME : use identifiant_unique as primary in import export
    identifiant_unique = models.CharField(max_length=255, unique=True)
    acteur_type = models.ForeignKey(
        ActeurType, on_delete=models.CASCADE, blank=True, null=True
    )
    adresse = models.CharField(max_length=255, blank=True, null=True)
    adresse_complement = models.CharField(max_length=255, blank=True, null=True)
    code_postal = models.CharField(max_length=10, blank=True, null=True)
    ville = models.CharField(max_length=255, blank=True, null=True)
    url = models.CharField(max_length=2048, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    # FIXME : not mandatory if digital
    # FIXME : lat long for import export
    # FIXME : export more than x lines should be forbidden
    location = models.PointField(null=False)
    telephone = models.CharField(max_length=255, blank=True, null=True)
    multi_base = models.BooleanField(default=False)
    nom_commercial = models.CharField(max_length=255, blank=True, null=True)
    nom_officiel = models.CharField(max_length=255, blank=True, null=True)
    manuel = models.BooleanField(default=False)
    label_reparacteur = models.BooleanField(default=False)
    siret = models.CharField(max_length=14, blank=True, null=True)
    source_donnee = models.CharField(max_length=255, blank=True, null=True)
    # FIXME : serialize source
    source = models.ForeignKey(
        SourceDonnee, on_delete=models.CASCADE, blank=True, null=True
    )
    identifiant_externe = models.CharField(max_length=255, blank=True, null=True)
    statut = models.CharField(
        max_length=255, default=ActeurStatus.ACTIF, choices=ActeurStatus.choices
    )

    @property
    def latitude(self):
        return self.location.y

    @property
    def longitude(self):
        return self.location.x

    @property
    def nom_affiche(self):
        return self.nom_commercial or self.nom

    @property
    def is_digital(self) -> bool:
        return bool(self.acteur_type and self.acteur_type.nom == "acteur digital")

    def serialize(self, format: None | str = None) -> dict | str:
        self_as_dict = model_to_dict(
            self, exclude=["location", "proposition_services", "acteur_type"]
        )
        if self.acteur_type:
            self_as_dict["acteur_type"] = self.acteur_type.serialize()
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

    # FIXME : could be remove if we use identifiant_unique as primary key
    id = models.AutoField(primary_key=True)

    def get_or_create_revision(self):
        fields = model_to_dict(
            self,
            fields=[
                "identifiant_unique",
                "nom",
                "adresse",
                "adresse_complement",
                "code_postal",
                "ville",
                "location",
                "acteur_type",
                "multi_base",
                "label_reparacteur",
                "manuel",
            ],
        )
        fields["acteur_type_id"] = fields.pop("acteur_type")
        (revision_acteur, created) = RevisionActeur.objects.get_or_create(
            id=self.id, defaults=fields
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


class RevisionActeur(BaseActeur):
    class Meta:
        verbose_name = "ACTEUR de l'EC - CORRIGÉ"
        verbose_name_plural = "ACTEURS de l'EC - CORRIGÉ"

    id = models.IntegerField(primary_key=True)


@receiver(pre_save, sender=RevisionActeur)
def create_acteur_if_not_exists(sender, instance, *args, **kwargs):
    if instance.id is None:
        acteur = Acteur.objects.create(
            **model_to_dict(
                instance, exclude=["id", "acteur_type", "proposition_services"]
            ),
            acteur_type=instance.acteur_type,
        )
        instance.id = acteur.id


class FinalActeur(BaseActeur):
    class Meta:
        managed = False
        db_table = "qfdmo_finalacteur"
        verbose_name = "ACTEUR de l'EC - AFFICHÉ"
        verbose_name_plural = "ACTEURS de l'EC - AFFICHÉ"

    id = models.IntegerField(primary_key=True)

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


class BasePropositionService(models.Model):
    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["acteur", "action", "acteur_service"],
                name="unique_by_acteur_action_service",
            )
        ]

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
    # FIXME : alphabetic order in admin
    sous_categories = models.ManyToManyField(
        SousCategorieObjet,
    )

    # FIXME: test me please !!!
    def __str__(self):
        return (
            f"{self.action.nom} - {self.acteur_service.nom} -"
            f" { ', '.join([ str(sc) for sc in self.sous_categories.all()]) }"
        )

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

    acteur = models.ForeignKey(
        Acteur,
        on_delete=models.CASCADE,
        null=False,
        related_name="proposition_services",
    )

    # FIXME: test me please !!!
    def __str__(self):
        return f"{self.acteur} - {super().__str__()}"


class RevisionPropositionService(BasePropositionService):
    class Meta:
        verbose_name = "PROPOSITION DE SERVICE - CORRIGÉ"
        verbose_name_plural = "PROPOSITIONS DE SERVICE - CORRIGÉ"

    revision_acteur = models.ForeignKey(
        RevisionActeur,
        on_delete=models.CASCADE,
        null=False,
        related_name="proposition_services",
    )

    # FIXME: test me please !!!
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
