"""Tests for CLI template commands."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch
from envctl.cli_template import template_cmd


@pytest.fixture
def runner():
    return CliRunner()


def test_render_success(runner):
    fake_vars = {"HOST": "localhost", "PORT": "3306"}
    with patch("envctl.cli_template.render_profile_template", return_value="localhost:3306"):
        result = runner.invoke(template_cmd, ["render", "proj", "dev", "{{HOST}}:{{PORT}}"])
    assert result.exit_code == 0
    assert "localhost:3306" in result.output


def test_render_missing_var(runner):
    with patch(
        "envctl.cli_template.render_profile_template",
        side_effect=KeyError("PORT"),
    ):
        result = runner.invoke(template_cmd, ["render", "proj", "dev", "{{PORT}}"])
    assert result.exit_code == 1
    assert "missing variable" in result.output


def test_render_unknown_error(runner):
    with patch(
        "envctl.cli_template.render_profile_template",
        side_effect=ValueError("profile not found"),
    ):
        result = runner.invoke(template_cmd, ["render", "proj", "dev", "{{X}}"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_vars_command(runner):
    result = runner.invoke(template_cmd, ["vars", "{{A}} and {{B}} and {{A}}"])
    assert result.exit_code == 0
    assert "A" in result.output
    assert "B" in result.output


def test_vars_command_empty(runner):
    result = runner.invoke(template_cmd, ["vars", "no placeholders"])
    assert result.exit_code == 0
    assert "No variables found" in result.output
