"""Tests for envctl.cli_label CLI commands."""
import pytest
from click.testing import CliRunner

from envctl.cli_label import label_cmd
from envctl.storage import save_profiles


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    import envctl.storage as st
    monkeypatch.setattr(st, "get_store_path", lambda: tmp_path / "store.json")
    save_profiles("myproject", {"staging": {"vars": {}}})


def test_set_label_success(runner):
    result = runner.invoke(label_cmd, ["set", "myproject", "staging", "owner", "alice"])
    assert result.exit_code == 0
    assert "owner=alice" in result.output


def test_set_label_missing_profile_exits_1(runner):
    result = runner.invoke(label_cmd, ["set", "myproject", "ghost", "k", "v"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_remove_label_success(runner):
    runner.invoke(label_cmd, ["set", "myproject", "staging", "tier", "gold"])
    result = runner.invoke(label_cmd, ["remove", "myproject", "staging", "tier"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_label_missing_key_exits_1(runner):
    result = runner.invoke(label_cmd, ["remove", "myproject", "staging", "nope"])
    assert result.exit_code == 1


def test_list_labels_text(runner):
    runner.invoke(label_cmd, ["set", "myproject", "staging", "env", "stage"])
    result = runner.invoke(label_cmd, ["list", "myproject", "staging"])
    assert result.exit_code == 0
    assert "env=stage" in result.output


def test_list_labels_empty(runner):
    result = runner.invoke(label_cmd, ["list", "myproject", "staging"])
    assert result.exit_code == 0
    assert "No labels" in result.output


def test_list_labels_json(runner):
    runner.invoke(label_cmd, ["set", "myproject", "staging", "region", "eu"])
    result = runner.invoke(label_cmd, ["list", "--json", "myproject", "staging"])
    assert result.exit_code == 0
    assert '"region"' in result.output
    assert '"eu"' in result.output


def test_find_label_success(runner):
    runner.invoke(label_cmd, ["set", "myproject", "staging", "env", "stage"])
    result = runner.invoke(label_cmd, ["find", "myproject", "env"])
    assert result.exit_code == 0
    assert "staging" in result.output


def test_find_label_no_matches(runner):
    result = runner.invoke(label_cmd, ["find", "myproject", "missing"])
    assert result.exit_code == 0
    assert "No matching" in result.output


def test_clear_labels_success(runner):
    runner.invoke(label_cmd, ["set", "myproject", "staging", "x", "1"])
    result = runner.invoke(label_cmd, ["clear", "myproject", "staging"])
    assert result.exit_code == 0
    assert "cleared" in result.output
