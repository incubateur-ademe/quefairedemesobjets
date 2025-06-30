from django.core.management.commands.loaddata import Command as LoadDataCommand
from django.core.serializers.base import DeserializedObject

from qfdmo.models import DisplayedActeur
from qfdmo.models.acteur import DisplayedPropositionService


class Command(LoadDataCommand):
    # TODO: document this command
    def save_obj(self, obj: DeserializedObject) -> bool:
        if isinstance(obj.object, DisplayedActeur):
            obj.object.generate_source_if_missing()
            obj.object.generate_identifiant_unique_if_missing()

        if isinstance(obj.object, DisplayedPropositionService):
            obj.object.generate_id_if_missing()

        return super().save_obj(obj)
