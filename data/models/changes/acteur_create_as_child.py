from pydantic import BaseModel
from rich import print

from data.models.changes.utils import data_reconstruct

from data.models.changes.utils import data_reconstruct


class ChangeActeurCreateAsChild(BaseModel):
    id: str
    data: dict = {}

    @classmethod
    def name(cls) -> str:
        return "acteur_create_as_child"

    def validate(self):
        from qfdmo.models import Acteur, DisplayedActeur, RevisionActeur

        # Parent field must be SET (but we can't check if parent exists yet
        # as it could be a new parent to be created)
        for field in ["parent", "parent_reason"]:
            if not self.data.get(field):
                msg = f"Création d'enfant: champ '{field}' à renseigner {self.data}"
                raise ValueError(msg)

        # Ensure child exists nowhere
        for model in [Acteur, RevisionActeur, DisplayedActeur]:
            obj = model.objects.filter(pk=self.id)
            if obj.exists():
                msg = (
                    f"Création d'enfant: '{self.id}' existe déjà dans {model.__name__}"
                )
                raise ValueError(msg)

    def apply(self):
        self.validate()
        from qfdmo.models import Acteur, RevisionActeur

        # Ensure parent exists in RevisionActeur
        parent = RevisionActeur.objects.get(pk=self.data["parent"])

        # Reconstruct data from RevisionActeur
        data = data_reconstruct(RevisionActeur, self.data)

        # Create child in Acteur to hold data
        data_base = data.copy()
        del data_base["parent"]
        del data_base["parent_reason"]
        # TODO: if we flatten our pydantic models, then we wouldn't
        if "identifiant_unique" in data_base:
            del data_base["identifiant_unique"]
        Acteur.objects.create(
            identifiant_unique=self.id,
            **data_base,
        )

        # Create child in RevisionActeur to hold reference to parent
        RevisionActeur.objects.create(
            identifiant_unique=self.id,
            parent_reason=data["parent_reason"],
            parent=parent,
            statut="ACTIF",
            source=data["source"],
            acteur_type=data["acteur_type"],
        )
