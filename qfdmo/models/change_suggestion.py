"""
Modèle de données Django pour les suggestions de changements
"""

from textwrap import dedent

from django.db import models
from django.utils import timezone


class ChangeSuggestion(models.Model):
    """
    Modèle de données Django pour les suggestions de changements

    Gestion des données:
     - change_data: ne doit contenir que le strict minimum pour gérer le changement
        (ex: pour un cluster d'acteur = cluster_id -> acteur_id). Ne pas stocker
        d'autres données qui pourraient devenir obsolètes au moment de la revue.
        Si on souhaite fournir de la donnée supplémentaire, il faut le faire à
        la vollée (ex: au moment de l'affichage ou de l'export)

     - debug_data (optionnel): si on veut expliquer comment on est arrivé à cette
        suggestion, on peut stocker ici des données de debug (ex: valeurs des champs,
        scores de similarité, etc.)
    """

    class Meta:
        db_table = "qfdmo_change_suggestions"
        verbose_name = "Suggestion de changement"
        verbose_name_plural = "Suggestions de changements"

    # ------------------------------------
    # Champs liés à la suggestion
    # ------------------------------------
    id = models.AutoField(primary_key=True)
    task_run_id = models.CharField(
        max_length=200, verbose_name="ID de la tâche qui a généré la suggestion"
    )
    task_run_at = models.DateTimeField(
        verbose_name="Date/heure de la tâche qui a généré la suggestion"
    )
    debug_data = models.JSONField(
        verbose_name=dedent(
            """Données de debug de la suggestion
        (quelles données ont été utilisées pour la suggestion)"""
        ),
        default=None,
    )
    change_type = models.CharField(
        max_length=20,
        choices=(("acteur_cluster", "Cluster d'acteur"),),
        verbose_name="Type de changement",
    )
    change_data = models.JSONField(
        verbose_name=dedent(
            """Données du changement
         (stocker uniquement le strict minimum pour
         gérer le changement)"""
        ),
    )
    change_description = models.TextField(verbose_name="Description")

    # ------------------------------------
    # Champs liés aux revues
    # ------------------------------------
    review_status = models.CharField(
        max_length=20,
        choices=(
            ("pending", "En attente"),
            ("accepted", "Acceptée"),
            ("rejected", "Rejetée"),
        ),
        default="pending",
        verbose_name="Statut de la revue",
    )
    review_at = models.DateTimeField(
        verbose_name="Date/heure de la revue (géré automatiquement à la sauvegarde)",
        editable=False,
    )
    review_comments = models.TextField(
        blank=True, null=True, verbose_name="Commentaires de revue"
    )

    def __str__(self) -> str:
        return f"Suggestion de changement {self.id=} ({self.review_status=})"

    def clean(self):
        """Normalisation/validation des données"""
        super().clean()

        # ------------------------------
        # Remplissages automatiques
        # ------------------------------
        # On remplit review_at si la revue est effectuée ET
        # que c'est la première fois qu'on change le statut (sinon
        # on garde la valeur originale)
        if self.review_status != "pending" and self.review_at is None:
            self.review_at = timezone.now()

        # ------------------------------
        # Validation de change_data
        # ------------------------------
        # Par défaut on s'attend à un dict ou une list
        if not isinstance(self.change_data, (dict, list)):
            raise ValueError("change_data doit être un dict ou list")

        # Validations spécifiques aux différents types de changements
        if self.change_type == "acteur_cluster":
            if not isinstance(self.change_data, dict):
                raise ValueError("acteur_cluster: change_data doit être un dict pour ")
            acteur_id = self.change_data.get("acteur_id")
            cluster_id = self.change_data.get("cluster_id")
            if not acteur_id:
                raise ValueError("acteur_cluster: change_data à besoin de acteur_id")
            if not cluster_id:
                raise ValueError("acteur_cluster: change_data à besoin de cluster_id")

        else:
            raise NotImplementedError(
                f"Pas de gestion change_data pour: {self.change_type}"
            )

    def save(self, *args, **kwargs):
        """Pour appliquer toutes les normalisations/validations"""
        self.full_clean()
        super().save(*args, **kwargs)
