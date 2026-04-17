"""Tests for CLI tag commands."""

import pytest
from click.testing import CliRunner
from envctl.cli_tags import tags_cmd
from envctl.storage import save_profiles


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    store = tmp_path / "store.json"
    monkeypatch.setattr("envctl.storage.get_store_path", lambda: store)
    save_profiles({"proj": {"dev": {"vars": {}, "tags": []}}})
    yield


def test_add_tag_success(runner):
    result = runner.invoke(tags_cmd, ["add", "proj", "dev", "mytag"])
    assert result.exit_code == 0
    assert "mytag" in result.output


def test_add_tag_missing_profile(runner):
    result = runner.invoke(tags_cmd, ["add", "proj", "ghost", "x"])
    assert result.exit_code == 1


def test_remove_tag_success(runner):
    runner.invoke(tags_cmd, ["add", "proj", "dev", "ci"])
    result = runner.invoke(tags_cmd, ["remove", "proj", "dev", "ci"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_tag_not_found(runner):
    result = runner.invoke(tags_cmd, ["remove", "proj", "dev", "nope"])
    assert result.exit_code == 1


def test_list_tags_empty(runner):
    result = runner.invoke(tags_cmd, ["list", "proj", "dev"])
    assert result.exit_code == 0
    assert "No tags" in result.output


def test_list_tags_with_values(runner):
    runner.invoke(tags_cmd, ["add", "proj", "dev", "alpha"])
    result = runner.invoke(tags_cmd, ["list", "proj", "dev"])
    assert "alpha" in result.output


def test_find_tag(runner):
    runner.invoke(tags_cmd, ["add", "proj", "dev", "shared"])
    result = runner.invoke(tags_cmd, ["find", "shared"])
    assert "proj/dev" in result.output


def test_find_tag_no_match(runner):
    result = runner.invoke(tags_cmd, ["find", "unknown"])
    assert "No profiles found" in result.output
