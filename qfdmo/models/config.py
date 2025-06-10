from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe
from wagtail.snippets.models import register_snippet


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


@register_snippet
class CarteConfig(models.Model):
    nom = models.CharField(unique=True)
    hide_legend = models.BooleanField(
        default=False,
        verbose_name="Cacher la légende",
        help_text="Cocher cette case cache la légende affichée en bas à gauche de la "
        "carte en desktop et au dessus de celle-ci en mobile",
    )
    no_branding = models.BooleanField(
        verbose_name="Supprimer le branding",
        default=False,
        help_text="Supprime le logo dans l'entête de la carte ainsi que"
        " le bouton Infos. Ce mode est utilisé essentiellement "
        "pour la carte affichée dans l'assistant",
    )
    slug = models.SlugField(
        unique=True,
        help_text=mark_safe(
            "Le slug est utilisé pour générer l'url de carte, "
            "par exemple: https://quefairedemesobjets.fr/carte/"
            "<strong>cyclevia</strong><br>"
            "Le slug est utilisé pour le script avec l'attribut"
            " <code>data-slug</code>, "
            "par exemple : <br/>"
            "<code>&lt;script "
            "src='https://quefairedemesobjets.ademe.fr/static/carte.js' "
            "data-slug='cyclevia'&gt;&lt;/script&gt;</code>"
        ),
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

    preview_title = models.CharField(
        blank=True,
        verbose_name="Titre de l'écran de prévisualisation",
        help_text="Ce titre s'affiche avant que l'utilisateur n'ait fait une recherche "
        "dans la carte",
    )
    preview_content = models.TextField(
        blank=True,
        verbose_name="Contenu de l'écran de prévisualisation",
        help_text="Ce texte s'affiche avant que l'utilisateur n'ait fait une recherche "
        "dans la carte",
    )

    def get_absolute_url(self):
        return reverse("qfdmo:carte_custom", kwargs={"slug": self.slug})

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Carte sur mesure"
        verbose_name_plural = "Cartes sur mesure"
