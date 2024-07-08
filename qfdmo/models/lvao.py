from django.contrib.gis.db import models

from qfdmo.models import (
    ActeurService,
    ActeurType,
    Action,
    NomAsNaturalKeyModel,
    SousCategorieObjet,
)


class LVAOBase(NomAsNaturalKeyModel):
    class Meta:
        app_label = "qfdmo"
        verbose_name = "Acteur LVAO"
        verbose_name_plural = "Acteurs LVAO"

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, blank=False, null=False)  # title
    identifiant_unique = models.CharField(
        max_length=255, blank=True, null=True, unique=True
    )  # UniqueId


class LVAOBaseRevision(NomAsNaturalKeyModel):
    class Meta:
        app_label = "qfdmo"
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
    exclusivite_de_reprisereparation = models.BooleanField(
        verbose_name="Exclusivité de réparation",
        default=False,
        help_text="Ce champ correspond dans les données des éco-organisme "
        "à exclusivite_de_reprisereparation. "
        "Cette notion n'étant pas encore présente dans l'application, "
        "il est considéré comme exclusivité de réparation uniquement.",
    )

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
