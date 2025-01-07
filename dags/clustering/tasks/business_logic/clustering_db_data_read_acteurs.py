import numpy as np
import pandas as pd
from sqlalchemy import Column, Integer, MetaData, String, Table, and_, or_
from sqlalchemy.dialects import postgresql

"""
TODO:
 - initialiser django au sein du contexte airflow
 puis dans le airflow_logic/*_task.py:
    - charger le modèle DisplayedActeur
    - appeler la fonction clustering_params_to_django_queryset
    - convertir le queryset SQL puis en dataframe
    - supprimer clustering_params_to_sql_query qui n'est plus utilisée
from django.db.models import Q

def clustering_params_to_django_queryset(
    model,
    include_source_ids,
    include_acteur_type_ids,
    include_if_fields_filled,
    exclude_if_any_field_filled,
):
    queryset = model.objects.all()

    # Filter by source_id
    if include_source_ids:
        queryset = queryset.filter(source_id__in=include_source_ids)

    # Filter by acteur_type_id
    if include_acteur_type_ids:
        queryset = queryset.filter(acteur_type_id__in=include_acteur_type_ids)

    # Ensure fields in include_if_fields_filled are not empty
    if include_if_fields_filled:
        for field in include_if_fields_filled:
            queryset = queryset.filter(
                ~Q(**{f"{field}__isnull": True}), ~Q(**{f"{field}": ""})
            )

    # Exclude entries where any field in exclude_if_any_field_filled is filled
    if exclude_if_any_field_filled:
        for field in exclude_if_any_field_filled:
            queryset = queryset.exclude(
                ~Q(**{f"{field}__isnull": True}) & ~Q(**{f"{field}": ""})
            )

    return queryset
"""


def clustering_params_to_sql_query(
    table_name,
    include_source_ids,
    include_acteur_type_ids,
    include_if_all_fields_filled,
    exclude_if_any_field_filled,
):
    # Dynamically create metadata and table definition
    metadata = MetaData()
    table = Table(
        table_name,
        metadata,
        Column("source_id", Integer),
        Column("acteur_type_id", Integer),
        *[
            Column(field, String)
            for field in include_if_all_fields_filled + exclude_if_any_field_filled
        ],
    )

    query = table.select()

    # Add source_id filter
    if include_source_ids:
        query = query.where(table.c.source_id.in_(include_source_ids))

    # Add acteur_type_id filter
    if include_acteur_type_ids:
        query = query.where(table.c.acteur_type_id.in_(include_acteur_type_ids))

    # Add include_if_all_fields_filled filters
    if include_if_all_fields_filled:
        non_empty_conditions = [
            and_(table.c[field] != "", table.c[field] is not None)
            for field in include_if_all_fields_filled
        ]
        query = query.where(and_(*non_empty_conditions))

    # Add exclude_if_any_field_filled filters
    if exclude_if_any_field_filled:
        empty_conditions = [
            or_(table.c[field] == "", table.c[field] is None)
            for field in exclude_if_any_field_filled
        ]
        query = query.where(~or_(*empty_conditions))

    # Compile the query into a SQL string
    compiled_query = str(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    ).replace(f"{table_name}.", "")
    return compiled_query


def clustering_db_data_read_acteurs(
    include_source_ids,
    include_acteur_type_ids,
    include_if_all_fields_filled,
    exclude_if_any_field_filled,
    engine,
) -> tuple[pd.DataFrame, str]:
    query = clustering_params_to_sql_query(
        "qfdmo_displayedacteur",
        include_source_ids,
        include_acteur_type_ids,
        include_if_all_fields_filled,
        exclude_if_any_field_filled,
    )
    df = pd.read_sql_query(query, engine).replace({np.nan: None})
    return df, query
