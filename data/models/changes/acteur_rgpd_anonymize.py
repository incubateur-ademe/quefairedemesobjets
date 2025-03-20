"""Special change model dedicated to RGPD because:

- NORMALLY we version data through RevisionActeur
   + consequence: we create a Revision if it doesn't exist

- HOWEVER WITH RGPD we don't do data versioning, we overwrite
   the data so it disappears from our DB
    = consequence: we don't create a Revision if it doesn't exist
      (again we are not versioning, just overwriting)

Since the approach to RGPD should be consistent, we don't
expect the model to take any other input than the ID of the acteur
we are changing, and the model takes care of the rest
"""

from datetime import datetime, timezone

from data.models.changes.acteur_abstract import ChangeActeurAbstract
from qfdmo.models import Acteur, ActeurStatus, RevisionActeur

VALUE_ANONYMIZED = "ANONYMISE POUR RAISON RGPD"
ACTEUR_FIELDS_TO_ANONYMIZE = {
    "nom": VALUE_ANONYMIZED,
    "nom_officiel": VALUE_ANONYMIZED,
    "nom_commercial": VALUE_ANONYMIZED,
    "email": None,  # due to email constraint
    "telephone": VALUE_ANONYMIZED,
    "adresse": VALUE_ANONYMIZED,
    "adresse_complement": VALUE_ANONYMIZED,
    "statut": ActeurStatus.INACTIF,
}


class ChangeActeurRgpdAnonymize(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_rgpd_anonymize"

    def validate(self) -> list[Acteur | RevisionActeur]:
        if self.data:
            raise ValueError("Pour RGPD ne pas fournir de data, le modèle efface")
        # The parent should already exist in revision or base
        # and we return all its instances to overwrite them all
        instances = []
        rev = RevisionActeur.objects.filter(pk=self.id).first()
        if rev:
            instances.append(rev)
        instances.append(Acteur.objects.get(pk=self.id))
        return instances

    def apply(self):
        # For each instance found
        instances = self.validate()
        for instance in instances:
            # We anonymize the fields
            for key, value in ACTEUR_FIELDS_TO_ANONYMIZE.items():
                setattr(instance, key, value)

            # Special case for comments
            now = datetime.now(timezone.utc).strftime("le %Y-%m-%d à %H:%M:%S UTC")
            instance.commentaires_ajouter(f"{VALUE_ANONYMIZED} {now}")
            instance.save()
