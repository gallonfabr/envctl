"""Integration tests: watermark full lifecycle through storage."""

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
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCTL_STORE", str(tmp_path / "profiles.json"))
    from envctl.storage import save_profiles
    save_profiles({
        "alpha": {
            "prod": {"vars": {"ENV": "production"}},
            "dev": {"vars": {"ENV": "development"}},
        }
    })
    yield


def test_full_lifecycle():
    # set
    wm = set_watermark("alpha", "prod", "ops-team", note="deployed")
    assert wm["author"] == "ops-team"

    # verify
    assert verify_watermark("alpha", "prod") is True

    # get
    fetched = get_watermark("alpha", "prod")
    assert fetched["note"] == "deployed"

    # clear
    clear_watermark("alpha", "prod")
    assert get_watermark("alpha", "prod") is None


def test_independent_profiles():
    set_watermark("alpha", "prod", "alice")
    # dev profile has no watermark
    assert get_watermark("alpha", "dev") is None
    # prod watermark unaffected
    assert get_watermark("alpha", "prod")["author"] == "alice"


def test_overwrite_watermark():
    set_watermark("alpha", "prod", "alice")
    wm2 = set_watermark("alpha", "prod", "bob", note="updated")
    assert wm2["author"] == "bob"
    assert verify_watermark("alpha", "prod") is True


def test_missing_project_raises():
    with pytest.raises(WatermarkError, match="not found"):
        set_watermark("no-such-project", "prod", "alice")
