import pytest

from utils.cmd import cmd_run


class TestCmdRun:

    def test_working(self):
        cmd = "echo 'Hello World'"
        stdout = cmd_run(cmd, dry_run=False)
        assert "Hello World" in stdout  # type: ignore

    def test_dry_run(self):
        cmd = "echo 'Hello World'"
        stdout = cmd_run(cmd, dry_run=True)
        assert stdout is None

    def test_raise_if_failing(self):
        with pytest.raises(SystemError, match="psql:"):
            cmd_run("psql", dry_run=False)

    def test_raise_reports_returncode_when_stderr_is_empty(self):
        with pytest.raises(SystemError, match="returncode=137 stdout=partial stderr="):
            cmd_run("printf partial; exit 137", dry_run=False)
