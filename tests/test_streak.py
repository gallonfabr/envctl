"""Tests for envctl.streak."""
from __future__ import annotations

import json
import pytest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from envctl import streak as streak_mod
from envctl.streak import StreakError, get_streak, record_apply, reset_streak


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    store = tmp_path / "store.json"
    store.write_text("{}")
    monkeypatch.setattr(streak_mod, "_get_path", lambda: tmp_path / "streaks.json")
    yield tmp_path


TODAY = date(2024, 6, 1)
YESTERDAY = TODAY - timedelta(days=1)
TWO_DAYS_AGO = TODAY - timedelta(days=2)


def test_get_streak_no_data():
    info = get_streak("proj", "dev")
    assert info.current == 0
    assert info.longest == 0
    assert info.last_applied is None


def test_record_apply_first_time():
    info = record_apply("proj", "dev", today=TODAY)
    assert info.current == 1
    assert info.longest == 1
    assert info.last_applied == TODAY.isoformat()


def test_record_apply_consecutive_days():
    record_apply("proj", "dev", today=YESTERDAY)
    info = record_apply("proj", "dev", today=TODAY)
    assert info.current == 2
    assert info.longest == 2


def test_record_apply_same_day_no_increment():
    record_apply("proj", "dev", today=TODAY)
    info = record_apply("proj", "dev", today=TODAY)
    assert info.current == 1


def test_record_apply_gap_resets_streak():
    record_apply("proj", "dev", today=TWO_DAYS_AGO)
    info = record_apply("proj", "dev", today=TODAY)
    assert info.current == 1


def test_longest_streak_preserved_after_reset():
    record_apply("proj", "dev", today=TWO_DAYS_AGO)
    record_apply("proj", "dev", today=YESTERDAY)
    # gap breaks streak
    info = record_apply("proj", "dev", today=TODAY)
    assert info.longest == 2
    assert info.current == 1


def test_record_apply_empty_project_raises():
    with pytest.raises(StreakError):
        record_apply("", "dev", today=TODAY)


def test_record_apply_empty_profile_raises():
    with pytest.raises(StreakError):
        record_apply("proj", "", today=TODAY)


def test_reset_streak_removes_data():
    record_apply("proj", "dev", today=TODAY)
    reset_streak("proj", "dev")
    info = get_streak("proj", "dev")
    assert info.current == 0


def test_reset_streak_missing_raises():
    with pytest.raises(StreakError, match="No streak data"):
        reset_streak("proj", "ghost")


def test_multiple_profiles_independent():
    record_apply("proj", "dev", today=YESTERDAY)
    record_apply("proj", "dev", today=TODAY)
    record_apply("proj", "prod", today=TODAY)
    dev = get_streak("proj", "dev")
    prod = get_streak("proj", "prod")
    assert dev.current == 2
    assert prod.current == 1
