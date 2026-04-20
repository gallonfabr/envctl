"""Tests for envctl.priority module."""

import pytest
from unittest.mock import patch, MagicMock

from envctl.priority import (
    set_priority,
    get_priority,
    clear_priority,
    ranked_profiles,
    PriorityError,
)

BASE_STORE = {
    "myproject": {
        "dev": {"vars": {"A": "1"}},
        "staging": {"vars": {"A": "2"}},
        "prod": {"vars": {"A": "3"}},
    }
}


def _store_copy():
    import copy
    return copy.deepcopy(BASE_STORE)


@pytest.fixture(autouse=True)
def patch_storage(monkeypatch):
    store = _store_copy()
    monkeypatch.setattr("envctl.priority.load_profiles", lambda: store)
    monkeypatch.setattr("envctl.priority.save_profiles", lambda s: store.update(s))
    return store


def test_set_priority_persists(patch_storage):
    set_priority("myproject", "dev", 5)
    assert patch_storage["myproject"]["dev"]["_priority"] == 5


def test_set_priority_negative_raises():
    with pytest.raises(PriorityError, match="non-negative"):
        set_priority("myproject", "dev", -1)


def test_set_priority_missing_profile_raises():
    with pytest.raises(PriorityError, match="not found"):
        set_priority("myproject", "ghost", 1)


def test_set_priority_missing_project_raises():
    with pytest.raises(PriorityError, match="not found"):
        set_priority("noproject", "dev", 1)


def test_get_priority_default_zero():
    assert get_priority("myproject", "dev") == 0


def test_get_priority_after_set(patch_storage):
    patch_storage["myproject"]["staging"]["_priority"] = 3
    assert get_priority("myproject", "staging") == 3


def test_get_priority_missing_profile_raises():
    with pytest.raises(PriorityError, match="not found"):
        get_priority("myproject", "ghost")


def test_clear_priority_removes_key(patch_storage):
    patch_storage["myproject"]["dev"]["_priority"] = 10
    clear_priority("myproject", "dev")
    assert "_priority" not in patch_storage["myproject"]["dev"]


def test_clear_priority_missing_profile_raises():
    with pytest.raises(PriorityError, match="not found"):
        clear_priority("myproject", "ghost")


def test_ranked_profiles_sorted(patch_storage):
    patch_storage["myproject"]["prod"]["_priority"] = 1
    patch_storage["myproject"]["staging"]["_priority"] = 2
    patch_storage["myproject"]["dev"]["_priority"] = 10
    ranked = ranked_profiles("myproject")
    assert ranked.index("prod") < ranked.index("staging") < ranked.index("dev")


def test_ranked_profiles_missing_project_raises():
    with pytest.raises(PriorityError, match="not found"):
        ranked_profiles("noproject")


def test_ranked_profiles_defaults_to_zero(patch_storage):
    # All profiles have no explicit priority, order is stable by sort
    ranked = ranked_profiles("myproject")
    assert set(ranked) == {"dev", "staging", "prod"}
