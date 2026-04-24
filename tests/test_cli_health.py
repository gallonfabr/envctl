"""Tests for envctl.cli_health."""
import json
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from envctl.cli_health import health_cmd
from envctl.health import HealthReport, HealthIssue, HealthError


@pytest.fixture
def runner():
    return CliRunner()


def _clean_report():
    return HealthReport(
        project="myproject",
        profile="prod",
        score=100,
        grade="A",
        issues=[],
    )


def _warn_report():
    return HealthReport(
        project="myproject",
        profile="prod",
        score=60,
        grade="C",
        issues=[
            HealthIssue(severity="warning", code="LINT", message="lowercase key found"),
        ],
    )


def test_check_healthy_text_output(runner):
    with patch("envctl.cli_health.check_profile", return_value=_clean_report()):
        result = runner.invoke(health_cmd, ["check", "myproject", "prod"])
    assert result.exit_code == 0
    assert "100/100" in result.output
    assert "Healthy" in result.output
    assert "No issues" in result.output


def test_check_with_issues_text_output(runner):
    with patch("envctl.cli_health.check_profile", return_value=_warn_report()):
        result = runner.invoke(health_cmd, ["check", "myproject", "prod"])
    assert result.exit_code == 0
    assert "LINT" in result.output
    assert "lowercase key found" in result.output


def test_check_json_output(runner):
    with patch("envctl.cli_health.check_profile", return_value=_clean_report()):
        result = runner.invoke(health_cmd, ["check", "myproject", "prod", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["score"] == 100
    assert data["grade"] == "A"
    assert data["healthy"] is True
    assert data["issues"] == []


def test_check_json_with_issues(runner):
    with patch("envctl.cli_health.check_profile", return_value=_warn_report()):
        result = runner.invoke(health_cmd, ["check", "myproject", "prod", "--json"])
    data = json.loads(result.output)
    assert len(data["issues"]) == 1
    assert data["issues"][0]["code"] == "LINT"


def test_check_missing_profile_exits_nonzero(runner):
    with patch("envctl.cli_health.check_profile", side_effect=HealthError("not found")):
        result = runner.invoke(health_cmd, ["check", "myproject", "ghost"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_check_passes_password(runner):
    mock = MagicMock(return_value=_clean_report())
    with patch("envctl.cli_health.check_profile", mock):
        runner.invoke(health_cmd, ["check", "myproject", "prod", "--password", "s3cr3t"])
    mock.assert_called_once_with("myproject", "prod", password="s3cr3t")
