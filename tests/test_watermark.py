"""Unit tests for envctl.watermark."""

from __future__ import annotations

import pytest

from envctl.watermark import (
    WatermarkError,
    clear_watermark,
    get_watermark,
    set_watermark,
    verify_watermark,
)


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    """Redirect storage to a temp directory and seed a test profile."""
    store = tmp_path / "profiles.json"
    monkeypatch.setenv("ENVCTL_STORE", str(store))

    from envctl.storage import save_profiles
    save_profiles({"myproject": {"dev": {"vars": {"KEY": "val"}}}})
    yield


def test_set_watermark_persists():
    wm = set_watermark("myproject", "dev", "alice")
    assert wm["author"] == "alice"
    assert len(wm["checksum"]) == 16
    assert wm["timestamp"] > 0


def test_set_watermark_with_note():
    wm = set_watermark("myproject", "dev", "bob", note="initial release")
    assert wm["note"] == "initial release"


def test_set_watermark_empty_author_raises():
    with pytest.raises(WatermarkError, match="Author must not be empty"):
        set_watermark("myproject", "dev", "   ")


def test_set_watermark_missing_profile_raises():
    with pytest.raises(WatermarkError, match="not found"):
        set_watermark("myproject", "ghost", "alice")


def test_get_watermark_returns_none_when_not_set():
    result = get_watermark("myproject", "dev")
    assert result is None


def test_get_watermark_returns_data_after_set():
    set_watermark("myproject", "dev", "carol")
    wm = get_watermark("myproject", "dev")
    assert wm is not None
    assert wm["author"] == "carol"


def test_verify_watermark_valid():
    set_watermark("myproject", "dev", "dave")
    assert verify_watermark("myproject", "dev") is True


def test_verify_watermark_tampered():
    set_watermark("myproject", "dev", "eve")
    from envctl.storage import load_profiles, save_profiles
    profiles = load_profiles()
    profiles["myproject"]["dev"]["watermark"]["checksum"] = "000000000000dead"
    save_profiles(profiles)
    assert verify_watermark("myproject", "dev") is False


def test_verify_watermark_missing_raises():
    with pytest.raises(WatermarkError, match="no watermark"):
        verify_watermark("myproject", "dev")


def test_clear_watermark_removes_entry():
    set_watermark("myproject", "dev", "frank")
    clear_watermark("myproject", "dev")
    assert get_watermark("myproject", "dev") is None


def test_clear_watermark_not_set_raises():
    with pytest.raises(WatermarkError, match="no watermark"):
        clear_watermark("myproject", "dev")
