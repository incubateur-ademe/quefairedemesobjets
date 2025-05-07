## FIXME : voir si cette classe doit être dépréciée

from pydantic import BaseModel

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
        from qfdmo.models import RevisionActeur

        # Ensure parent exists in RevisionActeur
        if self.data["parent"]:
            RevisionActeur.objects.get(pk=self.data["parent"])

        # Reconstruct data from RevisionActeur
        data = data_reconstruct(RevisionActeur, self.data)

        # Create child in RevisionActeur to hold reference to parent
        print(f"Creating child in RevisionActeur: {data}")
        RevisionActeur.objects.create(**data)
