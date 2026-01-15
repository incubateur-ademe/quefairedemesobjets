import json

from pydantic import BaseModel, ConfigDict


class SuggestionSourceModel(BaseModel):
    """
    This model is used to validate and manipulate the suggestion of source type.
    """

    model_config = ConfigDict(frozen=True)

    # Définition de tous les champs comme attributs optionnels
    identifiant_unique: str | None = None
    source_code: str | None = None
    identifiant_externe: str | None = None
    nom: str | None = None
    nom_commercial: str | None = None
    nom_officiel: str | None = None
    siret: str | None = None
    siren: str | None = None
    naf_principal: str | None = None
    description: str | None = None
    acteur_type_code: str | None = None
    url: str | None = None
    email: str | None = None
    telephone: str | None = None
    adresse: str | None = None
    adresse_complement: str | None = None
    code_postal: str | None = None
    ville: str | None = None
    latitude: str | None = None
    longitude: str | None = None
    horaires_osm: str | None = None
    horaires_description: str | None = None
    public_accueilli: str | None = None
    reprise: str | None = None
    exclusivite_de_reprisereparation: str | None = None
    uniquement_sur_rdv: str | None = None
    consignes_dacces: str | None = None
    statut: str | None = None
    commentaires: str | None = None
    label_codes: str | None = None
    acteur_service_codes: str | None = None
    proposition_service_codes: str | None = None
    lieu_prestation: str | None = None
    perimetre_adomicile_codes: str | None = None

    @classmethod
    def from_json(cls, json_data: str) -> "SuggestionSourceModel":
        data = json.loads(json_data)
        for key, value in data.items():
            if key.endswith("_codes"):
                data[key] = json.dumps(value)
            elif value is not None and value != "":
                data[key] = str(value)
        return cls.model_validate(data)

    @classmethod
    def get_ordered_fields(cls) -> list[tuple[str]]:
        GROUPED_FIELDS = [("latitude", "longitude")]

        ordered_fields = []
        grouped_fields_processed = []
        for field in cls.model_fields:
            # get grouped_fields from field
            group_fields = next(
                (
                    grouped_field
                    for grouped_field in GROUPED_FIELDS
                    if field in grouped_field
                ),
                None,
            )
            if group_fields is not None:
                if group_fields not in grouped_fields_processed:
                    grouped_fields_processed.append(group_fields)
                    ordered_fields.append(group_fields)
                continue
            ordered_fields.append((field,))
        return ordered_fields

    @classmethod
    def get_not_editable_fields(cls) -> list[str]:
        """
        Retourne la liste formatée des champs non éditables.
        """
        return [
            "acteur_service_codes",
            "identifiant_externe",
            "identifiant_unique",
            "label_codes",
            "proposition_service_codes",
            "source_code",
            "acteur_type_code",
            "perimetre_adomicile_codes",
        ]
