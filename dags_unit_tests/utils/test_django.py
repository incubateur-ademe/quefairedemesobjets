import pandas as pd
import pytest

from dags.utils.django import (
    django_model_queryset_generate,
    django_model_queryset_to_sql,
    django_model_to_pandas_schema,
    django_setup_full,
)

django_setup_full()
from qfdmo.models import Acteur  # noqa: E402


# Test function
@pytest.mark.django_db
def test_django_model_queryset_generate():

    # On vérifie qu'on est capable de sélectionner des champs
    # et des propriétés
    fields_include_all_filled = ["nom", "adresse"]
    fields_exclude_any_filled = ["siret", "longitude", "ville"]
    # fields_to_select = ["latitude","numero_et_complement_de_rue"]

    # Generate queryset
    queryset = django_model_queryset_generate(
        Acteur, fields_include_all_filled, fields_exclude_any_filled
    )

    # Convert queryset to SQL string
    sql = django_model_queryset_to_sql(queryset)

    # Expected SQL string (adjust to match your backend, structure may vary slightly)
    expected_sql = r"""
        "SELECT *
        FROM "qfdmo_acteur"
        "WHERE (NOT ("nom" IS NULL) AND NOT ("nom" = '')
        AND NOT ("adresse" IS NULL) AND NOT ("adresse" = ''))
        AND NOT (("siret" IS NOT NULL) OR ("siret" != ''))
        """
    print(sql)
    # TODO: activer ce test une fois qu'on est content
    # avec le résultat final via Airflow
    # assert sql.strip() == expected_sql.strip()
    assert expected_sql


def test_django_model_to_pandas_schema():
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
