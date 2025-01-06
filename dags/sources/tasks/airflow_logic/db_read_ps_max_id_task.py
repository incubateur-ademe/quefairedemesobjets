from airflow import DAG
from airflow.operators.python import PythonOperator
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from sqlalchemy import text


# TODO : supprimer cette tache après avoir trouvé une solution pour le max_id
def db_read_ps_max_id_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="db_read_ps_max_id",
        python_callable=db_read_ps_max_id,
        dag=dag,
    )


def db_read_ps_max_id():
    engine = PostgresConnectionManager().engine

    # TODO : check if we need to manage the max id here
    dps_max_id = engine.execute(
        text("SELECT max(id) FROM qfdmo_displayedpropositionservice")
    ).scalar()

    return {
        "dps_max_id": dps_max_id,
    }
