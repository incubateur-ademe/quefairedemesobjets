from django.db import models


class GroupeActionConfig(models.Model):
    carte_config = models.ForeignKey(
        "qfdmo.CarteConfig",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    groupe_action = models.OneToOneField(
        "qfdmo.GroupeAction",
        on_delete=models.CASCADE,
        verbose_name="Groupe d'actions",
    )

    icon = models.FileField(
        upload_to="config/groupeaction/icones/",
        verbose_name="Supplanter l'icône utilisée pour l'action",
        blank=True,
        null=True,
    )
    acteur_type = models.ManyToManyField(
        "qfdmo.ActeurType",
        verbose_name="Types d'acteur concernés par la configuration",
        help_text="Si la configuration de l'action est spécifique à un ou plusieurs"
        " types d'acteurs, ceux-ci peuvent être renseignés ici",
        blank=True,
    )


class CarteConfig(models.Model):
    nom = models.CharField(unique=True)
    slug = models.SlugField(unique=True)
    sous_categorie_objet = models.ManyToManyField(
        "qfdmo.SousCategorieObjet",
        verbose_name="Sous-catégories d'objets filtrés",
        help_text="Seules les sous-catégories sélectionnées s'afficheront sur la carte \n"
        "Si le champ n'est pas renseigné il sera ignoré",
        blank=True,
    )
    source = models.ManyToManyField(
        "qfdmo.Source",
        verbose_name="Source(s)",
        help_text="Seules les sources sélectionnées s'afficheront sur la carte \n"
        "Si le champ n'est pas renseigné il sera ignoré",
        blank=True,
    )

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Carte sur mesure"
        verbose_name_plural = "Cartes sur mesure"
