"""Integration tests for the trigger feature (set → list → fire → remove)."""
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
def isolated(tmp_path, monkeypatch):
    store = tmp_path / "store.json"
    monkeypatch.setattr(storage, "get_store_path", lambda: store)
    yield


def test_full_lifecycle():
    add_profile("myapp", "staging", {"DB": "postgres"})
    assert get_triggers("myapp", "staging") == {}

    set_trigger("myapp", "staging", "post_apply", "echo applied")
    set_trigger("myapp", "staging", "pre_delete", "echo deleting")

    triggers = get_triggers("myapp", "staging")
    assert set(triggers.keys()) == {"post_apply", "pre_delete"}

    code = fire_trigger("myapp", "staging", "post_apply")
    assert code == 0

    remove_trigger("myapp", "staging", "post_apply")
    assert "post_apply" not in get_triggers("myapp", "staging")
    assert "pre_delete" in get_triggers("myapp", "staging")


def test_triggers_independent_across_profiles():
    add_profile("myapp", "dev", {"X": "1"})
    add_profile("myapp", "prod", {"X": "2"})

    set_trigger("myapp", "dev", "post_apply", "echo dev")
    assert get_triggers("myapp", "prod") == {}


def test_overwrite_trigger():
    add_profile("myapp", "dev", {"X": "1"})
    set_trigger("myapp", "dev", "post_apply", "echo v1")
    set_trigger("myapp", "dev", "post_apply", "echo v2")
    assert get_triggers("myapp", "dev")["post_apply"] == "echo v2"


def test_remove_nonexistent_trigger_raises():
    add_profile("myapp", "dev", {"X": "1"})
    with pytest.raises(TriggerError):
        remove_trigger("myapp", "dev", "post_apply")


def test_all_valid_events_accepted():
    add_profile("myapp", "dev", {"X": "1"})
    for event in ("pre_apply", "post_apply", "pre_delete", "post_delete"):
        set_trigger("myapp", "dev", event, f"echo {event}")
    assert len(get_triggers("myapp", "dev")) == 4
