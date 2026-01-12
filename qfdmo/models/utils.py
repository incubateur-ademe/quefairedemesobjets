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


def string_remove_substring_via_normalization(
    s1: str | None, s2: str | None
) -> str | None:
    """Supprime la sous-chaîne s2 de s1:
    - en passant par les états normalisés pour la soustraction
       pour la rendre plus robuste
    - mais en retournant le résultat sur la base des mots d'origines
       pour préserver l'info d'origine"""
    # On scinde les champs en mots normalisés, on récupère les index
    # des mots à conserver, et on reconstruit une chaîne à partir
    # des mots d'origine
    s1 = (s1 or "").strip()
    s2 = (s2 or "").strip()
    s1_norm = normalize_string_basic(s1)
    s2_norm = normalize_string_basic(s2)
    if s2_norm not in s1_norm:
        return s1 or None
    words_s1 = s1.split()
    words_s1_norm = s1_norm.split()
    words_s2_norm = s2_norm.split()
    words_idx_kept = [i for i, w in enumerate(words_s1_norm) if w not in words_s2_norm]
    try:
        return " ".join([words_s1[i] for i in words_idx_kept]) or None
    except Exception:
        # Si à cause de la norma on peut pas retomber sur nos pieds, on
        # retourne le nom original
        return s1 or None


def compute_identifiant_unique(source_code: str, identifiant_externe: str) -> str:
    if not identifiant_externe:
        raise ValueError(
            "Identifiant externe is required to generate identifiant_unique"
        )
    if not source_code:
        raise ValueError("Source code is required to generate identifiant_unique")
    source_stub = unidecode(source_code.lower().strip()).replace(" ", "_")
    identifiant_externe_stub = (
        str(identifiant_externe).strip().replace("/", "-").replace(" ", "")
    )
    return source_stub + "_" + identifiant_externe_stub
