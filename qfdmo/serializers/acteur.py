from rest_framework import serializers

from qfdmo.models.acteur import Acteur


class ActeurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Acteur
        fields = "__all__"
