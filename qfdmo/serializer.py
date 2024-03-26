from rest_framework import serializers

from qfdmo.models import (
    ActeurType,
    DisplayedActeur,
    PropositionService,
    SousCategorieObjet,
)


class SousCategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = SousCategorieObjet
        fields = ["nom"]


class PropositionServiceSerializer(serializers.ModelSerializer):
    action = serializers.StringRelatedField()
    acteur_service = serializers.StringRelatedField()
    sous_categories = serializers.StringRelatedField(many=True)

    class Meta:
        model = PropositionService
        fields = ["action", "acteur_service", "sous_categories"]


class ActeurTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActeurType
        fields = ["nom"]


class DisplayedActeurSerializer(serializers.ModelSerializer):
    acteur_type = serializers.StringRelatedField()
    proposition_services = PropositionServiceSerializer(many=True)
    # latitude = serializers.FloatField(source="latitude", read_only=True)
    # longitude = serializers.FloatField(source="longitude", read_only=True)

    class Meta:
        model = DisplayedActeur
        fields = [
            "identifiant_unique",
            "acteur_type",
            "proposition_services",
            "nom",
            "adresse",
            "adresse_complement",
            "code_postal",
            "ville",
            "url",
            "latitude",
            "longitude",
            "nom_commercial",
            "nom_officiel",
            "siret",
            "naf_principal",
        ]
