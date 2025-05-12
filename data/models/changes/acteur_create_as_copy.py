import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ChangeActeurCreateAsCopy(BaseModel):
    id: str  # id of the acteur to copy
    data: dict = {}  # data to set on the new acteur

    def _get_acteur_to_copy(self):
        from qfdmo.models import Acteur, RevisionActeur

        return RevisionActeur.objects.filter(pk=self.id).first() or Acteur.objects.get(
            pk=self.id
        )

    @classmethod
    def name(cls) -> str:
        return "acteur_create_as_copy"

    def validate(self):
        from qfdmo.models import Acteur

        # Ensure source exists
        try:
            acteur = self._get_acteur_to_copy()
        except Acteur.DoesNotExist:
            msg = f"Copy d'acteur: l'acteur source '{self.id}' n'existe pas dans Acteur"
            raise ValueError(msg)

        # Ensure identifiant_unique is overridden
        if "identifiant_unique" not in self.data:
            msg = "Copy d'acteur: l'acteur cible doit surdefinir son identifiant_unique"
            raise ValueError(msg)

        # Ensure identifiant_unique is not the same as the source
        if self.data["identifiant_unique"] == acteur.identifiant_unique:
            msg = (
                "Copy d'acteur: l'acteur cible doit avoir un identifiant_unique"
                " différent de l'acteur source"
            )
            raise ValueError(msg)

    def copy_acteur(
        self,
        overriden_fields={
            "identifiant_unique": None,
            "identifiant_externe": None,
            "source": None,
        },
    ):
        from qfdmo.models import Acteur

        acteur_to_copy = Acteur.objects.get(pk=self.id)
        revision_acteur_to_copy = acteur_to_copy.get_or_create_revision()

        revision_acteur_to_copy.instance_copy(
            revision_acteur_to_copy, overriden_fields=overriden_fields
        )

    def apply(self):
        self.validate()
        from qfdmo.models import Acteur, ActeurStatus

        acteur_to_copy = Acteur.objects.get(pk=self.id)
        revision_acteur_to_copy = acteur_to_copy.get_or_create_revision()

        # Ensure Acteur is not active
        if acteur_to_copy.statut == ActeurStatus.ACTIF:
            msg = f"Copy d'acteur: l'acteur source '{self.id}' ne doit pas être actif"
            raise ValueError(msg)

        revision_acteur_to_copy.instance_copy(overriden_fields=self.data)
