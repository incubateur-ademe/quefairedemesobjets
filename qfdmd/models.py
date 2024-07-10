from django.contrib.gis.db import models


class Produit(models.Model):
    libelle = models.CharField(
        unique=True,
        blank=True,
        help_text="Ce champ est facultatif et n'est utilisé que "
        "dans l'administration Django.",
        verbose_name="Libellé",
    )
    id = models.IntegerField(
        primary_key=True,
        help_text="Correspond à l'identifiant ID défini dans les données "
        "<i>Que Faire</i>.",
    )

    def __str__(self):
        return "%s %s" % (self.id, self.libelle)

    class Meta:
        verbose_name = "Produit"
