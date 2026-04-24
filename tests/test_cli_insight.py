"""Tests for envctl.cli_insight CLI commands."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envctl.cli_insight import insight_cmd
from envctl.insight import InsightError, ProfileInsight, ProjectInsight


@pytest.fixture
def runner():
    return CliRunner()


_PROFILE_INS = ProfileInsight(
    project="myproject",
    profile="dev",
    var_count=3,
    is_locked=False,
    is_expired=False,
    is_pinned=True,
    expiry="2099-01-01",
    recent_applies=5,
    tags=["local", "dev"],
)

_PROJECT_INS = ProjectInsight(
    project="myproject",
    profile_count=2,
    total_vars=5,
    locked_count=1,
    expired_count=0,
    pinned_profile="dev",
    profiles=[_PROFILE_INS],
)


def test_profile_cmd_text(runner):
    with patch("envctl.cli_insight.profile_insight", return_value=_PROFILE_INS):
        result = runner.invoke(insight_cmd, ["profile", "myproject", "dev"])
    assert result.exit_code == 0
    assert "3" in result.output
    assert "2099-01-01" in result.output
    assert "local" in result.output


def test_profile_cmd_json(runner):
    with patch("envctl.cli_insight.profile_insight", return_value=_PROFILE_INS):
        result = runner.invoke(insight_cmd, ["profile", "myproject", "dev", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["var_count"] == 3
    assert data["is_pinned"] is True


def test_profile_cmd_missing(runner):
    with patch("envctl.cli_insight.profile_insight", side_effect=InsightError("not found")):
        result = runner.invoke(insight_cmd, ["profile", "myproject", "ghost"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_project_cmd_text(runner):
    with patch("envctl.cli_insight.project_insight", return_value=_PROJECT_INS):
        result = runner.invoke(insight_cmd, ["project", "myproject"])
    assert result.exit_code == 0
    assert "myproject" in result.output
    assert "dev" in result.output


def test_project_cmd_json(runner):
    with patch("envctl.cli_insight.project_insight", return_value=_PROJECT_INS):
        result = runner.invoke(insight_cmd, ["project", "myproject", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["profile_count"] == 2
    assert data["pinned_profile"] == "dev"


def test_project_cmd_missing(runner):
    with patch("envctl.cli_insight.project_insight", side_effect=InsightError("not found")):
        result = runner.invoke(insight_cmd, ["project", "ghost"])
    assert result.exit_code != 0
    assert "not found" in result.output
