"""change model to make no change to an acteur

Reason for having such a model is that we can
follow the same pattern to be consistent across the board.

For instance in the clustering pipeline, we might decide
that some acteurs do not need to be changed as they already point
to the chosen parent, yes we want to reflect all decisions made
in the cluster summary, this model allows us to do just that
without havint to create messy conditional code in pipelines

"""

from data.models.changes.acteur_abstract import ChangeActeurAbstract
from qfdmo.models import Acteur


class ChangeActeurNothingBase(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_change_nothing_in_base"

    def validate(self):
        """Since we're not making any changes we are not expecting any data,
        but we still verify that the acteur exists"""
        if self.data:
            raise ValueError("No data expected")
        Acteur.objects.get(pk=self.id)

    def apply(self):
        self.validate()
