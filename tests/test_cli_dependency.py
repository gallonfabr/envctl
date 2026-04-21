"""Tests for envctl.cli_dependency."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envctl.cli_dependency import dependency_cmd
from envctl.storage import save_profiles


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    store_file = tmp_path / "profiles.json"
    monkeypatch.setattr("envctl.storage.get_store_path", lambda: store_file)
    store = {
        "proj_a": {"dev": {"vars": {"A": "1"}}, "prod": {"vars": {"A": "2"}}},
        "proj_b": {"dev": {"vars": {"B": "3"}}},
    }
    save_profiles(store)
    yield


def test_add_dependency_success(runner):
    result = runner.invoke(dependency_cmd, ["add", "proj_a", "dev", "proj_b", "dev"])
    assert result.exit_code == 0
    assert "Added" in result.output


def test_add_dependency_missing_profile(runner):
    result = runner.invoke(dependency_cmd, ["add", "proj_a", "ghost", "proj_b", "dev"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_remove_dependency_success(runner):
    runner.invoke(dependency_cmd, ["add", "proj_a", "dev", "proj_b", "dev"])
    result = runner.invoke(dependency_cmd, ["remove", "proj_a", "dev", "proj_b", "dev"])
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_remove_dependency_not_present(runner):
    result = runner.invoke(dependency_cmd, ["remove", "proj_a", "dev", "proj_b", "dev"])
    assert result.exit_code == 1


def test_list_no_dependencies(runner):
    result = runner.invoke(dependency_cmd, ["list", "proj_a", "dev"])
    assert result.exit_code == 0
    assert "No dependencies" in result.output


def test_list_shows_dependency(runner):
    runner.invoke(dependency_cmd, ["add", "proj_a", "dev", "proj_b", "dev"])
    result = runner.invoke(dependency_cmd, ["list", "proj_a", "dev"])
    assert result.exit_code == 0
    assert "proj_b/dev" in result.output


def test_resolve_no_dependencies(runner):
    result = runner.invoke(dependency_cmd, ["resolve", "proj_a", "dev"])
    assert result.exit_code == 0
    assert "No dependencies" in result.output


def test_resolve_shows_order(runner):
    runner.invoke(dependency_cmd, ["add", "proj_a", "dev", "proj_b", "dev"])
    result = runner.invoke(dependency_cmd, ["resolve", "proj_a", "dev"])
    assert result.exit_code == 0
    assert "proj_b/dev" in result.output
