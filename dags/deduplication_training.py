from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
from shapely import Point
from airflow.providers.postgres.hooks.postgres import PostgresHook
import dedupe
from shapely.wkb import loads
from importlib import import_module
from pathlib import Path

env = Path(__file__).parent.name
utils = import_module(f"{env}.utils.utils")
default_args = {
    "owner": "airflow",
    "start_date": datetime(2024, 9, 11),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    utils.get_dag_name(__file__, "dedupe_actors_training"),
    default_args=default_args,
    description="DAG for dedupe actor training",
    schedule_interval=None,
    params={"threshold": 0.8, "acteur_type": 4},
    catchup=False,
)


def read_data(**kwargs):
    pg_hook = PostgresHook(postgres_conn_id=utils.get_db_conn_id(__file__))
    engine = pg_hook.get_sqlalchemy_engine()

    query = """WITH actor_counts AS (
        SELECT
            da.identifiant_unique,
            COUNT(dp.action_id) AS total_action_count,
            SUM(CASE WHEN dp.action_id = 5 THEN 1 ELSE 0 END) AS action_5_count
        FROM
            qfdmo_displayedacteur da
        JOIN
            qfdmo_displayedpropositionservice dp
        ON
            da.identifiant_unique = dp.acteur_id
        WHERE
            da.source_id NOT IN (12, 45, 1) and statut='ACTIF'
        GROUP BY
            da.identifiant_unique
    )
    SELECT
        da.*
    FROM
        qfdmo_displayedacteur da
    JOIN
        actor_counts ac
    ON
        da.identifiant_unique = ac.identifiant_unique
    WHERE
        ac.action_5_count = 0;
    """
    df = pd.read_sql(query, engine)
    return df


def parse_location(wkb_data):
    if wkb_data:  # Check if the WKB data is not None or empty
        try:
            point = loads(wkb_data)
            if isinstance(point, Point) and not point.is_empty:
                return (point.y, point.x)
        except Exception as e:
            print(f"Error parsing location: {e}")
    return (None, None)


def clean_location(latlon_tuple):
    if latlon_tuple and len(latlon_tuple) == 2:
        lat, lon = latlon_tuple
        if (
            lat is not None
            and lon is not None
            and -90 <= lat <= 90
            and -180 <= lon <= 180
        ):
            return latlon_tuple
    return None  # Return None for invalid or missing data


def clean_string(value):
    return value.strip() if value and value.strip() != "" else None


def preprocessing(**kwargs):
    df = kwargs["ti"].xcom_pull(task_ids="read_data")
    df["location_latlon"] = df["location"].apply(parse_location)
    df["location_latlon"] = df["location_latlon"].apply(clean_location)
    df = df[df["location_latlon"].notnull()]

    # Apply cleaning to relevant fields
    fields_to_clean = [
        "nom",
        "adresse",
        "email",
        "telephone",
        "nom_commercial",
        "nom_officiel",
        "siret",
        "naf_principal",
        "url",
        "ville",
        "adresse_complement",
        "telephone",
        "nom_officiel",
    ]
    for field in fields_to_clean:
        df[field] = df[field].apply(clean_string)

    df["siret"] = df["siret"].apply(lambda x: x if pd.notnull(x) else None)

    return df


def dedupe_training(**kwargs):
    df = kwargs["ti"].xcom_pull(task_ids="preprocessing")

    acteur_type = kwargs["params"]["acteur_type"]
    threshold = kwargs["params"]["threshold"]

    df_dech = df[df["acteur_type_id"] == acteur_type]
    df_sample = df_dech.sample(frac=0.8)
    df_dict_sample = df_sample.to_dict(orient="index")

    # Define dedupe fields
    fields = [
        dedupe.variables.String("nom", crf=True, name="name"),
        dedupe.variables.Exact("code_postal", name="postal_code"),
        dedupe.variables.Exact("ville", name="ville"),
        dedupe.variables.LatLong("location_latlon", name="latlon"),
        dedupe.variables.String("adresse", name="adresse"),
        dedupe.variables.String("siret", name="siret"),
    ]

    # Initialize and train the deduper
    deduper = dedupe.Dedupe(fields)
    deduper.prepare_training(df_dict_sample)
    # TODO: Add labelized examples
    deduper.train()

    clusters = deduper.partition(df_dict_sample, threshold)

    # Map clusters back to the original data
    cluster_id_map = {
        record_id: cluster_id
        for cluster_id, (record_ids, _) in enumerate(clusters)
        for record_id in record_ids
    }

    for record_id, record in df_dict_sample.items():
        record["cluster_id"] = cluster_id_map.get(record_id, -1)

    df_with_clusters = pd.DataFrame.from_dict(df_dict_sample, orient="index")

    filtered_df = df_with_clusters.groupby("cluster_id").filter(lambda x: len(x) >= 2)

    # TODO: Move to S3
    filtered_df.to_csv("duplicated_commerce_actors.csv", index=False)


# Define the tasks
read_data_task = PythonOperator(
    task_id="read_data", python_callable=read_data, provide_context=True, dag=dag
)

preprocessing_task = PythonOperator(
    task_id="preprocessing",
    python_callable=preprocessing,
    provide_context=True,
    dag=dag,
)

training_task = PythonOperator(
    task_id="dedupe_training",
    python_callable=dedupe_training,
    provide_context=True,
    dag=dag,
)

read_data_task >> preprocessing_task >> training_task
