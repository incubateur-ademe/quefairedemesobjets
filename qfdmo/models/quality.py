from django.db import models


class AdresseVerification(models.Model):
    source = models.CharField(max_length=255, default="equipe")
    cree_le = models.DateTimeField(auto_now_add=True)
    mis_a_jour_le = models.DateTimeField(auto_now=True)
    adresse = models.CharField(max_length=255, null=True, blank=True)
    adresse_complement = models.CharField(max_length=255, null=True, blank=True)
    code_postal = models.CharField(max_length=255, null=True, blank=True)
    ville = models.CharField(max_length=255, null=True, blank=True)
    result = models.JSONField(null=True, blank=True)
    adresse_valide = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    geoloc_valide = models.BooleanField(default=False)
    acteur = models.ForeignKey(
        "Acteur",
        on_delete=models.CASCADE,
        related_name="adresse_verifications",
        to_field="identifiant_unique",
    )
