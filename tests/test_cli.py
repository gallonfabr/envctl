import pytest
from click.testing import CliRunner
from unittest.mock import patch
from envctl.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@patch("envctl.cli.add_profile")
def test_add_plain_profile(mock_add, runner):
    result = runner.invoke(cli, ["add", "myapp", "dev", "-v", "KEY=val"])
    assert result.exit_code == 0
    assert "added" in result.output
    mock_add.assert_called_once_with("myapp", "dev", {"KEY": "val"}, password=None)


@patch("envctl.cli.add_profile")
def test_add_invalid_var_format(mock_add, runner):
    result = runner.invoke(cli, ["add", "myapp", "dev", "-v", "BADVAR"])
    assert result.exit_code != 0


@patch("envctl.cli.get_profile", return_value={"FOO": "bar", "BAZ": "qux"})
def test_get_profile(mock_get, runner):
    result = runner.invoke(cli, ["get", "myapp", "dev"])
    assert result.exit_code == 0
    assert "FOO=bar" in result.output
    assert "BAZ=qux" in result.output


@patch("envctl.cli.get_profile", return_value=None)
def test_get_missing_profile(mock_get, runner):
    result = runner.invoke(cli, ["get", "myapp", "missing"])
    assert "not found" in result.output


@patch("envctl.cli.apply_profile", return_value=["export FOO=bar"])
def test_apply_profile(mock_apply, runner):
    result = runner.invoke(cli, ["apply", "myapp", "dev"])
    assert result.exit_code == 0
    assert "export FOO=bar" in result.output


@patch("envctl.cli.apply_profile", return_value=None)
def test_apply_missing_profile(mock_apply, runner):
    result = runner.invoke(cli, ["apply", "myapp", "ghost"])
    assert "not found" in result.output


@patch("envctl.cli.delete_profile", return_value=True)
def test_delete_profile(mock_del, runner):
    result = runner.invoke(cli, ["delete", "myapp", "dev"], input="y\n")
 0
    assert "deleted" in result.output


@patch("envctl.cli.delete_profile", return_value=False)
def test_delete_missing_profile(mock_del, runner):
    result = runner.invoke(cli, ["delete", "myapp", "ghost"], input="y\n")
    assert "not found" in result.output


@patch("envctl.cli.list_projects", return_value=["proj1", "proj2"])
def test_list_projects(mock_list, runner):
    result = runner.invoke(cli, ["list"])
    assert "proj1" in result.output
    assert "proj2" in result.output


@patch("envctl.cli.list_profiles", return_value=["dev", "prod"])
def test_list_profiles(mock_list, runner):
    result = runner.invoke(cli, ["list", "myapp"])
    assert "dev" in result.output
    assert "prod" in result.output
