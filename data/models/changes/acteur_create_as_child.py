from pydantic import BaseModel


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

        # Create child in Acteur
        data_base = self.data.copy()
        del data_base["parent"]
        del data_base["parent_reason"]
        Acteur.objects.create(
            identifiant_unique=self.id,
            **data_base,
        )

        # In Revision we only store what is different, i.e. parent
        # FIXME: should we use get_or_create_revision?
        # I tried, it was failing, started to look at the code and went
        # down a rabbit hole
        RevisionActeur.objects.create(
            identifiant_unique=self.id,
            parent=parent,
            parent_reason=self.data["parent_reason"],
            statut="ACTIF",
            source=self.data["source"],
            acteur_type=self.data["acteur_type"],
        )
