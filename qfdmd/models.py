from django.contrib.gis.db import models


class Produit(models.Model):
    titre = models.CharField(unique=True, blank=True)
    id = models.IntegerField(primary_key=True)

    def __str__(self):
        return "%s %s" % (self.id, self.titre)

    class Meta:
        verbose_name = "Produit"
