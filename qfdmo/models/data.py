from django.contrib.gis.db import models
from django.db.models.functions import Now

from dags.sources.config.shared_constants import (
    SUGGESTION_ATRAITER,
    SUGGESTION_AVALIDER,
    SUGGESTION_CLUSTERING,
    SUGGESTION_ENCOURS,
    SUGGESTION_ERREUR,
    SUGGESTION_PARTIEL,
    SUGGESTION_REJETER,
    SUGGESTION_SOURCE,
    SUGGESTION_SOURCE_AJOUT,
    SUGGESTION_SOURCE_MISESAJOUR,
    SUGGESTION_SOURCE_SUPRESSION,
    SUGGESTION_SUCCES,
)
from qfdmo.models.acteur import ActeurType, Source


class SuggestionStatut(models.TextChoices):
    AVALIDER = SUGGESTION_AVALIDER, "À valider"
    REJETER = SUGGESTION_REJETER, "Rejeter"
    ATRAITER = SUGGESTION_ATRAITER, "À traiter"
    ENCOURS = SUGGESTION_ENCOURS, "En cours de traitement"
    ERREUR = SUGGESTION_ERREUR, "Fini en erreur"
    PARTIEL = SUGGESTION_PARTIEL, "Fini avec succès partiel"
    SUCCES = SUGGESTION_SUCCES, "Fini avec succès"


class SuggestionAction(models.TextChoices):
    CLUSTERING = SUGGESTION_CLUSTERING, "regroupement/déduplication des acteurs"
    SOURCE = (
        SUGGESTION_SOURCE,
        "ingestion de source de données",
    )
    SOURCE_AJOUT = (
        SUGGESTION_SOURCE_AJOUT,
        "ingestion de source de données - nouveau acteur",
    )
    SOURCE_MISESAJOUR = (
        SUGGESTION_SOURCE_MISESAJOUR,
        "ingestion de source de données - modification d'acteur existant",
    )
    SOURCE_SUPPRESSION = SUGGESTION_SOURCE_SUPRESSION, "ingestion de source de données"
    # A venir
    # ENRICHISSEMENT…


class SuggestionCohorte(models.Model):
    id = models.AutoField(primary_key=True)
    # On utilise identifiant car le champ n'est pas utilisé pour résoudre une relation
    # en base de données
    identifiant_action = models.CharField(
        max_length=250, help_text="Identifiant de l'action (ex : dag_id pour Airflow)"
    )
    identifiant_execution = models.CharField(
        max_length=250,
        help_text="Identifiant de l'execution (ex : run_id pour Airflow)",
    )
    type_action = models.CharField(
        choices=SuggestionAction.choices,
        max_length=250,
        blank=True,
    )
    statut = models.CharField(
        max_length=50,
        choices=SuggestionStatut.choices,
        default=SuggestionStatut.AVALIDER,
    )
    metadata = models.JSONField(
        null=True, blank=True, help_text="Metadata de la cohorte, données statistiques"
    )
    cree_le = models.DateTimeField(auto_now_add=True, db_default=Now())
    modifie_le = models.DateTimeField(auto_now=True, db_default=Now())

    @property
    def is_source_type(self) -> bool:
        # FIXME: ajout de tests
        return self.type_action in [
            SuggestionAction.SOURCE,
            SuggestionAction.SOURCE_AJOUT,
            SuggestionAction.SOURCE_MISESAJOUR,
            SuggestionAction.SOURCE_SUPPRESSION,
        ]

    @property
    def is_clustering_type(self) -> bool:
        # FIXME: ajout de tests
        return self.type_action == SuggestionAction.CLUSTERING

    def __str__(self) -> str:
        return f"{self.identifiant_action} - {self.identifiant_execution}"

    def display_meta_data(self) -> dict:
        displayed_metadata = {}
        displayed_metadata["Nombre d'acteur à créer ou mettre à jour"] = (
            self.metadata.get("acteurs_to_add_or_update", 0)
        )
        displayed_metadata["Nombre de duplicats"] = self.metadata.get(
            "number_of_duplicates", 0
        )
        displayed_metadata["Nombre d'acteur à supprimer"] = self.metadata.get(
            "number_of_removed_actors", 0
        )
        return displayed_metadata


class SuggestionUnitaire(models.Model):
    id = models.AutoField(primary_key=True)
    suggestion_cohorte = models.ForeignKey(
        SuggestionCohorte, on_delete=models.CASCADE, related_name="suggestion_unitaires"
    )
    type_action = models.CharField(
        choices=SuggestionAction.choices,
        max_length=250,
        blank=True,
    )
    statut = models.CharField(
        max_length=50,
        choices=SuggestionStatut.choices,
        default=SuggestionStatut.AVALIDER,
    )
    context = models.JSONField(
        null=True, blank=True, help_text="Contexte de la suggestion : données initiales"
    )
    suggestion = models.JSONField(blank=True, help_text="Suggestion de modification")
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
        verbose_name_plural = "Cache BAN"

    adresse = models.CharField(max_length=255, blank=True, null=True)
    code_postal = models.CharField(max_length=255, blank=True, null=True)
    ville = models.CharField(max_length=255, blank=True, null=True)
    location = models.PointField(blank=True, null=True)
    ban_returned = models.JSONField(blank=True, null=True)
    modifie_le = models.DateTimeField(auto_now=True, db_default=Now())
