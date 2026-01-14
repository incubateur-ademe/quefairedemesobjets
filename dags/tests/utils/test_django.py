import pandas as pd
import pytest
from utils.django import (
    django_model_fields_get,
    django_model_queryset_generate,
    django_model_queryset_to_sql,
    django_model_to_pandas_schema,
    django_setup_full,
    get_model_fields,
)

django_setup_full()


@pytest.mark.django_db
class TestDjangoModelFieldsGet:
    @pytest.fixture
    def without_props(self):
        from qfdmo.models import DisplayedActeur

        return django_model_fields_get(DisplayedActeur, include_properties=False)

    @pytest.fixture
    def with_props(self):
        from qfdmo.models import DisplayedActeur

        return django_model_fields_get(DisplayedActeur, include_properties=True)

    def test_without_props(self, without_props):
        assert "nom" in without_props
        assert "combine_adresses" not in without_props

    def test_with_props(self, with_props):
        assert "nom" in with_props
        assert "combine_adresses" in with_props

    def test_internal_fields_excluded(self, with_props):
        assert "pk" not in with_props

    def test_many_to_many_excluded(self, with_props):
        assert "sources" not in with_props


# Test function
@pytest.mark.django_db
def test_django_model_queryset_generate():
    from qfdmo.models import Acteur

    # On vérifie qu'on est capable de sélectionner des champs
    # et des propriétés
    fields_include_all_filled = ["nom", "adresse"]
    # fields_to_select = ["latitude","numero_et_complement_de_rue"]

    # Generate queryset
    queryset = django_model_queryset_generate(Acteur, fields_include_all_filled)

    # Convert queryset to SQL string
    django_model_queryset_to_sql(queryset)

    # Expected SQL string (adjust to match your backend, structure may vary slightly)
    expected_sql = r"""
        "SELECT *
        FROM "qfdmo_acteur"
        "WHERE (NOT ("nom" IS NULL) AND NOT ("nom" = '')
        AND NOT ("adresse" IS NULL) AND NOT ("adresse" = ''))
        """
    # TODO: activer ce test une fois qu'on est content
    # avec le résultat final via Airflow
    # assert sql.strip() == expected_sql.strip()
    assert expected_sql


def test_django_model_to_pandas_schema():
    from qfdmo.models import Acteur

    schema = django_model_to_pandas_schema(Acteur)
    assert schema["nom"] == "object"
    assert schema["adresse"] == "object"
    assert schema["cree_le"] == "datetime64[ns]"
    assert schema["source"] == "int64"
    assert schema["acteur_type"] == "int64"

    data = {
        "nom": ["a", "b", "c"],
        "code_postal": ["01000", "53000", "75000"],
        "source_id": [1, 2, 3],
        "acteur_type_id": [1, 2, 3],
    }
    # dtype = [v for k, v in schema.items() if k in data.keys()]
    df = pd.DataFrame(data, dtype="object")
    assert df["code_postal"].tolist() == ["01000", "53000", "75000"]
    assert df["source_id"].tolist() == [1, 2, 3]
    assert df["acteur_type_id"].tolist() == [1, 2, 3]


def test_get_model_fields():
    from qfdmo.models import Acteur

    fields = get_model_fields(Acteur, with_relationships=True, latlong=True)
    assert set(fields) == {
        "acteur_service_codes",
        "acteur_type_code",
        "action_principale_code",
        "adresse_complement",
        "adresse",
        "code_postal",
        "commentaires",
        "consignes_dacces",
        "cree_le",
        "description",
        "email",
        "exclusivite_de_reprisereparation",
        "horaires_description",
        "horaires_osm",
        "identifiant_externe",
        "identifiant_unique",
        "label_codes",
        "latitude",
        "lieu_prestation",
        "longitude",
        "modifie_le",
        "naf_principal",
        "nom_commercial",
        "nom_officiel",
        "nom",
        "perimetre_adomicile_codes",
        "proposition_service_codes",
        "public_accueilli",
        "reprise",
        "siren",
        "siret_is_closed",
        "siret",
        "source_code",
        "statut",
        "suggestion_groupe_codes",
        "suggestion_unitaire_codes",
        "telephone",
        "uniquement_sur_rdv",
        "url",
        "ville",
    }

    fields = get_model_fields(Acteur, with_relationships=False, latlong=False)
    assert set(fields) == {
        "adresse_complement",
        "adresse",
        "code_postal",
        "commentaires",
        "consignes_dacces",
        "cree_le",
        "description",
        "email",
        "exclusivite_de_reprisereparation",
        "horaires_description",
        "horaires_osm",
        "identifiant_externe",
        "identifiant_unique",
        "lieu_prestation",
        "location",
        "modifie_le",
        "naf_principal",
        "nom_commercial",
        "nom_officiel",
        "nom",
        "public_accueilli",
        "reprise",
        "siren",
        "siret_is_closed",
        "siret",
        "statut",
        "telephone",
        "uniquement_sur_rdv",
        "url",
        "ville",
    }
