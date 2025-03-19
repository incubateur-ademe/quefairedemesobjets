"""Config to handle RGPD anonymization"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RGPD:
    ACTEUR_FIELD_ANONYMIZED = "ANONYMISE POUR RAISON RGPD"
    ACTEUR_FIELDS_TO_ANONYMIZE = [
        "nom",
        "nom_officiel",
        "nom_commercial",
        "description",
        "email",
        "telephone",
        "adresse",
        "adresse_complement",
    ]
    ACTEUR_STATUS = "INACTIF"
