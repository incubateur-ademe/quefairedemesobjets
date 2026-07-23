import dedupe

FEATURES_NAMES_FROM_DATASET = [
    "nom",
    "description",
    "acteur_type_id",
    "source_id",
    "adresse",
    "adresse_complement",
    "code_postal",
    "ville",
    "url",
    "email",
    "telephone",
    "nom_commercial",
    "nom_officiel",
    "siren",
    "siret",
    "naf_principal",
    "horaires_osm",
    "horaires_description",
    "horaires_osm",
    "public_accueilli",
    "reprise",
    "exclusivite_de_reprisereparation",
    "reprise",
    "uniquement_sur_rdv",
    "consignes_dacces",
    "action_principale_id",
    "lieu_prestation",
    "code_commune_insee",
    "epci_id",
    "action_reparer",
    "action_acheter",
    "action_revendre",
    "action_donner",
    "action_louer",
    "action_mettreenlocation",
    "action_emprunter",
    "action_preter",
    "action_echanger",
    "action_trier",
    "action_rapporter",
]

DEDUPE_VARIABLES_CONFIG_MANDATORY = [
    dedupe.variables.String(name="nom", field="nom"),
    dedupe.variables.Categorical(
        "acteur_type_id",
        categories=["1", "2", "3", "4", "5", "7", "8", "9", "10", "11", "12"],
    ),
    dedupe.variables.String(name="adresse", field="adresse", has_missing=True),
    dedupe.variables.Exact(name="code_postal", field="code_postal", has_missing=True),
    dedupe.variables.String(name="ville", field="ville", has_missing=True),
    dedupe.variables.LatLong("location"),
    dedupe.variables.Categorical(
        "action_reparer", categories=["True", "False"], has_missing=True
    ),
    dedupe.variables.Categorical(
        "action_acheter", categories=["True", "False"], has_missing=True
    ),
    dedupe.variables.Categorical(
        "action_revendre", categories=["True", "False"], has_missing=True
    ),
    dedupe.variables.Categorical(
        "action_donner", categories=["True", "False"], has_missing=True
    ),
    dedupe.variables.Categorical(
        "action_louer", categories=["True", "False"], has_missing=True
    ),
    dedupe.variables.Categorical(
        "action_mettreenlocation", categories=["True", "False"], has_missing=True
    ),
    dedupe.variables.Categorical(
        "action_emprunter", categories=["True", "False"], has_missing=True
    ),
    dedupe.variables.Categorical(
        "action_preter", categories=["True", "False"], has_missing=True
    ),
    dedupe.variables.Categorical(
        "action_echanger", categories=["True", "False"], has_missing=True
    ),
    dedupe.variables.Categorical(
        "action_trier", categories=["True", "False"], has_missing=True
    ),
    dedupe.variables.Categorical(
        "action_rapporter", categories=["True", "False"], has_missing=True
    ),
]

DEDUPE_VARIABLES_CONFIG_FULL = DEDUPE_VARIABLES_CONFIG_MANDATORY + [
    dedupe.variables.Text("description", has_missing=True),
    dedupe.variables.String(
        name="adresse_complement", field="adresse_complement", has_missing=True
    ),
    dedupe.variables.Exact("url", has_missing=True),
    dedupe.variables.Exact("email", has_missing=True),
    dedupe.variables.Exact("telephone", has_missing=True),
    dedupe.variables.String(
        name="nom_commercial", field="nom_commercial", has_missing=True
    ),
    dedupe.variables.String(
        name="nom_officiel", field="nom_officiel", has_missing=True
    ),
    dedupe.variables.Exact("siren", has_missing=True),
    dedupe.variables.Exact("siret", has_missing=True),
    dedupe.variables.Exact("naf_principal", has_missing=True),
    dedupe.variables.Text(name="horaires_osm", field="horaires_osm", has_missing=True),
    dedupe.variables.Text(
        name="horaires_description", field="horaires_description", has_missing=True
    ),
    dedupe.variables.Categorical(
        "public_accueilli",
        categories=[
            "Aucun",
            "Particuliers",
            "Particuliers et professionnels",
            "Professionnels",
        ],
        has_missing=True,
    ),
    dedupe.variables.Categorical(
        name="reprise",
        field="reprise",
        categories=["1 pour 0", "1 pour 1"],
        has_missing=True,
    ),
    dedupe.variables.Categorical(
        name="exclusivite_de_reprisereparation",
        field="exclusivite_de_reprisereparation",
        categories=["True", "False"],
        has_missing=True,
    ),
    dedupe.variables.Categorical(
        "uniquement_sur_rdv", categories=["True", "False"], has_missing=True
    ),
    dedupe.variables.Text("consignes_dacces", has_missing=True),
    dedupe.variables.Categorical(
        "action_principale_id",
        categories=["7", "8", "5", "6", "1", "9", "3", "2", "12", "11", "4"],
        has_missing=True,
    ),
    dedupe.variables.Categorical(
        "lieu_prestation",
        categories=["A_DOMICILE", "SUR_PLACE", "SUR_PLACE_OU_A_DOMICILE"],
        has_missing=True,
    ),
    dedupe.variables.Exact("code_commune_insee", has_missing=True),
    dedupe.variables.Exact("epci_id", has_missing=True),
    dedupe.variables.Interaction(
        "nom",
        "nom_commercial",
        "nom_officiel",
    ),
    dedupe.variables.Interaction(
        "adresse",
        "adresse_complement",
    ),
    dedupe.variables.Interaction("horaires_osm", "horaires_description"),
    dedupe.variables.Interaction("reprise", "exclusivite_de_reprisereparation"),
]

DEDUPE_VARIABLES_CONFIG_RESTRICTED = DEDUPE_VARIABLES_CONFIG_MANDATORY + [
    dedupe.variables.String(
        name="nom_commercial", field="nom_commercial", has_missing=True
    ),
    dedupe.variables.Exact("siren", has_missing=True),
    dedupe.variables.Exact("siret", has_missing=True),
    dedupe.variables.Categorical(
        "public_accueilli",
        categories=[
            "Aucun",
            "Particuliers",
            "Particuliers et professionnels",
            "Professionnels",
        ],
        has_missing=True,
    ),
    dedupe.variables.Categorical(
        "action_principale_id",
        categories=["7", "8", "5", "6", "1", "9", "3", "2", "12", "11", "4"],
        has_missing=True,
    ),
    dedupe.variables.String(
        name="adresse_complement", field="adresse_complement", has_missing=True
    ),
    dedupe.variables.Exact("code_commune_insee", has_missing=True),
    dedupe.variables.Exact("epci_id", has_missing=True),
    dedupe.variables.Interaction(
        "nom",
        "nom_commercial",
    ),
    dedupe.variables.Interaction(
        "adresse",
        "adresse_complement",
    ),
]
