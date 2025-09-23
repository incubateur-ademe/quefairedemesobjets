from django.contrib.gis.db import models

from qfdmo.models.utils import CodeAsNaturalKeyModel
from qfdmo.validators import CodeValidator


class CategorieObjet(CodeAsNaturalKeyModel):
    class Meta:
        verbose_name = "Objet - Catégorie"

    id = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=255, blank=False, null=False)
    code = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=False,
        help_text=(
            "Ce champ est utilisé lors de l'import de données, il ne doit pas être"
            " mis à jour sous peine de casser l'import de données"
        ),
        validators=[CodeValidator()],
    )


class SousCategorieObjet(CodeAsNaturalKeyModel):
    class Meta:
        verbose_name = "Objet - Sous catégorie"
        ordering = ["libelle"]

    id = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=255, blank=False, null=False)
    categorie = models.ForeignKey(CategorieObjet, on_delete=models.CASCADE)
    code = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=False,
        help_text=(
            "Ce champ est utilisé lors de l'import de données, il ne doit pas être"
            " mis à jour sous peine de casser l'import de données"
        ),
        validators=[CodeValidator()],
    )
    qfdmd_produits = models.ManyToManyField(
        "qfdmd.produit",
        related_name="sous_categories",
        verbose_name="Produits Que Faire De Mes Déchets & Objets",
        blank=True,
    )
    reemploi_possible = models.BooleanField(
        default=True,
        verbose_name="Reemploi possible",
        help_text="Indique si la sous-catégorie est compatible avec le reemploi",
    )

    def __str__(self) -> str:
        return self.libelle

    def natural_key(self) -> tuple[str]:
        return (self.code,)


class Objet(CodeAsNaturalKeyModel):
    class Meta:
        verbose_name = "Objet - Objet"

    id = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=255, blank=False, null=False)
    code = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=False,
        help_text=(
            "Ce champ est utilisé lors de l'import de données, il ne doit pas être"
            " mis à jour sous peine de casser l'import de données"
        ),
        validators=[CodeValidator()],
    )
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
