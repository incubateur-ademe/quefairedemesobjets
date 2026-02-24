"""change model to verify an acteur's presence in revision"""

from data.models.changes.acteur_abstract import ChangeActeurAbstract
from qfdmo.models import RevisionActeur


class ChangeActeurVerifyRevision(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_verify_presence_in_revision"

    def validate(self):
        """Since we're not making any changes we are not expecting any data,
        but we still verify that the acteur exists"""
        if self.data:
            raise ValueError("No data expected")
        RevisionActeur.objects.get(pk=self.id)

    def apply(self):
        self.validate()
