from django.core.management.commands.loaddata import Command as LoadDataCommand
from django.core.serializers.base import DeserializedObject

from qfdmd.models import Produit
from qfdmo.models import DisplayedActeur
from qfdmo.models.acteur import DisplayedPropositionService


class Command(LoadDataCommand):
    """
    Custom implementation of the `loaddata` management command.

    This subclass extends Django's built-in `loaddata` command to provide
    additional processing for specific model instances during deserialization.

    It ensures that unique identifiers or source fields are generated for
    certain objects if they are missing when the fixture is loaded.
    """

    def save_obj(self, obj: DeserializedObject) -> bool:
        if isinstance(obj.object, DisplayedActeur):
            obj.object.generate_source_if_missing()
            obj.object.generate_identifiant_unique_if_missing()

        if isinstance(obj.object, DisplayedPropositionService):
            obj.object.generate_id_if_missing()

        if isinstance(obj.object, Produit):
            if not obj.object.id:
                obj.object.id = (
                    getattr(Produit.objects.all().order_by("-id").first(), "id", 0) + 1
                )

        return super().save_obj(obj)
