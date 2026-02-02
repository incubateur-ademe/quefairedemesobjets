from django.contrib.gis.db import models as gis_models
from django.core.validators import FileExtensionValidator
from django.db import models
from django.http import QueryDict
from django.urls import reverse
from django.utils.safestring import mark_safe
from wagtail.search import index
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
        constraints = [
            models.UniqueConstraint(
                fields=["carte_config", "groupe_action", "acteur_type"],
                name="unique_carte_config_groupe_action_acteur_type",
            )
        ]


@register_snippet
class CarteConfig(index.Indexed, models.Model):
    SOUS_CATEGORIE_QUERY_PARAM = "sc_id"

    nom = models.CharField(unique=True)
    SOLUTION_TEMPORAIRE_A_SUPPRIMER_DES_QUE_POSSIBLE_parametres_url = models.CharField(
        "paramètres d'URL pour la direction / groupes d'action", blank=True
    )

    # UI
    class ModesAffichage(models.TextChoices):
        CARTE = "carte", "Carte"
        LISTE = "liste", "Liste"

    mode_affichage = models.CharField(
        default=ModesAffichage.CARTE,
        choices=ModesAffichage,
        verbose_name="Mode d'affichage par défaut",
        help_text="Ce choix permet de définir le mode d'affichage par défaut de"
        " la carte. Le mode liste affiche une liste d'acteurs tandis qu'une"
        " carte affiche un fond de carte.",
    )
    nombre_d_acteurs_affiches = models.IntegerField(null=True, blank=True)

    # TODOWAGTAIL : remove double negation and use afficher_legende instead
    cacher_legende = models.BooleanField(
        default=False,
        verbose_name="Cacher la légende",
        help_text="Cocher cette case cache la légende affichée en bas à gauche de la "
        "carte en desktop et au dessus de celle-ci en mobile",
    )
    supprimer_branding = models.BooleanField(
        verbose_name="Supprimer le branding",
        default=False,
        help_text="Supprime le logo dans l'entête de la carte ainsi que"
        " le bouton Infos. Ce mode est utilisé essentiellement "
        "pour la carte affichée dans l'assistant",
    )
    cacher_filtre_objet = models.BooleanField(
        default=False,
        verbose_name="Cacher le filtre objet",
        help_text="Cocher cette case cache le filtre permettant de sélectionner "
        "les objets dans la carte",
    )
    titre_previsualisation = models.CharField(
        blank=True,
        verbose_name="Titre de l'écran de prévisualisation",
        help_text="Ce titre s'affiche avant que l'utilisateur n'ait fait une recherche "
        "dans la carte",
    )
    contenu_previsualisation = models.TextField(
        blank=True,
        verbose_name="Contenu de l'écran de prévisualisation",
        help_text="Ce texte s'affiche avant que l'utilisateur n'ait fait une recherche "
        "dans la carte",
    )

    # Config
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
    action = models.ManyToManyField(
        "qfdmo.Action",
        verbose_name="Actions",
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
    direction = models.ManyToManyField(
        "qfdmo.ActionDirection",
        verbose_name="Direction des actions",
        help_text="Seules les actions correspondantes à la direction choisie "
        "s'afficheront sur la carte"
        "\nSi le champ n'est pas renseigné il sera ignoré",
        blank=True,
    )

    label_qualite = models.ManyToManyField(
        "qfdmo.LabelQualite",
        verbose_name="Label(s) qualité",
        help_text="Ce champ agit comme un filtre des résultats affichés.<br/>"
        " Si les labels sélectionnés correspondent aux labels affichés dans "
        "la modale de filtres de la carte, alors ceux-ci seront cochés par défaut.<br/>"
        "\nSi le champ n'est pas renseigné il sera ignoré",
        blank=True,
    )
    acteur_type = models.ManyToManyField(
        "qfdmo.ActeurType",
        verbose_name="Type(s) d'acteurs",
        help_text="Seuls les types d'acteurs sélectionnés s'afficheront sur la carte"
        "\nSi le champ n'est pas renseigné il sera ignoré",
        blank=True,
    )

    epci = models.ManyToManyField("qfdmo.EPCI", verbose_name="EPCI", blank=True)

    bonus_reparation = models.BooleanField(
        verbose_name="Bonus réparation uniquement",
        default=False,
        help_text="Cocher cette case pour afficher uniquement les acteurs proposant "
        "le bonus réparation",
    )

    bounding_box = gis_models.PolygonField(
        verbose_name="Zone géographique (bounding box)",
        help_text="Définir une zone géographique pour limiter l'affichage de la carte "
        "à une région spécifique",
        blank=True,
        null=True,
        srid=4326,
    )

    test = models.BooleanField(
        default=False,
        verbose_name="Carte de test",
        help_text="Cocher cette case pour marquer cette carte comme une carte de test "
        "(utilisée pour les tests end-to-end).",
    )

    def get_absolute_url(self, override_sous_categories=None, initial_query_string=""):
        """This view can be used with categories set from the parent page.
        For example in the Assistant, with a Produit page, the sous_categorie_objet
        is set on the page itself and need to replace the ones set on the carte config.
        The carte config used on a Produit Page usually does not have
        sous_categorie_objet field filled,
        but in case this happens, we assume they need to be bypassed
        """
        query = QueryDict(initial_query_string, mutable=True)
        if override_sous_categories:
            query.setlist(self.SOUS_CATEGORIE_QUERY_PARAM, override_sous_categories)

        return reverse("qfdmo:carte_custom", kwargs={"slug": self.slug}, query=query)

    def __str__(self):
        return f"Carte - {self.nom}"

    class Meta:
        verbose_name = "Carte sur mesure"
        verbose_name_plural = "Cartes sur mesure"
        ordering = ("nom",)

    # Wagtail-specific
    search_fields = [
        index.SearchField("nom"),
        index.AutocompleteField("nom"),
    ]
