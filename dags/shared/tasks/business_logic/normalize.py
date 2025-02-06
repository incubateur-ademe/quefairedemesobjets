"""Utilitaires de normalisation de chaînes de caractères.

Nous sommes dans d'une normalisation partagée (shared)
et donc générique, qui rentre dans le contexte de travaille
avec des chaînes pour des tâches de data engineering type
clustering, d'où le fait que les valeurs vides retournées soient ""

Si vous voulez de la normalisation plus stricte qui retourne None
en cas de non-conformité, alors écrire des fonctions spécifiques
aux champs en question, et idéallement intégrer ce travail
aux modèles django.
"""

import re

from unidecode import unidecode


def string_basic(s: str) -> str:
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


def string_remove_small_words(s: str, size: int) -> str:
    """Normalisation d'une chaîne de caractères en supprimant les mots
    de taille inférieure ou égale à size
    """
    if s is None or not str(s).strip():
        return ""
    return " ".join([w for w in str(s).strip().split() if len(w) > size])


def string_order_unique_words(s: str) -> str:
    """Normalisation d'une chaîne de caractères en ordonnant les mots
    par ordre alphabétique et supprimant les doublons
    pour une fois de plus augmenter les chances de correspondance
    """
    if s is None or not str(s).strip():
        return ""
    return " ".join(sorted(set(str(s).strip().split())))
