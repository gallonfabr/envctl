"""Tests for envctl.schedule."""
import pytest
from datetime import datetime
from unittest.mock import patch
from envctl.schedule import (
    set_schedule, remove_schedule, get_schedule, list_schedules, active_now, ScheduleError
)


@pytest.fixture(autouse=True)
def reset_schedules(tmp_path, monkeypatch):
    monkeypatch.setattr("envctl.schedule._get_path", lambda: tmp_path / "schedules.json")


def test_set_schedule_persists():
    e = set_schedule("proj", "dev", "09:00", "17:00", ["mon", "tue"])
    assert e["start"] == "09:00"
    assert e["end"] == "17:00"
    assert e["days"] == ["mon", "tue"]


def test_set_schedule_invalid_time():
    with pytest.raises(ScheduleError, match="Invalid time"):
        set_schedule("proj", "dev", "25:00", "17:00", ["mon"])


def test_set_schedule_invalid_day():
    with pytest.raises(ScheduleError, match="Invalid days"):
        set_schedule("proj", "dev", "09:00", "17:00", ["xyz"])


def test_get_schedule_missing_returns_none():
    assert get_schedule("proj", "missing") is None


def test_remove_schedule():
    set_schedule("proj", "dev", "09:00", "17:00", ["mon"])
    remove_schedule("proj", "dev")
    assert get_schedule("proj", "dev") is None


def test_remove_missing_raises():
    with pytest.raises(ScheduleError):
        remove_schedule("proj", "ghost")


def test_list_schedules_all():
    set_schedule("p1", "dev", "08:00", "12:00", ["mon"])
    set_schedule("p2", "prod", "08:00", "12:00", ["fri"])
    assert len(list_schedules()) == 2


def test_list_schedules_filtered():
    set_schedule("p1", "dev", "08:00", "12:00", ["mon"])
    set_schedule("p2", "prod", "08:00", "12:00", ["fri"])
    assert len(list_schedules("p1")) == 1


def test_active_now_within_window():
    set_schedule("proj", "dev", "09:00", "17:00", ["mon", "tue", "wed", "thu", "fri"])
    monday_noon = datetime(2024, 1, 8, 12, 0)  # Monday
    assert active_now("proj", "dev", at=monday_noon) is True


def test_active_now_outside_window():
    set_schedule("proj", "dev", "09:00", "17:00", ["mon"])
    monday_evening = datetime(2024, 1, 8, 20, 0)
    assert active_now("proj", "dev", at=monday_evening) is False


def test_active_now_wrong_day():
    set_schedule("proj", "dev", "09:00", "17:00", ["sat"])
    monday_noon = datetime(2024, 1, 8, 12, 0)
    assert active_now("proj", "dev", at=monday_noon) is False


def test_active_now_no_schedule():
    assert active_now("proj", "missing", at=datetime(2024, 1, 8, 12, 0)) is False
