from django.contrib.gis.db import models


class CodeAsNaturalKeyManager(models.Manager):
    def get_by_natural_key(self, code: str) -> models.Model:
        return self.get(code=code)


class CodeAsNaturalKeyModel(models.Model):
    class Meta:
        app_label = "qfdmo"
        abstract = True

    objects = CodeAsNaturalKeyManager()

    def natural_key(self) -> tuple[str]:
        return (getattr(self, "code"),)

    def __str__(self) -> str:
        return getattr(self, "code")


class NomAsNaturalKeyManager(models.Manager):
    def get_by_natural_key(self, nom: str) -> models.Model:
        return self.get(nom=nom)


class NomAsNaturalKeyModel(models.Model):
    class Meta:
        app_label = "qfdmo"
        abstract = True

    objects = NomAsNaturalKeyManager()

    nom = models.CharField()

    def natural_key(self) -> tuple[str]:
        return (self.nom,)

    def __str__(self) -> str:
        return self.nom
