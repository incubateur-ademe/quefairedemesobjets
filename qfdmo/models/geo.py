from django.db import models


class EPCI(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=10, unique=True)
    nom = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nom} ({self.code})"
