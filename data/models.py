from django.contrib.gis.db import models
from django.db.models.functions import Now

from core.models import TimestampedModel
from dags.sources.config.shared_constants import (
    SUGGESTION_ATRAITER,
    SUGGESTION_AVALIDER,
    SUGGESTION_CLUSTERING,
    SUGGESTION_ENCOURS,
    SUGGESTION_ERREUR,
    SUGGESTION_PARTIEL,
    SUGGESTION_REJETEE,
    SUGGESTION_SOURCE_AJOUT,
    SUGGESTION_SOURCE_MISESAJOUR,
    SUGGESTION_SOURCE_SUPRESSION,
    SUGGESTION_SUCCES,
)
from qfdmo.models.acteur import ActeurType, Source


class SuggestionStatut(models.TextChoices):
    AVALIDER = SUGGESTION_AVALIDER, "À valider"
    REJETEE = SUGGESTION_REJETEE, "Rejetée"
    ATRAITER = SUGGESTION_ATRAITER, "À traiter"
    ENCOURS = SUGGESTION_ENCOURS, "En cours de traitement"
    ERREUR = SUGGESTION_ERREUR, "Fini en erreur"
    PARTIEL = SUGGESTION_PARTIEL, "Fini avec succès partiel"
    SUCCES = SUGGESTION_SUCCES, "Fini avec succès"


class SuggestionAction(models.TextChoices):
    CLUSTERING = SUGGESTION_CLUSTERING, "regroupement/déduplication des acteurs"
    SOURCE_AJOUT = (
        SUGGESTION_SOURCE_AJOUT,
        "ingestion de source de données - nouveau acteur",
    )
    SOURCE_MISESAJOUR = (
        SUGGESTION_SOURCE_MISESAJOUR,
        "ingestion de source de données - modification d'acteur existant",
    )
    SOURCE_SUPPRESSION = SUGGESTION_SOURCE_SUPRESSION, "ingestion de source de données"


class SuggestionCohorte(TimestampedModel):
    id = models.AutoField(primary_key=True)
    # On utilise identifiant car le champ n'est pas utilisé pour résoudre une relation
    # en base de données
    identifiant_action = models.CharField(
        verbose_name="Identifiant de l'action", help_text="(ex : dag_id pour Airflow)"
    )
    identifiant_execution = models.CharField(
        verbose_name="Identifiant de l'execution",
        help_text="(ex : run_id pour Airflow)",
    )
    type_action = models.CharField(
        choices=SuggestionAction.choices,
        max_length=50,
        blank=True,
    )
    statut = models.CharField(
        max_length=50,
        choices=SuggestionStatut.choices,
        default=SuggestionStatut.AVALIDER,
    )
    metadata = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Metadata de la cohorte, données statistiques",
    )

    @property
    def is_source_type(self) -> bool:
        return self.type_action in [
            SuggestionAction.SOURCE_AJOUT,
            SuggestionAction.SOURCE_MISESAJOUR,
            SuggestionAction.SOURCE_SUPPRESSION,
        ]

    @property
    def is_clustering_type(self) -> bool:
        return self.type_action == SuggestionAction.CLUSTERING

    def __str__(self) -> str:
        return f"{self.identifiant_action} - {self.identifiant_execution}"


class Suggestion(models.Model):
    id = models.AutoField(primary_key=True)
    suggestion_cohorte = models.ForeignKey(
        SuggestionCohorte, on_delete=models.CASCADE, related_name="suggestion_unitaires"
    )
    statut = models.CharField(
        max_length=50,
        choices=SuggestionStatut.choices,
        default=SuggestionStatut.AVALIDER,
    )
    context = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Contexte de la suggestion : données initiales",
    )
    suggestion = models.JSONField(blank=True, verbose_name="Suggestion de modification")
    cree_le = models.DateTimeField(auto_now_add=True, db_default=Now())
    modifie_le = models.DateTimeField(auto_now=True, db_default=Now())

    # FIXME: A revoir
    def display_acteur_details(self) -> dict:
        displayed_details = {}
        for field, field_value in {
            "nom": "Nom",
            "nom_commercial": "Nom commercial",
            "siret": "SIRET",
            "siren": "SIREN",
            "url": "Site web",
            "email": "Email",
            "telephone": "Téléphone",
            "adresse": "Adresse",
            "adresse_complement": "Complement d'adresse",
            "code_postal": "Code postal",
            "ville": "Ville",
            "commentaires": "Commentaires",
            "horaires_description": "Horaires",
            "latitude": "latitude",
            "longitude": "longitude",
            "identifiant_unique": "identifiant_unique",
            "identifiant_externe": "identifiant_externe",
        }.items():
            if value := self.suggestion.get(field):
                displayed_details[field_value] = value
        if value := self.suggestion.get("acteur_type_id"):
            displayed_details["Type d'acteur"] = ActeurType.objects.get(
                pk=value
            ).libelle
        if value := self.suggestion.get("source_id"):
            displayed_details["Source"] = Source.objects.get(pk=value).libelle
        if value := self.suggestion.get("labels"):
            displayed_details["Labels"] = ", ".join(
                [str(v["labelqualite_id"]) for v in value]
            )
        if value := self.suggestion.get("acteur_services"):
            displayed_details["Acteur Services"] = ", ".join(
                [str(v["acteurservice_id"]) for v in value]
            )

        return displayed_details

    # FIXME: A revoir
    def display_proposition_service(self):
        return self.suggestion.get("proposition_services", [])


class BANCache(models.Model):
    class Meta:
        verbose_name = "Cache BAN"
        verbose_name_plural = "Caches BAN"

    adresse = models.CharField(blank=True, null=True)
    code_postal = models.CharField(blank=True, null=True)
    ville = models.CharField(blank=True, null=True)
    location = models.PointField(blank=True, null=True)
    ban_returned = models.JSONField(blank=True, null=True)
    modifie_le = models.DateTimeField(auto_now=True, db_default=Now())
