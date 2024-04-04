from django.contrib.gis.db import models
from django.forms import model_to_dict
from unidecode import unidecode

from qfdmo.models.utils import CodeAsNaturalKeyManager, NomAsNaturalKeyModel


class CategorieObjet(NomAsNaturalKeyModel):
    class Meta:
        verbose_name = "Catégorie d'objets"
        verbose_name_plural = "Catégories d'objets"

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)

    def serialize(self):
        return model_to_dict(self)


class SousCategorieObjet(models.Model):
    class Meta:
        verbose_name = "Sous catégorie d'objets"
        verbose_name_plural = "Sous catégories d'objets"
        ordering = ["nom"]

    objects = CodeAsNaturalKeyManager()

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)
    categorie = models.ForeignKey(CategorieObjet, on_delete=models.CASCADE)
    code = models.CharField(max_length=10, unique=True, blank=False, null=False)

    def __str__(self) -> str:
        return self.nom

    def natural_key(self) -> tuple[str]:
        return (self.code,)

    @property
    def sanitized_nom(self) -> str:
        return unidecode(self.nom).upper()

    def serialize(self):
        sous_categorie = model_to_dict(self, exclude=["categorie"])
        sous_categorie["categorie"] = self.categorie.serialize()
        return sous_categorie


class Objet(NomAsNaturalKeyModel):
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, blank=False, null=False)
    sous_categorie = models.ForeignKey(
        SousCategorieObjet,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="objets",
    )
