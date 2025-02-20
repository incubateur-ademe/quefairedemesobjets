import logging

from django.contrib.gis.db import models
from django.db.models.functions import Now
from django.template.loader import render_to_string

from core.models import TimestampedModel
from dags.sources.config.shared_constants import (
    SUGGESTION_ATRAITER,
    SUGGESTION_AVALIDER,
    SUGGESTION_CLUSTERING,
    SUGGESTION_CRAWL_URLS,
    SUGGESTION_ENCOURS,
    SUGGESTION_ERREUR,
    SUGGESTION_REJETEE,
    SUGGESTION_SOURCE_AJOUT,
    SUGGESTION_SOURCE_MODIFICATION,
    SUGGESTION_SOURCE_SUPRESSION,
    SUGGESTION_SUCCES,
)
from data.models.change import SuggestionChange
from qfdmo.models.acteur import (
    Acteur,
    ActeurService,
    ActeurStatus,
    ActeurType,
    LabelQualite,
    PropositionService,
    RevisionActeur,
    Source,
)
from qfdmo.models.action import Action
from qfdmo.models.categorie_objet import SousCategorieObjet

logger = logging.getLogger(__name__)


class SuggestionStatut(models.TextChoices):
    AVALIDER = SUGGESTION_AVALIDER, "À valider"
    REJETEE = SUGGESTION_REJETEE, "Rejetée"
    ATRAITER = SUGGESTION_ATRAITER, "À traiter"
    ENCOURS = SUGGESTION_ENCOURS, "En cours de traitement"
    ERREUR = SUGGESTION_ERREUR, "Fini en erreur"
    SUCCES = SUGGESTION_SUCCES, "Fini avec succès"


class SuggestionCohorteStatut(models.TextChoices):
    AVALIDER = SUGGESTION_AVALIDER, "Suggestions à valider"
    ENCOURS = SUGGESTION_ENCOURS, "Suggestions en cours de traitement"
    SUCCES = SUGGESTION_SUCCES, "Suggestions traitées"


class SuggestionAction(models.TextChoices):
    CRAWL_URLS = SUGGESTION_CRAWL_URLS, "🔗 URLs scannées"
    CLUSTERING = SUGGESTION_CLUSTERING, "regroupement/déduplication des acteurs"
    SOURCE_AJOUT = (
        SUGGESTION_SOURCE_AJOUT,
        "ingestion de source de données - nouveau acteur",
    )
    SOURCE_MODIFICATION = (
        SUGGESTION_SOURCE_MODIFICATION,
        "ingestion de source de données - modification d'acteur existant",
    )
    SOURCE_SUPPRESSION = SUGGESTION_SOURCE_SUPRESSION, "ingestion de source de données"


class SuggestionCohorte(TimestampedModel):
    class Meta:
        verbose_name = "📦 Cohorte"

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
        choices=SuggestionCohorteStatut.choices,
        default=SuggestionCohorteStatut.AVALIDER,
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
            SuggestionAction.SOURCE_MODIFICATION,
            SuggestionAction.SOURCE_SUPPRESSION,
        ]

    @property
    def is_clustering_type(self) -> bool:
        return self.type_action == SuggestionAction.CLUSTERING

    def __str__(self) -> str:
        return f"{self.identifiant_action} - {self.identifiant_execution}"


class Suggestion(models.Model):

    class Meta:
        verbose_name = "1️⃣ Suggestion"

    id = models.AutoField(primary_key=True)
    suggestion_cohorte = models.ForeignKey(
        SuggestionCohorte, on_delete=models.CASCADE, related_name="suggestion_unitaires"
    )
    statut = models.CharField(
        max_length=50,
        choices=SuggestionStatut.choices,
        default=SuggestionStatut.AVALIDER,
    )
    contexte = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Données initiales",
    )
    suggestion = models.JSONField(blank=True, verbose_name="Suggestion de modification")
    cree_le = models.DateTimeField(auto_now_add=True, db_default=Now())
    modifie_le = models.DateTimeField(auto_now=True, db_default=Now())
    metadata = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Metadata de la cohorte, données statistiques",
    )

    @property
    def display_contexte_details(self):
        identifiant_unique = None
        identifiant_uniques = []
        if isinstance(self.contexte, dict) and "identifiant_unique" in self.contexte:
            identifiant_unique = self.contexte.get("identifiant_unique")
        if isinstance(self.contexte, list):
            identifiant_uniques = [
                item.get("identifiant_unique")
                for item in self.contexte
                if isinstance(item, dict)
            ]
        return render_to_string(
            "data/_partials/contexte_details.html",
            {
                "contexte": self.contexte,
                "identifiant_unique": identifiant_unique,
                "identifiant_uniques": identifiant_uniques,
            },
        )

    # FIXME: this display management will be reviewed with PYDANTIC classes which will
    # be used to handle all specificities of suggestions
    @property
    def display_suggestion_details(self):
        template_name = "data/_partials/suggestion_details.html"
        template_context = {"suggestion": self.suggestion}
        if self.suggestion_cohorte.type_action == SuggestionAction.CLUSTERING:
            template_context = self.suggestion
            template_name = "data/_partials/clustering_suggestion_details.html"
        elif (
            self.suggestion_cohorte.type_action == SuggestionAction.SOURCE_SUPPRESSION
            and isinstance(self.suggestion, dict)
        ):
            template_name = "data/_partials/suppression_suggestion_details.html"
            template_context = {
                "identifiant_unique": self.suggestion.get("identifiant_unique")
            }
        elif (
            self.suggestion_cohorte.type_action == SuggestionAction.SOURCE_MODIFICATION
            and isinstance(self.suggestion, dict)
            and isinstance(self.contexte, dict)
        ):
            template_name = "data/_partials/modification_suggestion_details.html"
            updated_fields = {}
            unchanged_fields = {}
            for key, value in self.suggestion.items():
                if key not in self.contexte:
                    continue
                if self.contexte.get(key) != value:
                    updated_fields[key] = {"new": value, "old": self.contexte.get(key)}
                else:
                    unchanged_fields[key] = value
            template_context = {
                "updated_fields": updated_fields,
                "unchanged_fields": unchanged_fields,
            }
        elif (
            self.suggestion_cohorte.type_action == SuggestionAction.SOURCE_AJOUT
            and isinstance(self.suggestion, dict)
        ):
            template_name = "data/_partials/ajout_suggestion_details.html"
        elif self.suggestion_cohorte.type_action == SuggestionAction.CRAWL_URLS:
            template_name = "data/_partials/change_suggestion_details.html"
            template_context = self.suggestion.copy()

        return render_to_string(template_name, template_context)

    # FIXME: this acteur management will be reviewed with PYDANTIC classes which will
    # be used to handle all specificities of suggestions
    def _acteur_fields_to_update(self):
        return {
            field.name: self.suggestion.get(field.name)
            for field in Acteur._meta.get_fields()
            if field.name in self.suggestion
            and field.name
            not in [
                "source",
                "acteur_type",
                "labels",
                "source_id",
                "acteur_type_id",
                "acteur_services",
                "proposition_services",
            ]
        }

    # FIXME: this acteur management will be reviewed with PYDANTIC classes which will
    # be used to handle all specificities of self.suggestions
    def _remove_acteur_linked_objects(self, acteur):
        acteur.proposition_services.all().delete()
        acteur.labels.clear()
        acteur.acteur_services.clear()

    # FIXME: this acteur management will be reviewed with PYDANTIC classes which will
    # be used to handle all specificities of self.suggestions
    def _create_acteur_linked_objects(self, acteur):
        for proposition_service_code in self.suggestion["proposition_service_codes"]:
            proposition_service = PropositionService.objects.create(
                action=Action.objects.get(code=proposition_service_code["action"]),
                acteur=acteur,
            )
            for sous_categorie_code in proposition_service_code["sous_categories"]:
                proposition_service.sous_categories.add(
                    SousCategorieObjet.objects.get(code=sous_categorie_code)
                )
        for label_code in self.suggestion["label_codes"]:
            label = LabelQualite.objects.get(code=label_code)
            acteur.labels.add(label.id)

        for acteurservice_code in self.suggestion["acteur_service_codes"]:
            acteur_service = ActeurService.objects.get(code=acteurservice_code)
            acteur.acteur_services.add(acteur_service.id)

    # FIXME: this acteur management will be reviewed with PYDANTIC classes which will
    # be used to handle all specificities of self.suggestions
    def _create_acteur(self):
        acteur_fields = self._acteur_fields_to_update()
        acteur = Acteur.objects.create(
            **acteur_fields,
            source=Source.objects.get(code=self.suggestion.get("source_code")),
            acteur_type=ActeurType.objects.get(
                code=self.suggestion.get("acteur_type_code")
            ),
        )
        self._create_acteur_linked_objects(acteur)

    # FIXME: this acteur management will be reviewed with PYDANTIC classes which will
    # be used to handle all specificities of self.suggestions
    def _update_acteur(self):
        acteur = Acteur.objects.get(
            identifiant_unique=self.suggestion.get("identifiant_unique")
        )
        for acteur_field in self._acteur_fields_to_update():
            setattr(acteur, acteur_field, self.suggestion.get(acteur_field))
        acteur.source = Source.objects.get(code=self.suggestion.get("source_code"))
        acteur.acteur_type = ActeurType.objects.get(
            code=self.suggestion.get("acteur_type_code")
        )
        acteur.save()

        self._remove_acteur_linked_objects(acteur)
        self._create_acteur_linked_objects(acteur)

    # FIXME: this acteur management will be reviewed with PYDANTIC classes which will
    # be used to handle all specificities of suggestions
    def apply(self):
        if self.suggestion_cohorte.type_action in [
            SuggestionAction.CLUSTERING,
            SuggestionAction.CRAWL_URLS,
        ]:
            changes = self.suggestion["changes"]
            changes.sort(key=lambda x: x["order"])
            for change in changes:
                SuggestionChange(**change).apply()
        elif self.suggestion_cohorte.type_action == SuggestionAction.SOURCE_AJOUT:
            self._create_acteur()
        elif (
            self.suggestion_cohorte.type_action == SuggestionAction.SOURCE_MODIFICATION
        ):
            self._update_acteur()
        elif self.suggestion_cohorte.type_action == SuggestionAction.SOURCE_SUPPRESSION:
            identifiant_unique = self.suggestion["identifiant_unique"]
            Acteur.objects.filter(identifiant_unique=identifiant_unique).update(
                statut=ActeurStatus.SUPPRIME
            )
            RevisionActeur.objects.filter(identifiant_unique=identifiant_unique).update(
                statut=ActeurStatus.SUPPRIME
            )
        else:
            raise Exception(
                "Suggestion cohorte statut is not implemented "
                f"{self.suggestion_cohorte.type_action}"
            )

    # FIXME: DEPRECATED, to be removed
    def display_proposition_service(self):
        return self.suggestion.get("proposition_services", [])

    # FIXME: DEPRECATED, to be removed
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
