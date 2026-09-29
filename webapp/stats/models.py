from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel


class KeyResult(ClusterableModel):
    """A key result (OKR) exposed to Metabase through the read-only DB user.

    Managed in the Wagtail admin. Values are a series (one row per period):
    written nightly for PostHog and code sources, typed by hand otherwise.
    The current figure is derived by the `stats_keyresult_current` SQL view.
    """

    class Source(models.TextChoices):
        MANUAL = "manual", "Saisie manuelle"
        POSTHOG = "posthog", "Insight PostHog"
        CODE = "code", "Calculé par le code (stats/key_results.py)"

    class Aggregation(models.TextChoices):
        SUM_YEAR = "sum_year", "Somme des valeurs de l'année en cours"
        LAST = "last", "Dernière valeur"

    code = models.SlugField(
        unique=True, help_text="Identifiant technique, ex : visiteurs_orientes"
    )
    title = models.CharField("Titre", max_length=255)
    description = models.TextField(blank=True)
    target = models.FloatField(
        "Cible", null=True, blank=True, help_text="Objectif à atteindre sur l'année"
    )
    source = models.CharField(
        max_length=10, choices=Source.choices, default=Source.MANUAL
    )
    posthog_insight = models.CharField(
        "Insight PostHog",
        max_length=20,
        blank=True,
        help_text="Seule la première série de l'insight est enregistrée, " "par mois.",
    )
    aggregation = models.CharField(
        "Résultat",
        max_length=10,
        choices=Aggregation.choices,
        default=Aggregation.LAST,
        help_text="Comment le résultat courant est calculé à partir des valeurs.",
    )

    class Meta:
        verbose_name = "Key result"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.title


class KeyResultValue(models.Model):
    key_result = ParentalKey(KeyResult, on_delete=models.CASCADE, related_name="values")
    date = models.DateField(help_text="Premier jour de la période (mois, année)")
    value = models.FloatField("Valeur")

    class Meta:
        verbose_name = "Valeur"
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(
                fields=["key_result", "date"], name="unique_key_result_date"
            )
        ]

    def __str__(self) -> str:
        return f"{self.date}: {self.value}"
