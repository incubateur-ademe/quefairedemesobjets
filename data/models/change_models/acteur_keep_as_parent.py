from data.models.change_models import ChangeActeurNothingRevision


class ChangeActeurKeepAsParent(ChangeActeurNothingRevision):
    # Parents are revisions, so we can just inherit the do-nothing
    # model and just change the name
    @classmethod
    def name(cls) -> str:
        return "acteur_keep_as_parent"
