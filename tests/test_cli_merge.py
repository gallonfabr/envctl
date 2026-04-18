"""Tests for envctl.cli_merge."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch
from envctl.cli_merge import merge_cmd


@pytest.fixture()
def runner():
    return CliRunner()


def test_merge_run_success(runner):
    with patch("envctl.cli_merge.merge_profiles", return_value={"A": "1", "B": "2"}) as mock:
        result = runner.invoke(merge_cmd, ["run", "proj", "base", "other", "dest"])
    assert result.exit_code == 0
    assert "2 variable(s)" in result.output
    mock.assert_called_once_with("proj", "base", "other", "dest", strategy="error", password=None)


def test_merge_run_with_strategy(runner):
    with patch("envctl.cli_merge.merge_profiles", return_value={"A": "1"}):
        result = runner.invoke(
            merge_cmd, ["run", "proj", "base", "other", "dest", "--strategy", "ours"]
        )
    assert result.exit_code == 0


def test_merge_run_conflict_error(runner):
    with patch("envctl.cli_merge.merge_profiles", side_effect=ValueError("Merge conflict on keys: HOST")):
        result = runner.invoke(merge_cmd, ["run", "proj", "base", "other", "dest"])
    assert result.exit_code == 1
    assert "Merge conflict" in result.output


def test_merge_run_with_password(runner):
    with patch("envctl.cli_merge.merge_profiles", return_value={"X": "y"}) as mock:
        result = runner.invoke(
            merge_cmd, ["run", "proj", "base", "other", "dest", "--password", "secret"]
        )
    assert result.exit_code == 0
    _, kwargs = mock.call_args
    assert kwargs["password"] == "secret"
