import json

from django.contrib.gis.db import models
from django.db import connection
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.forms import model_to_dict
from django.template.loader import render_to_string
from unidecode import unidecode


class NomAsNaturalKeyManager(models.Manager):
    def get_by_natural_key(self, nom: str) -> models.Model:
        return self.get(nom=nom)


class NomAsNaturalKeyModel(models.Model):
    class Meta:
        abstract = True

    objects = NomAsNaturalKeyManager()

    nom = models.CharField()

    def natural_key(self) -> tuple[str]:
        return (self.nom,)

    def __str__(self) -> str:
        return self.nom


class CategorieObjet(NomAsNaturalKeyModel):
    class Meta:
        verbose_name = "Catégorie d'objets"
        verbose_name_plural = "Catégories d'objets"

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)

    def serialize(self):
        return model_to_dict(self)


class CodeAsNaturalKeyManager(models.Manager):
    def get_by_natural_key(self, code: str) -> models.Model:
        return self.get(code=code)


class SousCategorieObjet(models.Model):
    class Meta:
        verbose_name = "Sous catégorie d'objets"
        verbose_name_plural = "Sous catégories d'objets"

    objects = CodeAsNaturalKeyManager()

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)
    lvao_id = models.IntegerField(blank=True, null=True)
    categorie = models.ForeignKey(CategorieObjet, on_delete=models.CASCADE)
    code = models.CharField(max_length=10, unique=True, blank=False, null=False)

    def __str__(self) -> str:
        return self.nom

    def natural_key(self) -> tuple[str]:
        return (self.code,)

    @property
    def sanitized_nom(self) -> str:
        return unidecode(self.nom).upper()

    def serialize(self):
        sous_categorie = model_to_dict(self, exclude=["categorie"])
        sous_categorie["categorie"] = self.categorie.serialize()
        return sous_categorie


class Objet(NomAsNaturalKeyModel):
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)
    sous_categorie = models.ForeignKey(
        SousCategorieObjet,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="objets",
    )


class ActionDirection(NomAsNaturalKeyModel):
    class Meta:
        verbose_name = "Direction de l'action"
        verbose_name_plural = "Directions de l'action"

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)
    order = models.IntegerField(blank=False, null=False, default=0)
    nom_affiche = models.CharField(max_length=255, unique=True, blank=False, null=False)

    def __str__(self):
        return self.nom_affiche


class Action(NomAsNaturalKeyModel):
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)
    nom_affiche = models.CharField(max_length=255, null=False, default="")
    description = models.CharField(max_length=255, null=True, blank=True)
    order = models.IntegerField(blank=False, null=False, default=0)
    lvao_id = models.IntegerField(blank=True, null=True)
    directions = models.ManyToManyField(ActionDirection)
    couleur = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default="yellow-tournesol",
        help_text="""Couleur du badge à choisir dans le DSFR
Couleur dispoible : blue-france, green-tilleul-verveine, green-bourgeon, green-emeraude,
green-menthe, green-archipel, blue-ecume, blue-cumulus, purple-glycine, pink-macaron,
pink-tuile, yellow-tournesol, yellow-moutarde, orange-terre-battue, brown-cafe-creme,
brown-caramel, brown-opera, beige-gris-galet""",
    )
    icon = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Icône du badge à choisir dans le <a href='https://www.systeme-de-design.gouv.fr/elements-d-interface/fondamentaux-techniques/icones' target='_blank'>DSFR</a>",  # noqa E501
    )

    def serialize(self):
        return model_to_dict(self, exclude=["directions"])


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


class LVAOBase(NomAsNaturalKeyModel):
    class Meta:
        verbose_name = "Acteur LVAO"
        verbose_name_plural = "Acteurs LVAO"

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, blank=False, null=False)  # title
    identifiant_unique = models.CharField(
        max_length=255, blank=True, null=True, unique=True
    )  # UniqueId


class LVAOBaseRevision(NomAsNaturalKeyModel):
    class Meta:
        verbose_name = "Révision Acteur LVAO"
        verbose_name_plural = "Révision Acteurs LVAO"

    id = models.AutoField(primary_key=True)
    lvao_base = models.ForeignKey(
        LVAOBase,
        on_delete=models.CASCADE,
        null=False,
        related_name="lvao_base_revisions",
    )
    lvao_node_id = models.IntegerField(null=False)  # node_id
    lvao_revision_id = models.IntegerField(null=True, unique=True)  # revision_id
    nom = models.CharField(max_length=255, blank=False, null=False)  # title
    acteur_type = models.ForeignKey(
        ActeurType, on_delete=models.CASCADE, blank=True, null=True
    )  # TypeActeur
    adresse = models.CharField(max_length=255, blank=True, null=True)  # Adresse1
    adresse_complement = models.CharField(
        max_length=255, blank=True, null=True
    )  # Adresse2
    code_postal = models.CharField(max_length=10, blank=True, null=True)  # CodePostal
    ville = models.CharField(max_length=255, blank=True, null=True)  # Ville
    url = models.CharField(max_length=2048, blank=True, null=True)  # url
    email = models.EmailField(blank=True, null=True)  # email
    latitude = models.FloatField(blank=True, null=True)  # latitude
    longitude = models.FloatField(blank=True, null=True)  # longitude
    telephone = models.CharField(max_length=255, blank=True, null=True)  # Telephone
    multi_base = models.BooleanField(default=False)  # MultiBase
    nom_commercial = models.CharField(max_length=255, blank=True, null=True)  # NomCial
    nom_officiel = models.CharField(
        max_length=255, blank=True, null=True
    )  # RaisonSociale
    publie = models.BooleanField(default=False)  # Published
    manuel = models.BooleanField(default=False)  # Manuel
    label_reparacteur = models.BooleanField(default=False)  # Reparacteur
    siret = models.CharField(max_length=14, blank=True, null=True)  # Siret
    source_donnee = models.CharField(
        max_length=255, blank=True, null=True
    )  # BDD # todo: choice field
    identifiant_externe = models.CharField(
        max_length=255, blank=True, null=True
    )  # ActeurId
    actions = models.ManyToManyField(Action, related_name="actions")  # Geste
    acteur_services = models.ManyToManyField(
        ActeurService, related_name="acteur_services"
    )  # Activite
    sous_categories = models.ManyToManyField(
        SousCategorieObjet, related_name="sous_categories"
    )  # Objets


class BaseActeur(NomAsNaturalKeyModel):
    class Meta:
        abstract = True

    nom = models.CharField(max_length=255, blank=False, null=False)
    identifiant_unique = models.CharField(
        max_length=255, blank=True, null=True, unique=True
    )
    acteur_type = models.ForeignKey(
        ActeurType, on_delete=models.CASCADE, blank=True, null=True
    )
    adresse = models.CharField(max_length=255, blank=True, null=True)
    adresse_complement = models.CharField(max_length=255, blank=True, null=True)
    code_postal = models.CharField(max_length=10, blank=True, null=True)
    ville = models.CharField(max_length=255, blank=True, null=True)
    url = models.CharField(max_length=2048, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    location = models.PointField(null=False)
    telephone = models.CharField(max_length=255, blank=True, null=True)
    multi_base = models.BooleanField(default=False)
    nom_commercial = models.CharField(max_length=255, blank=True, null=True)
    nom_officiel = models.CharField(max_length=255, blank=True, null=True)
    manuel = models.BooleanField(default=False)
    label_reparacteur = models.BooleanField(default=False)
    siret = models.CharField(max_length=14, blank=True, null=True)
    source_donnee = models.CharField(max_length=255, blank=True, null=True)
    identifiant_externe = models.CharField(max_length=255, blank=True, null=True)

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

    id = models.AutoField(primary_key=True)

    def get_or_create_revision(self):
        fields = model_to_dict(
            self,
            exclude=["proposition_services", "id"],
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
    sous_categories = models.ManyToManyField(
        SousCategorieObjet,
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
        verbose_name = "Proposition de service"
        verbose_name_plural = "Proposition de service"

    acteur = models.ForeignKey(
        Acteur,
        on_delete=models.CASCADE,
        null=False,
        related_name="proposition_services",
    )


class RevisionPropositionService(BasePropositionService):
    class Meta:
        verbose_name = "Proposition de service"
        verbose_name_plural = "Proposition de service"

    revision_acteur = models.ForeignKey(
        RevisionActeur,
        on_delete=models.CASCADE,
        null=False,
        related_name="proposition_services",
    )


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
