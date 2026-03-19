import json

from pydantic import BaseModel, ConfigDict
from qfdmo.models.acteur import Acteur, RevisionActeur


class SuggestionSourceModel(BaseModel):
    """
    This model is used to validate and manipulate the suggestion of source type.
    Represent any updates for a given object :
    Acteur, RevisionActeur, ParentRevisionActeur.
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
    def from_dict(cls, data: dict) -> "SuggestionSourceModel":
        return cls(**{key: data.get(key, "") for key in data.keys()})

    @classmethod
    def from_acteur(
        cls,
        acteur: Acteur | RevisionActeur | None,
        fields_to_include: list[str] | None = None,
    ) -> "SuggestionSourceModel":
        """
        Extract values from an Acteur or RevisionActeur instance
        using SuggestionSourceModel fields.
        Returns a SuggestionSourceModel instance with extracted values.
        Empty string is returned for missing or None values.
        """

        def get_field_from_code(
            acteur: Acteur | RevisionActeur, field_name: str
        ) -> str:
            """Extract code from a ForeignKey field."""
            if field_name == "source_code":
                source_obj = getattr(acteur, "source", None)
                return source_obj.code if source_obj else ""
            if not field_name.endswith("_code"):
                raise ValueError(f"Field {field_name} is not a code field")
            fk_field_name = field_name.removesuffix("_code")
            object_field = getattr(acteur, fk_field_name, None)
            return object_field.code if object_field else ""

        def get_field_from_proposition_service_codes(
            acteur: Acteur | RevisionActeur,
        ) -> str:
            """Extract proposition_service_codes as JSON string."""
            prop_services = (
                list(acteur.proposition_services.all())
                if hasattr(acteur, "proposition_services")
                else []
            )
            if prop_services:
                prop_data = sorted(
                    [
                        {
                            "action": prop.action.code,
                            "sous_categories": sorted(
                                [sc.code for sc in prop.sous_categories.all()]
                            ),
                        }
                        for prop in prop_services
                    ],
                    key=lambda x: x["action"],
                )
                return json.dumps(prop_data, ensure_ascii=False)
            return ""

        def get_field_from_perimetre_adomicile_codes(
            acteur: Acteur | RevisionActeur,
        ) -> str:
            """Extract perimetre_adomicile_codes as JSON string."""
            perimetres = (
                list(acteur.perimetre_adomiciles.all())
                if hasattr(acteur, "perimetre_adomiciles")
                else []
            )
            return (
                json.dumps(
                    sorted(
                        [
                            {"type": perimetre.type, "valeur": perimetre.valeur}
                            for perimetre in perimetres
                        ],
                        key=lambda x: (x["type"], x["valeur"]),
                    ),
                    ensure_ascii=False,
                )
                if perimetres
                else ""
            )

        def get_field_from_codes(
            acteur: Acteur | RevisionActeur, field_name: str
        ) -> str:
            """Extract codes from ManyToMany fields as JSON string."""
            if not field_name.endswith("_codes"):
                raise ValueError(f"Field {field_name} is not a codes field")
            # Remove _codes suffix and add 's' to get the ManyToMany field name
            # e.g., label_codes -> labels, acteur_service_codes -> acteur_services
            m2m_field_name = field_name.removesuffix("_codes") + "s"
            m2m_objects = (
                list(getattr(acteur, m2m_field_name).all())
                if hasattr(acteur, m2m_field_name)
                else []
            )
            return (
                json.dumps(
                    sorted([obj.code for obj in m2m_objects]), ensure_ascii=False
                )
                if m2m_objects
                else ""
            )

        if acteur is None:
            return cls()

        model_fields = SuggestionSourceModel.model_fields.keys()
        fields_to_process = (
            fields_to_include if fields_to_include else list(model_fields)
        )

        values = {}
        for field_name in fields_to_process:
            if field_name not in model_fields:
                raise ValueError(
                    f"Field {field_name} not found in SuggestionSourceModel"
                )
            if field_name.endswith("_code"):
                values[field_name] = get_field_from_code(acteur, field_name)
            elif field_name == "proposition_service_codes":
                values[field_name] = get_field_from_proposition_service_codes(acteur)
            elif field_name == "perimetre_adomicile_codes":
                values[field_name] = get_field_from_perimetre_adomicile_codes(acteur)
            elif field_name.endswith("_codes"):
                values[field_name] = get_field_from_codes(acteur, field_name)
            else:
                # Handle regular fields
                value = getattr(acteur, field_name, None)
                values[field_name] = str(value) if value is not None else ""

        return cls(**values)

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
        Returns the list of fields that are not editable.

        For now, we don't allow to update these fields because the values are specific
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

    @classmethod
    def get_not_reportable_on_revision_fields(cls) -> list[str]:
        """
        Returns the list of fields that are not reportable on revisionacteur.

        - identifiants aren't reportable on revisionacteur
          because they are generated by the system.
        """
        return [
            "identifiant_externe",
            "identifiant_unique",
        ]

    @classmethod
    def get_not_reportable_on_parent_fields(cls) -> list[str]:
        """
        Returns the list of fields that are not reportable on parentrevisionacteur.

        - identifiants aren't reportable on parentrevisionacteur
          because they are generated by the system.
        - fields ending with _codes aren't reportable on parentrevisionacteur because
          they are inherited from the the children.
        """
        return [
            "acteur_service_codes",
            "identifiant_externe",
            "identifiant_unique",
            "label_codes",
            "proposition_service_codes",
            "perimetre_adomicile_codes",
        ]
