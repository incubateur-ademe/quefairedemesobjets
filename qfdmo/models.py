from django.db import models
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


class SousCategorieObjet(NomAsNaturalKeyModel):
    class Meta:
        verbose_name = "Sous catégorie d'objets"
        verbose_name_plural = "Sous catégories d'objets"

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)
    lvao_id = models.IntegerField(blank=True, null=True)
    categorie = models.ForeignKey(
        CategorieObjet, on_delete=models.CASCADE, blank=True, null=True
    )
    code = models.CharField(max_length=10, unique=True, blank=False, null=False)

    @property
    def sanitized_nom(self) -> str:
        return unidecode(self.nom).upper()


class Action(NomAsNaturalKeyModel):
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)
    lvao_id = models.IntegerField(blank=True, null=True)


class ActeurService(NomAsNaturalKeyModel):
    class Meta:
        verbose_name = "Service proposé"
        verbose_name_plural = "Services proposés"

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)
    lvao_id = models.IntegerField(blank=True, null=True)
    actions = models.ManyToManyField(Action)


class ActeurType(NomAsNaturalKeyModel):
    class Meta:
        verbose_name = "Type d'acteur"
        verbose_name_plural = "Types d'acteur"

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)
    lvao_id = models.IntegerField(blank=True, null=True)


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
