import logging
import re
from datetime import datetime

from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from more_itertools import first, flatten
from pydantic import BaseModel, ConfigDict

from core.models.mixin import TimestampedModel
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
from data.models.apply_models.abstract_apply_model import AbstractApplyModel
from data.models.apply_models.source_apply_model import SourceApplyModel
from data.models.change import SuggestionChange
from data.models.utils import data_latlong_to_location
from qfdmo.models.acteur import (
    Acteur,
    ActeurService,
    ActeurStatus,
    ActeurType,
    DisplayedActeur,
    LabelQualite,
    PerimetreADomicile,
    PropositionService,
    RevisionActeur,
    Source,
)
from qfdmo.models.action import Action
from qfdmo.models.categorie_objet import SousCategorieObjet

logger = logging.getLogger(__name__)


class SuggestionStatut(models.TextChoices):
    AVALIDER = SUGGESTION_AVALIDER, "🟠 À valider"
    REJETEE = SUGGESTION_REJETEE, "🔴 Rejetée"
    ATRAITER = SUGGESTION_ATRAITER, "⏳ À traiter"
    ENCOURS = SUGGESTION_ENCOURS, "⏳ En cours de traitement"
    ERREUR = SUGGESTION_ERREUR, "❌ Finie en erreur"
    SUCCES = SUGGESTION_SUCCES, "✅ Finie avec succès"


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


class SuggestionCohorteSerializer(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    suggestion_cohorte: SuggestionCohorte
    statut: str
    action: str
    identifiant_unique: str
    fields_groups: list[tuple] = []
    fields_values: dict = {}  # dict[str, dict[str, str]]
    acteur: Acteur | None = None
    acteur_overridden_by: RevisionActeur | None = None  # Revision or Parent

    def to_dict(self) -> dict:
        return self.model_dump()

    def to_json(self) -> str:
        # We rely on to_dict to ensure the use of model_to_dict
        import json

        data = self.model_dump()
        data["acteur"] = self.acteur.identifiant_unique if self.acteur else None
        data["acteur_overridden_by"] = (
            self.acteur_overriden_by.identifiant_unique
            if self.acteur_overriden_by
            else None
        )
        data["suggestion_cohorte"] = self.suggestion_cohorte.id

        return json.dumps(data)


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
    NOT_EDITABLE_FIELDS = [
        "acteur_service_codes",
        "identifiant_externe",
        "identifiant_unique",
        "label_codes",
        "proposition_service_codes",
        "source_code",
        "acteur_type_code",
    ]

    ORDERED_FIELDS = [
        ("lieu_prestation",),
        ("identifiant_unique",),
        ("source_code",),
        ("identifiant_externe",),
        ("nom",),
        ("nom_commercial",),
        ("nom_officiel",),
        ("siret",),
        ("siren",),
        ("naf_principal",),
        ("description",),
        ("acteur_type_code",),
        ("url",),
        ("email",),
        ("telephone",),
        ("adresse",),
        ("adresse_complement",),
        ("code_postal",),
        ("ville",),
        (
            "latitude",
            "longitude",
        ),
        ("horaires_osm",),
        ("horaires_description",),
        ("public_accueilli",),
        ("reprise",),
        ("exclusivite_de_reprisereparation",),
        ("uniquement_sur_rdv",),
        ("consignes_dacces",),
        ("statut",),
        ("commentaires",),
        ("label_codes",),
        ("acteur_service_codes",),
        ("proposition_service_codes",),
    ]

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

    def __str__(self) -> str:
        libelle = self.suggestion_cohorte.identifiant_action
        if self.acteur:
            libelle += f" - {self.acteur.identifiant_unique}"
        return libelle

    def acteur_overridden_by(self) -> RevisionActeur | None:
        return (
            self.revision_acteur.parent
            if self.revision_acteur and self.revision_acteur.parent
            else self.revision_acteur
        )

    @property
    def displayed_acteur_uuid(self) -> str | None:
        acteur = self.acteur_overridden_by() or self.acteur
        if acteur:
            displayed_acteur = DisplayedActeur.objects.filter(
                identifiant_unique=acteur.identifiant_unique
            ).first()
            return displayed_acteur.uuid if displayed_acteur else None
        return None

    def get_identifiant_unique_from_suggestion_unitaires(self) -> str:
        """
        Get the identifiant_unique from the suggestion_unitaires for the Acteur model
        Useful for SOURCE_AJOUT
        """
        return first(
            (
                suggestion_unitaire.valeurs[
                    suggestion_unitaire.champs.index("identifiant_unique")
                ]
                for suggestion_unitaire in self.suggestion_unitaires.filter(
                    suggestion_modele="Acteur"
                )
                if "identifiant_unique" in suggestion_unitaire.champs
            ),
            "",
        )

    def _build_serializer_common_fields(self) -> dict:
        """Build common fields for SuggestionCohorteSerializer"""
        return {
            "id": self.id,
            "suggestion_cohorte": self.suggestion_cohorte,
            "statut": self.get_statut_display(),
            "action": self.suggestion_cohorte.type_action,
        }

    def serialize(self) -> SuggestionCohorteSerializer:
        def _flatten_suggestion_unitaires(
            suggestion_unitaires: dict[tuple, list],
        ) -> dict:
            return {
                k: v
                for k, v in zip(
                    flatten(suggestion_unitaires.keys()),
                    flatten(suggestion_unitaires.values()),
                )
            }

        def _get_ordered_fields_groups(
            acteur_suggestion_unitaires: dict,
            acteur_overridden_by_suggestion_unitaires: dict | None = None,
        ) -> list[tuple]:
            fields_groups = list(
                set(acteur_suggestion_unitaires.keys())
                | set(
                    acteur_overridden_by_suggestion_unitaires.keys()
                    if acteur_overridden_by_suggestion_unitaires
                    else set()
                )
            )

            if any(
                fields not in SuggestionGroupe.ORDERED_FIELDS
                for fields in fields_groups
            ):
                raise ValueError(
                    f"""fields in fields_groups are not in ORDERED_FIELDS:
                                {fields_groups=}
                                {SuggestionGroupe.ORDERED_FIELDS=}"""
                )
            return [
                fields
                for fields in SuggestionGroupe.ORDERED_FIELDS
                if fields in fields_groups
            ]

        # Get all suggestion_unitaires
        suggestion_unitaires = list(self.suggestion_unitaires.all())

        # Get all suggestion_unitaires for Acteur
        acteur_suggestion_unitaires = {
            tuple(unit.champs): unit.valeurs
            for unit in suggestion_unitaires
            if unit.suggestion_modele == "Acteur"
        }
        acteur_overridden_by_suggestion_unitaires = {
            tuple(unit.champs): unit.valeurs
            for unit in suggestion_unitaires
            if unit.suggestion_modele == "RevisionActeur"
        }
        fields_groups = _get_ordered_fields_groups(
            acteur_suggestion_unitaires, acteur_overridden_by_suggestion_unitaires
        )
        acteur_overridden_by_suggestion_unitaires_by_field = (
            _flatten_suggestion_unitaires(acteur_overridden_by_suggestion_unitaires)
        )

        if self.suggestion_cohorte.type_action == SuggestionAction.SOURCE_AJOUT:
            identifiant_unique = self.get_identifiant_unique_from_suggestion_unitaires()
            fields_values = {
                key: {
                    "displayed_value": value,
                    "new_value": value,
                    "updated_displayed_value": (
                        acteur_overridden_by_suggestion_unitaires_by_field.get(key, "")
                    ),
                }
                for fields, values in acteur_suggestion_unitaires.items()
                for key, value in zip(fields, values)
            }
            return SuggestionCohorteSerializer(
                **self._build_serializer_common_fields(),
                identifiant_unique=identifiant_unique,
                fields_groups=fields_groups,
                fields_values=fields_values,
            )

        acteur = self.acteur
        acteur_overridden_by = self.acteur_overridden_by()

        fields_groups = _get_ordered_fields_groups(acteur_suggestion_unitaires)

        fields = [key for keys in fields_groups for key in keys]

        acteur_suggestion_unitaires_by_field = _flatten_suggestion_unitaires(
            acteur_suggestion_unitaires
        )
        displayed_values = {}
        for field in fields:
            value = (
                getattr(acteur_overridden_by, field) if acteur_overridden_by else None
            )
            if value is None:
                value = acteur_suggestion_unitaires_by_field.get(field)
                if value is None:
                    value = getattr(acteur, field)
            displayed_values[field] = str(value)

        fields_values = {}
        for field in fields:
            fields_values[field] = {
                "displayed_value": str(displayed_values.get(field, "")),
                "updated_displayed_value": (
                    str(
                        acteur_overridden_by_suggestion_unitaires_by_field.get(
                            field, ""
                        )
                    )
                ),
                "new_value": str(acteur_suggestion_unitaires_by_field.get(field, "")),
                "old_value": str(getattr(acteur, field, "")),
            }

        return SuggestionCohorteSerializer(
            **self._build_serializer_common_fields(),
            fields_groups=fields_groups,
            fields_values=fields_values,
            acteur=acteur,
            identifiant_unique=acteur.identifiant_unique,
            acteur_overridden_by=acteur_overridden_by,
        )

    def _validate_proposed_updates(
        self, values_to_update: dict, fields_values: dict
    ) -> dict:
        """
        Check if the proposed updates are valid
        Returns a dictionary of errors (empty if valid)
        """
        # Validate the RevisionActeur with the proposed values

        if "longitude" in values_to_update or "latitude" in values_to_update:
            for coord_field in ["longitude", "latitude"]:
                try:
                    values_to_update[coord_field] = values_to_update.get(
                        coord_field,
                        fields_values.get(coord_field, {}).get("displayed_value", ""),
                    )
                except (ValueError, KeyError) as e:
                    logger.warning(f"ValueError for {coord_field}: {e}")
                    return {coord_field: f"{coord_field} must be a float: {e}"}

        try:
            values_to_update = data_latlong_to_location(values_to_update)
        except (ValueError, KeyError) as e:
            logger.warning(f"ValueError for : {e}")
            return {
                "latitude": f"latitude must be a float: {e}",
                "longitude": f"longitude must be a float: {e}",
            }
        try:
            revision_acteur = RevisionActeur(
                **data_latlong_to_location(values_to_update)
            )
            revision_acteur.full_clean()
        except ValidationError as e:
            logger.warning(f"RevisionActeur is not valid: {e}")
            return e.error_dict
        except TypeError as e:
            logger.warning(f"RevisionActeur is not valid: {e}")
            return {"error": str(e)}

        return {}

    def update_from_serialized_data(
        self, fields_values: dict, fields_groups: list[tuple]
    ) -> tuple[bool, dict | None]:
        """
        Try to create the RevisionActeur Suggestions
        Returns a tuple with:
        - bool: True if the update is successful, False otherwise
        - dict: None if the update is successful, a dictionary of errors otherwise
          general errors are under the key "error"
          field errors are under the key "field_name"
        """
        # Build mapping of existing revision suggestions by field
        revision_suggestion_unitaire_by_field = {
            field: value
            for unit in self.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur"
            )
            for field, value in zip(unit.champs, unit.valeurs)
        }

        # Determine which fields need to be updated
        values_to_update = {
            field: by_state_values["updated_displayed_value"]
            for field, by_state_values in fields_values.items()
            if field not in SuggestionGroupe.NOT_EDITABLE_FIELDS
            and "updated_displayed_value" in by_state_values
            and (
                by_state_values["updated_displayed_value"]
                != by_state_values["displayed_value"]
                or (
                    field in revision_suggestion_unitaire_by_field
                    and revision_suggestion_unitaire_by_field[field]
                    != by_state_values["updated_displayed_value"]
                )
            )
        }
        values_to_update = {k: v for k, v in values_to_update.items() if v != ""}

        # Validate proposed updates
        if errors := self._validate_proposed_updates(values_to_update, fields_values):
            return False, errors

        # Create or update SuggestionUnitaire objects
        for fields in fields_groups:
            if any(field in values_to_update for field in fields):
                suggestion_unitaire, _ = SuggestionUnitaire.objects.get_or_create(
                    suggestion_groupe=self,
                    champs=fields,
                    suggestion_modele="RevisionActeur",
                    defaults={
                        "acteur": self.acteur,
                        "revision_acteur": self.revision_acteur,
                    },
                )
                suggestion_unitaire.valeurs = [
                    values_to_update.get(field, "") for field in fields
                ]
                suggestion_unitaire.save()

        return True, None

    def _get_apply_models(self) -> list[AbstractApplyModel]:
        if self.suggestion_cohorte.type_action in [
            SuggestionAction.SOURCE_AJOUT,
            SuggestionAction.SOURCE_MODIFICATION,
            SuggestionAction.SOURCE_SUPPRESSION,
        ]:
            apply_models = []
            # get the suggestion_unitaires on Acteur model
            acteur_suggestion_unitaires = self.suggestion_unitaires.filter(
                suggestion_modele="Acteur"
            ).all()
            if not acteur_suggestion_unitaires.exists():
                raise ValueError("No acteur suggestion unitaires found")
            identifiant_unique = (
                acteur_suggestion_unitaires.first().acteur_id
                or self.get_identifiant_unique_from_suggestion_unitaires()
            )
            apply_models.append(
                SourceApplyModel(
                    identifiant_unique=identifiant_unique,
                    order=0,
                    acteur_model=Acteur,
                    data={
                        champ: valeur
                        for suggestion_unitaire in acteur_suggestion_unitaires
                        for champ, valeur in zip(
                            suggestion_unitaire.champs, suggestion_unitaire.valeurs
                        )
                    },
                )
            )

            # get the suggestion_unitaires on RevisionActeur model
            revision_acteur_suggestion_unitaires = self.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur"
            ).all()
            if first := revision_acteur_suggestion_unitaires.first():
                identifiant_unique = first.revision_acteur_id or identifiant_unique
            apply_models.append(
                SourceApplyModel(
                    identifiant_unique=identifiant_unique,
                    order=1,
                    acteur_model=RevisionActeur,
                    data={
                        champ: valeur
                        for suggestion_unitaire in (
                            revision_acteur_suggestion_unitaires
                        )
                        for champ, valeur in zip(
                            suggestion_unitaire.champs, suggestion_unitaire.valeurs
                        )
                    },
                )
            )
            return apply_models
        return []

    def apply(self):
        apply_models = self._get_apply_models()
        for apply_model in sorted(apply_models, key=lambda x: x.order):
            apply_model.apply()


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
    parametres = models.JSONField(blank=True, default=dict)
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
    modifie_le = models.DateTimeField(auto_now=True)
