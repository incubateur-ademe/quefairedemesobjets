"""
DEPRECATED, should use the data django app
"""

from django.contrib.gis.db import models

from dags.sources.config.shared_constants import (
    DAGRUN_FINISHED,
    DAGRUN_REJECTED,
    DAGRUN_TOINSERT,
    DAGRUN_TOVALIDATE,
)
from qfdmo.models.acteur import ActeurType, Source


class DagRunStatus(models.TextChoices):
    TO_VALIDATE = DAGRUN_TOVALIDATE
    TO_INSERT = DAGRUN_TOINSERT
    REJECTED = DAGRUN_REJECTED
    FINISHED = DAGRUN_FINISHED


class DagRun(models.Model):
    id = models.AutoField(primary_key=True)
    dag_id = models.CharField(max_length=250)
    run_id = models.CharField(max_length=250)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=50,
        choices=DagRunStatus.choices,
        default=DagRunStatus.TO_VALIDATE,
    )
    # {to_create : 134, to_update : 0, to_delete : 0, to_ignore : 0, errors : 0}
    meta_data = models.JSONField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.dag_id} - {self.run_id}"

    def display_meta_data(self) -> dict:
        displayed_metadata = {}
        displayed_metadata["Nombre d'acteur à créer"] = self.meta_data.get(
            "added_rows", 0
        )
        displayed_metadata["Nombre de duplicats"] = self.meta_data.get(
            "number_of_duplicates", 0
        )
        displayed_metadata["Nombre d'acteur MAJ"] = self.meta_data.get(
            "updated_rows", 0
        )
        return displayed_metadata


class DagRunChangeType(models.Choices):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class DagRunChange(models.Model):
    id = models.AutoField(primary_key=True)
    dag_run = models.ForeignKey(
        DagRun, on_delete=models.CASCADE, related_name="dagrunchanges"
    )
    change_type = models.CharField(max_length=50, choices=DagRunChangeType.choices)
    meta_data = models.JSONField(null=True, blank=True)
    # metadata : JSON of any error or information about the line to change
    row_updates = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=DagRunStatus.choices,
        default=DagRunStatus.TO_VALIDATE,
    )

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
            if value := self.row_updates.get(field):
                displayed_details[field_value] = value
        if value := self.row_updates.get("acteur_type_id"):
            displayed_details["Type d'acteur"] = ActeurType.objects.get(
                pk=value
            ).libelle
        if value := self.row_updates.get("source_id"):
            displayed_details["Source"] = Source.objects.get(pk=value).libelle
        if value := self.row_updates.get("labels"):
            displayed_details["Labels"] = ", ".join(
                [str(v["labelqualite_id"]) for v in value]
            )
        if value := self.row_updates.get("acteur_services"):
            displayed_details["Acteur Services"] = ", ".join(
                [str(v["acteurservice_id"]) for v in value]
            )

        return displayed_details

    def display_proposition_service(self):
        return self.row_updates.get("proposition_services", [])

    def update_row_update_field(self, field_name, value):
        if self.row_updates is None:
            self.row_updates = {}

        if field_name in self.row_updates and self.row_updates[field_name] == value:
            del self.row_updates[field_name]
        else:
            self.row_updates[field_name] = value

        self.save()

    def update_row_update_candidate(self, status, index):
        if self.row_updates is None:
            self.row_updates = {}

        if (
            self.status == status
            and "best_candidat_index" in self.row_updates
            and self.row_updates["best_candidat_index"] == index
        ):
            self.status = DagRunStatus.TO_VALIDATE.value
            del self.row_updates["best_candidat_index"]

        else:
            self.status = status
            self.row_updates["best_candidat_index"] = index

        self.save()

    def get_candidat(self, index):
        return self.row_updates["ae_result"][int(index) - 1]
