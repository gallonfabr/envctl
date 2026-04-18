"""Tests for envctl.cli_clone."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch
from envctl.cli_clone import clone_cmd


@pytest.fixture
def runner():
    return CliRunner()


def test_clone_profile_success(runner):
    with patch("envctl.cli_clone.clone_profile", return_value={"K": "v"}) as mock_clone:
        result = runner.invoke(clone_cmd, ["profile", "proj_a", "dev", "proj_b", "dev"])
    assert result.exit_code == 0
    assert "proj_a/dev" in result.output
    assert "proj_b/dev" in result.output


def test_clone_profile_missing_src(runner):
    with patch("envctl.cli_clone.clone_profile", side_effect=KeyError("dev")):
        result = runner.invoke(clone_cmd, ["profile", "proj_a", "dev", "proj_b", "dev"])
    assert result.exit_code == 1


def test_clone_profile_with_password(runner):
    with patch("envctl.cli_clone.clone_profile", return_value={}) as mock_clone:
        result = runner.invoke(clone_cmd, ["profile", "a", "p", "b", "p", "--password", "secret"])
    assert result.exit_code == 0
    mock_clone.assert_called_once_with("a", "p", "b", "p", password="secret")


def test_mirror_success(runner):
    with patch("envctl.cli_clone.list_profiles", return_value=["dev", "prod"]), \
         patch("envctl.cli_clone.mirror_project", return_value=["dev", "prod"]):
        result = runner.invoke(clone_cmd, ["mirror", "src", "dst"])
    assert result.exit_code == 0
    assert "2 profile(s)" in result.output


def test_mirror_no_profiles(runner):
    with patch("envctl.cli_clone.list_profiles", return_value=[]):
        result = runner.invoke(clone_cmd, ["mirror", "src", "dst"])
    assert result.exit_code == 0
    assert "No profiles" in result.output
