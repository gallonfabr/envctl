"""Tests for envctl.cli_quota_ceiling."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envctl.cli_quota_ceiling import quota_ceiling_cmd
from envctl.quota_ceiling import GuardResult, QuotaCeilingError


@pytest.fixture()
def runner():
    return CliRunner()


MOD = "envctl.cli_quota_ceiling"


# --- check-vars ---

def test_check_vars_allowed(runner):
    with patch(f"{MOD}.check_var_ceiling", return_value=GuardResult(allowed=True)):
        result = runner.invoke(quota_ceiling_cmd, ["check-vars", "proj", "staging"])
    assert result.exit_code == 0
    assert "ok" in result.output


def test_check_vars_denied(runner):
    with patch(
        f"{MOD}.check_var_ceiling",
        return_value=GuardResult(allowed=False, reason="ceiling of 2 exceeded"),
    ):
        result = runner.invoke(
            quota_ceiling_cmd, ["check-vars", "proj", "staging", "--incoming", "3"]
        )
    assert result.exit_code == 1
    assert "denied" in result.output
    assert "ceiling of 2" in result.output


def test_check_vars_error(runner):
    with patch(
        f"{MOD}.check_var_ceiling",
        side_effect=QuotaCeilingError("profile not found"),
    ):
        result = runner.invoke(quota_ceiling_cmd, ["check-vars", "proj", "ghost"])
    assert result.exit_code == 1
    assert "error" in result.output


# --- check-quota ---

def test_check_quota_allowed(runner):
    with patch(
        f"{MOD}.check_project_quota", return_value=GuardResult(allowed=True)
    ):
        result = runner.invoke(quota_ceiling_cmd, ["check-quota", "proj"])
    assert result.exit_code == 0
    assert "ok" in result.output


def test_check_quota_denied(runner):
    with patch(
        f"{MOD}.check_project_quota",
        return_value=GuardResult(allowed=False, reason="quota exceeded"),
    ):
        result = runner.invoke(quota_ceiling_cmd, ["check-quota", "proj"])
    assert result.exit_code == 1
    assert "denied" in result.output
    assert "quota exceeded" in result.output
