"""Tests for envctl.ceiling."""

from __future__ import annotations

import pytest
from unittest.mock import patch

from envctl.ceiling import (
    CeilingError,
    set_ceiling,
    remove_ceiling,
    get_ceiling,
    check_ceiling,
    ceiling_status,
)


_STORE: dict = {}


@pytest.fixture(autouse=True)
def reset_profiles():
    _STORE.clear()
    with (
        patch("envctl.ceiling.load_profiles", side_effect=lambda: dict(_STORE)),
        patch(
            "envctl.ceiling.save_profiles",
            side_effect=lambda d: _STORE.update(d),
        ),
        patch(
            "envctl.ceiling.list_profiles",
            side_effect=lambda proj: list(
                k for k in _STORE.get(proj, {}) if not k.startswith("__")
            ),
        ),
    ):
        yield


def test_set_ceiling_persists():
    set_ceiling("myproject", 5)
    assert get_ceiling("myproject") == 5


def test_set_ceiling_zero_raises():
    with pytest.raises(CeilingError, match="positive integer"):
        set_ceiling("myproject", 0)


def test_set_ceiling_negative_raises():
    with pytest.raises(CeilingError, match="positive integer"):
        set_ceiling("myproject", -3)


def test_get_ceiling_unset_returns_none():
    assert get_ceiling("ghost") is None


def test_remove_ceiling_clears_limit():
    set_ceiling("myproject", 3)
    remove_ceiling("myproject")
    assert get_ceiling("myproject") is None


def test_remove_ceiling_nonexistent_is_noop():
    remove_ceiling("nonexistent")  # should not raise


def test_check_ceiling_no_ceiling_passes():
    check_ceiling("myproject")  # no ceiling set — should not raise


def test_check_ceiling_under_limit_passes():
    _STORE["myproject"] = {"dev": {}, "prod": {}}
    set_ceiling("myproject", 5)
    check_ceiling("myproject")  # 2 profiles, limit 5 — should not raise


def test_check_ceiling_at_limit_raises():
    _STORE["myproject"] = {"dev": {}, "prod": {}}
    set_ceiling("myproject", 2)
    with pytest.raises(CeilingError, match="ceiling of 2"):
        check_ceiling("myproject")


def test_ceiling_status_no_ceiling():
    _STORE["myproject"] = {"dev": {}}
    status = ceiling_status("myproject")
    assert status["limit"] is None
    assert status["used"] == 1
    assert status["available"] is None


def test_ceiling_status_with_ceiling():
    _STORE["myproject"] = {"dev": {}, "staging": {}}
    set_ceiling("myproject", 10)
    status = ceiling_status("myproject")
    assert status["limit"] == 10
    assert status["used"] == 2
    assert status["available"] == 8
