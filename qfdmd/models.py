from django.contrib.gis.db import models

from qfdmo.models.categorie_objet import SousCategorieObjet


class Produit(models.Model):
    id = models.IntegerField(primary_key=True)
    sous_categorie = models.ForeignKey(SousCategorieObjet, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Produit"
