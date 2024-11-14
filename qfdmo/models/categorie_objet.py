from urllib.parse import urlencode

from django.conf import settings
from django.contrib.gis.db import models
from django.db.utils import cached_property

from qfdmo.models.utils import CodeAsNaturalKeyModel


class CategorieObjet(CodeAsNaturalKeyModel):
    class Meta:
        verbose_name = "Catégorie d'objets"
        verbose_name_plural = "Catégories d'objets"

    id = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=255, blank=False, null=False)
    code = models.CharField(max_length=255, unique=True, blank=False, null=False)


class SousCategorieObjet(CodeAsNaturalKeyModel):
    class Meta:
        verbose_name = "Sous catégorie d'objets"
        verbose_name_plural = "Sous catégories d'objets"
        ordering = ["libelle"]

    id = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=255, blank=False, null=False)
    categorie = models.ForeignKey(CategorieObjet, on_delete=models.CASCADE)
    code = models.CharField(max_length=255, unique=True, blank=False, null=False)
    afficher = models.BooleanField(default=True)
    qfdmd_produits = models.ManyToManyField(
        "qfdmd.produit",
        related_name="sous_categories",
        verbose_name="Produits Que Faire De Mes Déchets & Objets",
        blank=True,
    )
    afficher_carte = models.BooleanField(
        default=False,
        verbose_name="Afficher la carte dans l’assistant",
        help_text="afficher la carte LVAO dans les fiches produits "
        "“Que faire de mes objets et déchets” avec les identifiants "
        "indiqués au niveau de la sous-catégorie",
    )

    def __str__(self) -> str:
        return self.libelle

    @cached_property
    def carte_settings(self):
        return {
            "carte": 1,
            "direction": "jai",
            "first_dir": "jai",
            "sous_categorie_objet": self.libelle,
            "sc_id": self.id,
            "limit": 25,
        }

    @property
    def url_carte(self):
        if self.afficher_carte:
            params = urlencode(self.carte_settings)

            return f"{settings.BASE_URL}/?{params}"

    def natural_key(self) -> tuple[str]:
        return (self.code,)


class Objet(CodeAsNaturalKeyModel):
    id = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=255, blank=False, null=False)
    code = models.CharField(max_length=255, unique=True, blank=False, null=False)
    sous_categorie = models.ForeignKey(
        SousCategorieObjet,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="objets",
    )
    identifiant_qfdmod = models.IntegerField(
        blank=True, null=True, verbose_name="Identifiant QFDMD"
    )
