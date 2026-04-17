"""Tests for CLI compare commands."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch
from envctl.cli_compare import compare_cmd


@pytest.fixture()
def runner():
    return CliRunner()


DIFF_RESULT = {
    "added": {"LOG_LEVEL": "warn"},
    "removed": {"DEBUG": "true"},
    "changed": {"DB_HOST": ("localhost", "prod.db")},
}

EMPTY_DIFF = {"added": {}, "removed": {}, "changed": {}}


def test_compare_run_shows_diff(runner):
    with patch("envctl.cli_compare.compare_profiles", return_value=DIFF_RESULT), \
         patch("envctl.cli_compare.format_diff", return_value="some diff output"):
        result = runner.invoke(compare_cmd, ["run", "proj", "dev", "proj", "prod"])
    assert result.exit_code == 0
    assert "some diff output" in result.output


def test_compare_run_identical(runner):
    with patch("envctl.cli_compare.compare_profiles", return_value=EMPTY_DIFF), \
         patch("envctl.cli_compare.format_diff", return_value=""):
        result = runner.invoke(compare_cmd, ["run", "proj", "dev", "proj", "dev"])
    assert result.exit_code == 0
    assert "identical" in result.output


def test_compare_run_summary_flag(runner):
    with patch("envctl.cli_compare.compare_profiles", return_value=DIFF_RESULT), \
         patch("envctl.cli_compare.compare_summary", return_value="+1 added  -1 removed  ~1 changed"):
        result = runner.invoke(
            compare_cmd, ["run", "proj", "dev", "proj", "prod", "--summary"]
        )
    assert result.exit_code == 0
    assert "+1 added" in result.output


def test_compare_run_missing_profile(runner):
    with patch("envctl.cli_compare.compare_profiles", side_effect=KeyError("not found")):
        result = runner.invoke(compare_cmd, ["run", "proj", "dev", "proj", "prod"])
    assert result.exit_code != 0
    assert "Error" in result.output
