import re

from django.contrib.gis.db import models
from unidecode import unidecode


class CodeAsNaturalKeyManager(models.Manager):
    def get_by_natural_key(self, code: str) -> models.Model:
        return self.get(code=code)


class CodeAsNaturalKeyModel(models.Model):
    class Meta:
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
        abstract = True

    objects = NomAsNaturalKeyManager()

    nom = models.CharField()

    def natural_key(self) -> tuple[str]:
        return (self.nom,)

    def __str__(self) -> str:
        return self.nom


# TODO: centraliser nos utilitaires éparpillés dans:
# qfdmo/models/utils.py
# dags/shared/tasks/business_logic/normalize.py
# dags/utils
def normalize_string_basic(s: str) -> str:
    """Normalisation basique d'une chaîne de caractères, à savoir:
    - mise en minuscules
    - suppression des espaces superflus
    - conversion des accents
    - suppression des caractères spéciaux

    L'objectif: favoriser la convergent vers une forme unique en
    ne perdant rien d'essentiel et sans pour autant
    engendrer des collisions (sachant qu'en général on travaille
    champ par champ et très souvent par code postal/ville ce qui
    réduit encore davantage les risques de collision).
    """
    if s is None or not str(s).strip():
        return ""
    s = unidecode(str(s).strip().lower())
    s = re.sub(r"[^a-z0-9]", " ", s)
    return re.sub(r"\s+", " ", s).strip()
