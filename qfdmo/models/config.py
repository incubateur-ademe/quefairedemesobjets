from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse


class GroupeActionConfig(models.Model):
    carte_config = models.ForeignKey(
        "qfdmo.CarteConfig",
        on_delete=models.CASCADE,
        related_name="groupe_action_configs",
        null=True,
        blank=True,
    )
    groupe_action = models.ForeignKey(
        "qfdmo.GroupeAction",
        on_delete=models.CASCADE,
        verbose_name="Groupe d'action",
        help_text="La configuration peut être limitée à un groupe d'action "
        "spécifique. Auquel cas il doit être indiqué ici.\n"
        "Si aucune action n'est renseignée, cette configuration "
        "s'appliquera à tout type d'acteur.",
        null=True,
        blank=True,
    )

    acteur_type = models.ForeignKey(
        "qfdmo.ActeurType",
        on_delete=models.CASCADE,
        verbose_name="Types d'acteur concernés par la configuration",
        help_text="La configuration peut être limitée à un type d'acteur "
        "spécifique. Auquel cas il doit être indiqué ici.\n"
        "Si aucun type d'acteur n'est renseigné, cette configuration "
        "s'appliquera à tout type d'acteur.",
        null=True,
        blank=True,
    )

    icon = models.FileField(
        upload_to="config/groupeaction/icones/",
        verbose_name="Supplanter l'icône utilisée pour l'action",
        help_text="L'icône doit être au format SVG. ",
        validators=[FileExtensionValidator(allowed_extensions=["svg"])],
        blank=True,
        null=True,
    )

    class Meta:
        unique_together = ["carte_config", "groupe_action", "acteur_type"]


class CarteConfig(models.Model):
    nom = models.CharField(unique=True)
    slug = models.SlugField(
        unique=True,
        help_text="Le slug est utilisé pour générer l'url de carte, "
        "par exemple: https://quefairedemesobjets.fr/carte/<strong>cyclevia</strong>",
    )
    sous_categorie_objet = models.ManyToManyField(
        "qfdmo.SousCategorieObjet",
        verbose_name="Sous-catégories d'objets filtrés",
        help_text="Seules les objets sélectionnés s'afficheront sur la carte"
        "\nSi le champ n'est pas renseigné il sera ignoré",
        blank=True,
    )
    groupe_action = models.ManyToManyField(
        "qfdmo.GroupeAction",
        verbose_name="Groupe d'actions",
        help_text="Seules les actions sélectionnées s'afficheront sur la carte"
        "\nSi le champ n'est pas renseigné il sera ignoré",
        blank=True,
    )
    source = models.ManyToManyField(
        "qfdmo.Source",
        verbose_name="Source(s)",
        help_text="Seules les sources sélectionnées s'afficheront sur la carte"
        "\nSi le champ n'est pas renseigné il sera ignoré",
        blank=True,
    )

    def get_absolute_url(self):
        return reverse("qfdmo:carte_custom", kwargs={"slug": self.slug})

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Carte sur mesure"
        verbose_name_plural = "Cartes sur mesure"
