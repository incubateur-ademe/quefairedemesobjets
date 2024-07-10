from django.conf import settings
from urllib.parse import quote_plus
from django.contrib.gis.db import models
from django.db.utils import cached_property
from django.forms import model_to_dict

from qfdmo.models.utils import CodeAsNaturalKeyModel


class CategorieObjet(CodeAsNaturalKeyModel):
    class Meta:
        verbose_name = "Catégorie d'objets"
        verbose_name_plural = "Catégories d'objets"

    id = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=255, blank=False, null=False)
    code = models.CharField(max_length=255, unique=True, blank=False, null=False)

    def serialize(self):
        return model_to_dict(self)


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
    def url_carte(self):
        if self.afficher_carte:
            return (
                f"{settings.BASE_URL}/?carte&sous_categorie_objet="
                f"{quote_plus(self.libelle)}&sc_id={self.id}&limit=25"
            )

    def natural_key(self) -> tuple[str]:
        return (self.code,)

    def serialize(self):
        sous_categorie = model_to_dict(self, exclude=["categorie"])
        sous_categorie["categorie"] = self.categorie.serialize()
        return sous_categorie


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
