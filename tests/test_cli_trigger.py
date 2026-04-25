"""CLI tests for envctl.cli_trigger."""
import pytest
from click.testing import CliRunner

from envctl.cli_trigger import trigger_cmd
from envctl.profile import add_profile
from envctl import storage


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    store = tmp_path / "store.json"
    monkeypatch.setattr(storage, "get_store_path", lambda: store)
    add_profile("proj", "dev", {"K": "v"})
    yield


def test_set_trigger_success(runner):
    result = runner.invoke(trigger_cmd, ["set", "proj", "dev", "post_apply", "echo hi"])
    assert result.exit_code == 0
    assert "Trigger set" in result.output


def test_set_trigger_invalid_event_exits_1(runner):
    result = runner.invoke(trigger_cmd, ["set", "proj", "dev", "bad_event", "echo hi"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_set_trigger_missing_profile_exits_1(runner):
    result = runner.invoke(trigger_cmd, ["set", "proj", "ghost", "post_apply", "echo"])
    assert result.exit_code == 1


def test_remove_trigger_success(runner):
    runner.invoke(trigger_cmd, ["set", "proj", "dev", "pre_apply", "echo pre"])
    result = runner.invoke(trigger_cmd, ["remove", "proj", "dev", "pre_apply"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_trigger_missing_exits_1(runner):
    result = runner.invoke(trigger_cmd, ["remove", "proj", "dev", "post_delete"])
    assert result.exit_code == 1


def test_list_triggers_empty(runner):
    result = runner.invoke(trigger_cmd, ["list", "proj", "dev"])
    assert result.exit_code == 0
    assert "No triggers" in result.output


def test_list_triggers_shows_entries(runner):
    runner.invoke(trigger_cmd, ["set", "proj", "dev", "post_apply", "echo done"])
    result = runner.invoke(trigger_cmd, ["list", "proj", "dev"])
    assert "post_apply" in result.output
    assert "echo done" in result.output


def test_fire_no_trigger(runner):
    result = runner.invoke(trigger_cmd, ["fire", "proj", "dev", "post_apply"])
    assert result.exit_code == 0
    assert "No trigger configured" in result.output


def test_fire_successful_trigger(runner):
    runner.invoke(trigger_cmd, ["set", "proj", "dev", "post_apply", "true"])
    result = runner.invoke(trigger_cmd, ["fire", "proj", "dev", "post_apply"])
    assert result.exit_code == 0
    assert "successfully" in result.output
