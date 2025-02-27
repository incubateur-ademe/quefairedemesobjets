"""A template DAG to demonstrate how to
read from the Django DB. The DAG is placed
inside the "templates" folder whilst following
the same directory structure as production DAGS
so it can serve as e2e airflow test as well.

"""

from airflow import DAG
from airflow.operators.python import PythonOperator

with DAG(
    dag_id="template_read_db",
    dag_display_name="Template - Read DB",
    schedule=None,
    catchup=False,
    tags=["template"],
) as dag:

    def read_db(ti, params):
        from utils.django import django_setup_full

        settings = django_setup_full()
        from qfdmo.models import Acteur

        # Returning some settings info to help test
        # that Airflow uses the local DB when running
        # e2e tests
        ti.xcom_push(key="settings", value=settings)

        # Returning some acteur data to demonstrate
        # we can read from the test DB in e2e mode
        query = Acteur.objects.filter(
            nom__contains=params["include_acteurs_nom_contains"]
        )
        # Works because it's JSON-serializable
        ti.xcom_push(key="acteurs_list", value=list(query.values("nom")))
        # Returns None and causes task to fail because XCOM
        # cannot serialize a QuerySet
        ti.xcom_push(key="acteurs_query", value=query.all())

    def read_db_task(dag: DAG) -> PythonOperator:
        return PythonOperator(
            task_id="read_db",
            python_callable=read_db,
            provide_context=True,
            dag=dag,
        )

    read_db_task(dag)
