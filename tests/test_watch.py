"""Tests for envctl.watch drift detection."""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from envctl.watch import check_drift, drift_summary
from envctl.cli_watch import watch_cmd


PROFILE_DATA = {"vars": {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_ENV": "production"}}


@pytest.fixture
def mock_get_profile():
    with patch("envctl.watch.get_profile", return_value=PROFILE_DATA) as m:
        yield m


@pytest.fixture
def mock_log():
    with patch("envctl.watch.log_event") as m:
        yield m


def test_no_drift(mock_get_profile, mock_log):
    env = {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_ENV": "production"}
    drifts = check_drift("proj", "prod", env)
    assert drifts == []
    mock_log.assert_not_called()


def test_missing_key(mock_get_profile, mock_log):
    env = {"DB_HOST": "localhost"}
    drifts = check_drift("proj", "prod", env)
    keys = {d["key"] for d in drifts}
    assert "DB_PORT" in keys
    assert "APP_ENV" in keys
    assert all(d["status"] == "missing" for d in drifts if d["key"] in {"DB_PORT", "APP_ENV"})


def test_changed_key(mock_get_profile, mock_log):
    env = {"DB_HOST": "remotehost", "DB_PORT": "5432", "APP_ENV": "production"}
    drifts = check_drift("proj", "prod", env)
    assert len(drifts) == 1
    assert drifts[0]["key"] == "DB_HOST"
    assert drifts[0]["status"] == "changed"
    assert drifts[0]["actual"] == "remotehost"


def test_drift_logs_event(mock_get_profile, mock_log):
    env = {}
    check_drift("proj", "prod", env)
    mock_log.assert_called_once()


def test_drift_summary():
    drifts = [
        {"key": "A", "status": "missing"},
        {"key": "B", "status": "changed"},
        {"key": "C", "status": "missing"},
    ]
    summary = drift_summary(drifts)
    assert summary["missing"] == 2
    assert summary["changed"] == 1


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_no_drift(runner):
    with patch("envctl.cli_watch.check_drift", return_value=[]):
        result = runner.invoke(watch_cmd, ["check", "proj", "prod"])
    assert result.exit_code == 0
    assert "No drift" in result.output


def test_cli_with_drift(runner):
    drifts = [{"key": "DB_HOST", "expected": "localhost", "actual": "other", "status": "changed"}]
    with patch("envctl.cli_watch.check_drift", return_value=drifts):
        result = runner.invoke(watch_cmd, ["check", "proj", "prod"])
    assert "CHANGED" in result.output
    assert "DB_HOST" in result.output


def test_cli_summary_flag(runner):
    drifts = [{"key": "X", "expected": "a", "actual": None, "status": "missing"}]
    with patch("envctl.cli_watch.check_drift", return_value=drifts):
        result = runner.invoke(watch_cmd, ["check", "proj", "prod", "--summary"])
    assert "missing" in result.output
