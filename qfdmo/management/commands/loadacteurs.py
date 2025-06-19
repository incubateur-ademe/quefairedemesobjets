from django.core.management.commands.loaddata import Command as LoadDataCommand
from django.core.serializers.base import DeserializedObject

from qfdmo.models import DisplayedActeur


class Command(LoadDataCommand):
    # TODO: document and explain comment this command
    def save_obj(self, obj: DeserializedObject) -> bool:
        if isinstance(obj.object, DisplayedActeur):
            obj.object.generate_source_if_missing()
            obj.object.generate_identifiant_unique_if_missing()

        return super().save_obj(obj)
