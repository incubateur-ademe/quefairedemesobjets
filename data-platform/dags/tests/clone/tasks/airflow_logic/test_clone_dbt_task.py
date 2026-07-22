from unittest.mock import MagicMock, patch

import pytest
from airflow.sdk.exceptions import AirflowSkipException
from clone.tasks.airflow_logic.clone_dbt_task import (
    PARAM_DBT_RUN_COMMAND,
    PARAM_DBT_TEST_COMMAND,
    PARAM_RUN_DBT,
    RUN_ACTION,
    TEST_ACTION,
    clone_dbt_params,
    clone_dbt_wrapper,
)

RUN_COMMAND = "dbt run --select +tag:etablissement"
TEST_COMMAND = "dbt test --select +tag:etablissement"


@pytest.fixture
def ti():
    task_instance = MagicMock()
    task_instance.get_template_context.return_value = {}
    return task_instance


@pytest.fixture
def params():
    return {
        PARAM_RUN_DBT: True,
        PARAM_DBT_RUN_COMMAND: RUN_COMMAND,
        PARAM_DBT_TEST_COMMAND: TEST_COMMAND,
        "dry_run": False,
    }


class TestCloneDbtParams:

    def test_builds_full_commands_from_select(self):
        built = clone_dbt_params(dbt_select="+tag:etablissement")
        assert built[PARAM_DBT_RUN_COMMAND].value == RUN_COMMAND
        assert built[PARAM_DBT_TEST_COMMAND].value == TEST_COMMAND
        assert built[PARAM_RUN_DBT].value is True


class TestCloneDbtWrapper:

    def test_skip_when_command_missing(self, ti, params):
        params[PARAM_DBT_RUN_COMMAND] = ""
        with patch(
            "clone.tasks.airflow_logic.clone_dbt_task.BashOperator"
        ) as mock_bash:
            with pytest.raises(AirflowSkipException):
                clone_dbt_wrapper(RUN_ACTION, ti=ti, params=params)
            mock_bash.assert_not_called()

    def test_skip_when_run_dbt_is_false(self, ti, params):
        params[PARAM_RUN_DBT] = False
        with patch(
            "clone.tasks.airflow_logic.clone_dbt_task.BashOperator"
        ) as mock_bash:
            with pytest.raises(AirflowSkipException):
                clone_dbt_wrapper(RUN_ACTION, ti=ti, params=params)
            mock_bash.assert_not_called()

    def test_skip_when_dry_run(self, ti, params):
        params["dry_run"] = True
        with patch(
            "clone.tasks.airflow_logic.clone_dbt_task.BashOperator"
        ) as mock_bash:
            with pytest.raises(AirflowSkipException):
                clone_dbt_wrapper(RUN_ACTION, ti=ti, params=params)
            mock_bash.assert_not_called()

    def test_run_uses_dbt_run_command_param(self, ti, params):
        with patch(
            "clone.tasks.airflow_logic.clone_dbt_task.BashOperator"
        ) as mock_bash:
            clone_dbt_wrapper(RUN_ACTION, ti=ti, params=params)
            _, kwargs = mock_bash.call_args
            assert kwargs["bash_command"] == RUN_COMMAND
            mock_bash.return_value.execute.assert_called_once_with(context={})

    def test_test_uses_dbt_test_command_param(self, ti, params):
        with patch(
            "clone.tasks.airflow_logic.clone_dbt_task.BashOperator"
        ) as mock_bash:
            clone_dbt_wrapper(TEST_ACTION, ti=ti, params=params)
            _, kwargs = mock_bash.call_args
            assert kwargs["bash_command"] == TEST_COMMAND
            mock_bash.return_value.execute.assert_called_once_with(context={})
