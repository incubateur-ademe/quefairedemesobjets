from django.contrib.gis.db import models


class DagRunStatus(models.Choices):
    TO_VALIDATE = "TO_VALIDATE"
    TO_INSERT = "TO_INSERT"
    REJECTED = "REJECTED"
    FINISHED = "FINISHED"


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


class DagRunChangeType(models.Choices):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class DagRunChange(models.Model):
    id = models.AutoField(primary_key=True)
    dag_run = models.ForeignKey(DagRun, on_delete=models.CASCADE)
    change_type = models.CharField(max_length=50, choices=DagRunChangeType.choices)
    meta_data = models.JSONField(null=True, blank=True)
    # metadata : JSON of any error or information about the line to change
    row_updates = models.JSONField(null=True, blank=True)
    # row_updates : JSON of acteur to update or create to store on row_updates
    # {
    #     "nom": "NOM",
    #     "description": null,
    #     "identifiant_unique": "IDENTIFIANT_UNIQUE",
    #     "adresse": "ADRESSE",
    #     "adresse_complement": "…",
    #     "code_postal": "CODE_POSTAL",
    #     "ville": "VILLE",
    #     "url": "…",
    #     "email": "…",
    #     "telephone": "…",
    #     "nom_commercial": "…",
    #     "nom_officiel": "…",
    #     "label_reparacteur": false,
    #     "siret": "49819433100019",
    #     "identifiant_externe": "144103",
    #     "statut": "ACTIF",
    #     "naf_principal": "62.02A",
    #     "commentaires": null,
    #     "horaires_osm": null,
    #     "horaires_description": null,
    #     "acteur_type_id": 3,
    #     "source_id": 4,
    #     "location": [2.9043527, 42.6949013],
    #     "proposition_services": [
    #         {
    #             "action_id": 1,
    #             "acteur_service_id": 15,
    #             "sous_categories": [90]
    #         }
    #     ]
    # }
