"""Tests for envctl.cli_badge."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch

from envctl.cli_badge import badge_cmd
from envctl.badge import BadgeError


@pytest.fixture
def runner():
    return CliRunner()


SAMPLE_BADGE = {
    "project": "myproject",
    "profile": "dev",
    "status": "ok",
    "locked": "false",
    "expired": "false",
    "pinned": "false",
    "var_count": "2",
}


def test_show_badge_success(runner):
    with patch("envctl.cli_badge.profile_badge", return_value=SAMPLE_BADGE), \
         patch("envctl.cli_badge.format_badge", return_value="  myproject/dev [ok] 🔓 ✅ vars=2"):
        result = runner.invoke(badge_cmd, ["show", "myproject", "dev"])
    assert result.exit_code == 0
    assert "myproject/dev" in result.output


def test_show_badge_json(runner):
    with patch("envctl.cli_badge.profile_badge", return_value=SAMPLE_BADGE):
        result = runner.invoke(badge_cmd, ["show", "myproject", "dev", "--json"])
    assert result.exit_code == 0
    assert "status: ok" in result.output
    assert "var_count: 2" in result.output


def test_show_badge_missing_profile(runner):
    with patch("envctl.cli_badge.profile_badge", side_effect=BadgeError("not found")):
        result = runner.invoke(badge_cmd, ["show", "myproject", "ghost"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_project_badges_success(runner):
    badges = [SAMPLE_BADGE, {**SAMPLE_BADGE, "profile": "prod", "var_count": "1"}]
    with patch("envctl.cli_badge.project_badges", return_value=badges), \
         patch("envctl.cli_badge.format_badge", side_effect=lambda b: f"badge:{b['profile']}"):
        result = runner.invoke(badge_cmd, ["project", "myproject"])
    assert result.exit_code == 0
    assert "badge:dev" in result.output
    assert "badge:prod" in result.output


def test_project_badges_empty(runner):
    with patch("envctl.cli_badge.project_badges", return_value=[]):
        result = runner.invoke(badge_cmd, ["project", "emptyproject"])
    assert result.exit_code == 0
    assert "No profiles" in result.output


def test_project_badges_missing_project(runner):
    with patch("envctl.cli_badge.project_badges", side_effect=BadgeError("not found")):
        result = runner.invoke(badge_cmd, ["project", "ghost"])
    assert result.exit_code != 0
    assert "not found" in result.output
