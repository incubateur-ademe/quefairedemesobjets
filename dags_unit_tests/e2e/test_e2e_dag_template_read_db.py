"""A test to ensure our test DB integration is working properly:
- create acteurs outside DAG (should write into test DB)
- read acteurs inside DAG (should read from test DB)"""

import pytest

from dags_unit_tests.e2e.utils import DATE_IN_PAST, airflow_init, dag_get, ti_get

airflow_init()


@pytest.mark.django_db()
class TestE2ETemplateReadDb:

    @pytest.fixture
    def create_acteurs(self):
        from django.contrib.gis.geos import Point

        from qfdmo.models import Acteur, ActeurType

        at = ActeurType(code="my_at")
        at.save()
        loc = Point(1, 2)
        Acteur(nom="🟢 included 1", acteur_type=at, location=loc).save()
        Acteur(nom="🔴 excluded 1", acteur_type=at, location=loc).save()
        Acteur(nom="🟢 included 2", acteur_type=at, location=loc).save()

    @pytest.fixture
    def dag_test(self, create_acteurs):
        dag = dag_get("template_read_db")
        # We use .test() and not the tempting .run()
        # which has a richer API but was removed
        # on Oct 2024 for Airflow 3:
        # https://github.com/apache/airflow/pull/42761
        dag.test(
            execution_date=DATE_IN_PAST,
            # Values put here will be available under "params"
            # argument of Airflow task functions
            run_conf={
                "include_acteurs_nom_contains": "included",
            },
        )
        return dag

    @pytest.fixture
    def ti(self, dag_test):
        tis = dag_test.get_task_instances()
        return ti_get(tis, "read_db")

    @pytest.fixture
    def ti_settings(self, ti):
        return ti.xcom_pull(key="settings", task_ids="read_db")

    @pytest.fixture
    def ti_acteurs_list(self, ti):
        return ti.xcom_pull(key="acteurs_list", task_ids="read_db")

    @pytest.fixture
    def ti_acteurs_query(self, ti):
        return ti.xcom_pull(key="acteurs_query", task_ids="read_db")

    def test_db_is_local_test(self, ti_settings):
        # Airflow should use the local test DB
        dbs = ti_settings["DATABASES"]
        db_test = {"HOST": "localhost", "PORT": 6543, "NAME": "test_qfdmo"}
        assert dbs["default"] == db_test
        assert dbs["readonly"] == db_test

    def test_acteurs_list_works(self, ti_acteurs_list):
        # We should we able to retrieve acteurs created via models outside Airflow
        assert len(ti_acteurs_list) == 2
        names = sorted([a["nom"] for a in ti_acteurs_list])
        assert names == ["🟢 included 1", "🟢 included 2"]

    def test_acteurs_query_fails(self, ti_acteurs_query):
        # Reading a queryset from XCOM fails as Django is unable
        # to serialize, exception from airflow/models/xcom.py:
        # json.dumps(value, cls=XComEncoder).encode("UTF-8")
        # TypeError: cannot serialize object of
        # type <class 'django.db.models.query.QuerySet'>
        assert ti_acteurs_query is None
