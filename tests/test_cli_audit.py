"""Tests for audit CLI commands."""

import pytest
from click.testing import CliRunner
from envctl.cli_audit import audit_cmd
from envctl.audit import log_event, clear_audit_log


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def isolated_audit(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCTL_HOME", str(tmp_path))
    yield
    clear_audit_log()


def test_log_empty(runner):
    result = runner.invoke(audit_cmd, ["log"])
    assert result.exit_code == 0
    assert "No audit log entries found" in result.output


def test_log_shows_entries(runner):
    log_event("get", "myapp", "dev")
    log_event("add", "myapp", "prod")
    result = runner.invoke(audit_cmd, ["log"])
    assert result.exit_code == 0
    assert "myapp/dev" in result.output
    assert "myapp/prod" in result.output


def test_log_filter_by_project(runner):
    log_event("get", "myapp", "dev")
    log_event("get", "other", "staging")
    result = runner.invoke(audit_cmd, ["log", "--project", "myapp"])
    assert result.exit_code == 0
    assert "myapp/dev" in result.output
    assert "other" not in result.output


def test_log_limit(runner):
    for i in range(10):
        log_event("get", "myapp", f"p{i}")
    result = runner.invoke(audit_cmd, ["log", "--limit", "3"])
    assert result.exit_code == 0
    assert result.output.count("myapp/") == 3


def test_clear_confirmed(runner):
    log_event("get", "myapp", "dev")
    result = runner.invoke(audit_cmd, ["clear"], input="y\n")
    assert result.exit_code == 0
    assert "cleared" in result.output


def test_clear_aborted(runner):
    log_event("get", "myapp", "dev")
    result = runner.invoke(audit_cmd, ["clear"], input="n\n")
    assert result.exit_code != 0 or "Aborted" in result.output
