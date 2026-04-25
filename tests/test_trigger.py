"""Unit tests for envctl.trigger."""
import pytest

from envctl.trigger import (
    TriggerError,
    fire_trigger,
    get_triggers,
    remove_trigger,
    set_trigger,
)
from envctl.profile import add_profile
from envctl import storage


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    store = tmp_path / "store.json"
    monkeypatch.setattr(storage, "get_store_path", lambda: store)
    add_profile("proj", "dev", {"KEY": "val"})
    yield


def test_set_trigger_persists():
    set_trigger("proj", "dev", "post_apply", "echo done")
    triggers = get_triggers("proj", "dev")
    assert triggers["post_apply"] == "echo done"


def test_set_trigger_invalid_event_raises():
    with pytest.raises(TriggerError, match="Invalid event"):
        set_trigger("proj", "dev", "on_magic", "echo hi")


def test_set_trigger_empty_command_raises():
    with pytest.raises(TriggerError, match="empty"):
        set_trigger("proj", "dev", "post_apply", "   ")


def test_set_trigger_missing_profile_raises():
    with pytest.raises(TriggerError, match="not found"):
        set_trigger("proj", "ghost", "post_apply", "echo hi")


def test_remove_trigger_success():
    set_trigger("proj", "dev", "pre_apply", "echo pre")
    remove_trigger("proj", "dev", "pre_apply")
    assert "pre_apply" not in get_triggers("proj", "dev")


def test_remove_trigger_missing_raises():
    with pytest.raises(TriggerError, match="No trigger set"):
        remove_trigger("proj", "dev", "post_delete")


def test_get_triggers_empty_by_default():
    assert get_triggers("proj", "dev") == {}


def test_multiple_triggers_independent():
    set_trigger("proj", "dev", "post_apply", "echo a")
    set_trigger("proj", "dev", "pre_apply", "echo b")
    triggers = get_triggers("proj", "dev")
    assert len(triggers) == 2
    assert triggers["post_apply"] == "echo a"
    assert triggers["pre_apply"] == "echo b"


def test_fire_trigger_no_trigger_returns_none():
    result = fire_trigger("proj", "dev", "post_apply")
    assert result is None


def test_fire_trigger_runs_command():
    set_trigger("proj", "dev", "post_apply", "true")
    code = fire_trigger("proj", "dev", "post_apply")
    assert code == 0


def test_fire_trigger_failing_command_returns_nonzero():
    set_trigger("proj", "dev", "post_apply", "false")
    code = fire_trigger("proj", "dev", "post_apply")
    assert code != 0


def test_set_trigger_overwrites_existing():
    set_trigger("proj", "dev", "post_apply", "echo first")
    set_trigger("proj", "dev", "post_apply", "echo second")
    assert get_triggers("proj", "dev")["post_apply"] == "echo second"
