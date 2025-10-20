import logging
import re
from datetime import datetime

from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models.functions import Now
from django.template.loader import render_to_string

from core.models.mixin import TimestampedModel
from data.models.change import SuggestionChange
from qfdmo.models.acteur import (
    Acteur,
    ActeurService,
    ActeurStatus,
    ActeurType,
    LabelQualite,
    PerimetreADomicile,
    PropositionService,
    RevisionActeur,
    Source,
)
from qfdmo.models.action import Action
from qfdmo.models.categorie_objet import SousCategorieObjet

logger = logging.getLogger(__name__)

# Suggestion statut
SUGGESTION_AVALIDER = "AVALIDER"
SUGGESTION_REJETEE = "REJETEE"
SUGGESTION_ATRAITER = "ATRAITER"
SUGGESTION_ENCOURS = "ENCOURS"
SUGGESTION_ERREUR = "ERREUR"
SUGGESTION_SUCCES = "SUCCES"

# SuggestionCohorte type_action
SUGGESTION_CRAWL_URLS = "CRAWL_URLS"
SUGGESTION_CLUSTERING = "CLUSTERING"
SUGGESTION_SOURCE_AJOUT = "SOURCE_AJOUT"
SUGGESTION_SOURCE_MODIFICATION = "SOURCE_MODIFICATION"
SUGGESTION_SOURCE_SUPRESSION = "SOURCE_SUPRESSION"


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
    ENRICH_ACTEURS_CLOSED = "ENRICH_ACTEURS_CLOSED", "🚪 Acteurs fermés"
    ENRICH_ACTEURS_RGPD = "ENRICH_ACTEURS_RGPD", "🕵 Anonymisation RGPD"
    ENRICH_ACTEURS_VILLES_TYPO = (
        "ENRICH_ACTEURS_VILLES_TYPO",
        "🏙️ Acteurs villes typographiques",
    )
    ENRICH_ACTEURS_VILLES_NEW = (
        "ENRICH_ACTEURS_VILLES_NEW",
        "🏙️ Acteurs villes nouvelles",
    )
    ENRICH_ACTEURS_CP_TYPO = (
        "ENRICH_ACTEURS_CP_TYPO",
        "🏙️ Acteurs codes postaux non conformes",
    )
    ENRICH_REVISION_ACTEURS_CP_TYPO = (
        "ENRICH_REVISION_ACTEURS_CP_TYPO",
        "🏙️ Revision acteurs codes postaux non conformes",
    )
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
        verbose_name = "1️⃣ Suggestion Cohorte"
        verbose_name_plural = "1️⃣ Suggestions Cohortes"

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
    # TODO: once all suggestions migrated to pydantic, we should be able to remove this
    # field as all changes will be done generically through changes. apply() method
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

    @property
    def execution_datetime(self) -> str:
        execution_datetime = self.identifiant_execution
        date_match = re.search(
            r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", execution_datetime
        )
        if date_match:
            # Conversion et formatage de la date en une seule ligne
            execution_datetime = datetime.fromisoformat(date_match.group(1)).strftime(
                "%d/%m/%Y %H:%M"
            )
        return execution_datetime

    def __str__(self) -> str:
        return f"""{self.id} - {self.identifiant_action} -- {self.execution_datetime}"""


class Suggestion(TimestampedModel):

    class Meta:
        verbose_name = "2️⃣ Suggestion - Bientôt déprécié"
        verbose_name_plural = "2️⃣ Suggestions - Bientôt déprécié"

    id = models.AutoField(primary_key=True)
    suggestion_cohorte = models.ForeignKey(
        SuggestionCohorte, on_delete=models.CASCADE, related_name="suggestions"
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

        context = {
            "contexte": self.contexte,
            "identifiant_unique": identifiant_unique,
            "identifiant_uniques": identifiant_uniques,
        }

        # Opening details toggle by default
        if self.suggestion_cohorte.type_action in [
            SuggestionAction.CLUSTERING,
            SuggestionAction.CRAWL_URLS,
            SuggestionAction.ENRICH_ACTEURS_RGPD,
            SuggestionAction.ENRICH_ACTEURS_VILLES_TYPO,
            SuggestionAction.ENRICH_ACTEURS_VILLES_NEW,
        ]:
            context["details_open"] = True

        return render_to_string("data/_partials/contexte_details.html", context)

    # FIXME: this display management will be reviewed with PYDANTIC classes which will
    # be used to handle all specificities of suggestions
    @property
    def display_suggestion_details(self):
        template_name = "data/_partials/suggestion_details.html"
        template_context = {"contexte": self.contexte, "suggestion": self.suggestion}

        # Suggestions leveraging the PYDANTIC SuggestionChange model
        if self.suggestion_cohorte.type_action in [
            SuggestionAction.ENRICH_ACTEURS_CLOSED,
            SuggestionAction.ENRICH_ACTEURS_RGPD,
            SuggestionAction.ENRICH_ACTEURS_VILLES_TYPO,
            SuggestionAction.ENRICH_ACTEURS_VILLES_NEW,
            SuggestionAction.CRAWL_URLS,
            SuggestionAction.CLUSTERING,
            SuggestionAction.ENRICH_ACTEURS_CP_TYPO,
            SuggestionAction.ENRICH_REVISION_ACTEURS_CP_TYPO,
        ]:
            template_name = "data/_partials/suggestion_details_changes.html"
            template_context = {"suggestion": self}

        # TODO: suggestions to migrate to PYDANTIC classes
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

            valid_items = [
                (key, value)
                for key, value in self.suggestion.items()
                if key in self.contexte and key != "location"
            ]
            updated_fields = {
                key: value
                for key, value in valid_items
                if self.contexte.get(key) != value
            }
            unchanged_fields = {
                key: value
                for key, value in valid_items
                if self.contexte.get(key) == value
            }

            template_context = {
                "updated_fields": updated_fields,
                "unchanged_fields": unchanged_fields,
                "suggestion_contexte": self.contexte,
            }
        elif (
            self.suggestion_cohorte.type_action == SuggestionAction.SOURCE_AJOUT
            and isinstance(self.suggestion, dict)
        ):
            template_name = "data/_partials/ajout_suggestion_details.html"

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
        acteur.perimetre_adomiciles.all().delete()
        acteur.labels.clear()
        acteur.acteur_services.clear()

    # FIXME: this acteur management will be reviewed with PYDANTIC classes which will
    # be used to handle all specificities of self.suggestions
    def _create_acteur_linked_objects(self, acteur):
        if "proposition_service_codes" in self.suggestion:
            for proposition_service_code in self.suggestion[
                "proposition_service_codes"
            ]:
                proposition_service = PropositionService.objects.create(
                    action=Action.objects.get(code=proposition_service_code["action"]),
                    acteur=acteur,
                )
                for sous_categorie_code in proposition_service_code["sous_categories"]:
                    proposition_service.sous_categories.add(
                        SousCategorieObjet.objects.get(code=sous_categorie_code)
                    )
        if "perimetre_adomicile_codes" in self.suggestion:
            for perimetre_adomicile_code in self.suggestion[
                "perimetre_adomicile_codes"
            ]:
                PerimetreADomicile.objects.create(
                    type=perimetre_adomicile_code["type"],
                    valeur=perimetre_adomicile_code["valeur"],
                    acteur=acteur,
                )
        if "label_codes" in self.suggestion:
            for label_code in self.suggestion["label_codes"]:
                label = LabelQualite.objects.get(code=label_code)
                acteur.labels.add(label.id)
        if "acteur_service_codes" in self.suggestion:
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

    def apply(self):
        # Suggestions leveraging the PYDANTIC SuggestionChange model
        if self.suggestion_cohorte.type_action in [
            SuggestionAction.CLUSTERING,
            SuggestionAction.CRAWL_URLS,
            SuggestionAction.ENRICH_ACTEURS_CLOSED,
            SuggestionAction.ENRICH_ACTEURS_RGPD,
            SuggestionAction.ENRICH_ACTEURS_VILLES_TYPO,
            SuggestionAction.ENRICH_ACTEURS_VILLES_NEW,
            SuggestionAction.ENRICH_ACTEURS_CP_TYPO,
            SuggestionAction.ENRICH_REVISION_ACTEURS_CP_TYPO,
        ]:
            changes = self.suggestion["changes"]
            changes.sort(key=lambda x: x["order"])
            for change in changes:
                SuggestionChange(**change).apply()

        # FIXME: this acteur management will be reviewed with PYDANTIC classes
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


class SuggestionGroupe(TimestampedModel):

    class Meta:
        verbose_name = "2️⃣ ⏳ ⚠️ Suggestion Groupe - Livraison prochainement"
        verbose_name_plural = "2️⃣ ⏳ ⚠️ Suggestions Groupes - Livraison prochainement"

    id = models.AutoField(primary_key=True)
    suggestion_cohorte = models.ForeignKey(
        SuggestionCohorte, on_delete=models.CASCADE, related_name="suggestion_groupes"
    )
    statut = models.CharField(
        max_length=50,
        choices=SuggestionStatut.choices,
        default=SuggestionStatut.AVALIDER,
    )
    acteur = models.ForeignKey(
        Acteur,
        on_delete=models.CASCADE,
        related_name="suggestion_groupes",
        null=True,
    )
    revision_acteur = models.ForeignKey(
        RevisionActeur,
        on_delete=models.CASCADE,
        related_name="suggestion_groupes",
        null=True,
    )
    contexte = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Données initiales",
    )
    metadata = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Metadata de la cohorte, données statistiques",
    )


class SuggestionUnitaire(TimestampedModel):

    class Meta:
        verbose_name = "3️⃣ ⏳ ⚠️ Suggestion Unitaire - Livraison prochainement"
        verbose_name_plural = "3️⃣ ⏳ ⚠️ Suggestions Unitaires - Livraison prochainement"

    id = models.AutoField(primary_key=True)
    suggestion_groupe = models.ForeignKey(
        SuggestionGroupe, on_delete=models.CASCADE, related_name="suggestion_unitaires"
    )
    statut = models.CharField(
        max_length=50,
        choices=SuggestionStatut.choices,
        default=SuggestionStatut.AVALIDER,
    )
    acteur = models.ForeignKey(
        Acteur,
        on_delete=models.CASCADE,
        related_name="suggestion_unitaires",
        null=True,
    )
    revision_acteur = models.ForeignKey(
        RevisionActeur,
        on_delete=models.CASCADE,
        related_name="suggestion_unitaires",
        null=True,
    )
    ordre = models.IntegerField(default=1, blank=True)
    raison = models.TextField(blank=True, db_default="", default="")
    parametres = models.JSONField(blank=True, db_default="", default="")
    suggestion_modele = models.CharField(
        max_length=255, blank=True, db_default="", default="", choices=[]
    )
    champs = ArrayField(
        models.TextField(),
        blank=True,
        default=list,
    )
    valeurs = ArrayField(
        models.TextField(),
        blank=True,
        default=list,
    )


class SuggestionLog(TimestampedModel):
    class Meta:
        verbose_name = "📝 Suggestion Log"

    class SuggestionLogLevel(models.TextChoices):
        WARNING = "WARNING", "Warning"
        ERROR = "ERROR", "Error"

    id = models.AutoField(primary_key=True)
    suggestion_cohorte = models.ForeignKey(
        SuggestionCohorte,
        on_delete=models.CASCADE,
        related_name="suggestion_logs",
        null=True,
    )
    suggestion_groupe = models.ForeignKey(
        SuggestionGroupe,
        on_delete=models.CASCADE,
        related_name="suggestion_logs",
        null=True,
    )
    suggestion_unitaire = models.ForeignKey(
        SuggestionUnitaire,
        on_delete=models.CASCADE,
        related_name="suggestion_logs",
        null=True,
    )
    identifiant_unique = models.CharField(max_length=255, blank=True, default="")
    niveau_de_log = models.CharField(
        max_length=50,
        choices=SuggestionLogLevel.choices,
        default=SuggestionLogLevel.WARNING,
    )
    fonction_de_transformation = models.CharField(max_length=255)
    origine_colonnes = ArrayField(models.CharField(max_length=255), null=True)
    origine_valeurs = ArrayField(models.TextField(), null=True)
    destination_colonnes = ArrayField(models.CharField(max_length=255), null=True)
    message = models.TextField(blank=True, db_default="", default="")


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
