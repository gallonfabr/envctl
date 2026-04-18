"""Integration tests for schedule with real storage."""
import pytest
from pathlib import Path
from datetime import datetime
from envctl.schedule import set_schedule, active_now, list_schedules, remove_schedule


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr("envctl.schedule._get_path", lambda: tmp_path / "schedules.json")


def test_full_lifecycle():
    set_schedule("myapp", "staging", "08:00", "20:00", ["mon", "wed", "fri"])
    entries = list_schedules("myapp")
    assert len(entries) == 1
    assert entries[0]["profile"] == "staging"

    wednesday_noon = datetime(2024, 1, 10, 12, 0)  # Wednesday
    assert active_now("myapp", "staging", at=wednesday_noon) is True

    tuesday_noon = datetime(2024, 1, 9, 12, 0)  # Tuesday
    assert active_now("myapp", "staging", at=tuesday_noon) is False

    remove_schedule("myapp", "staging")
    assert list_schedules("myapp") == []


def test_multiple_projects():
    set_schedule("app1", "dev", "09:00", "17:00", ["mon"])
    set_schedule("app2", "dev", "09:00", "17:00", ["mon"])
    set_schedule("app1", "prod", "00:00", "23:59", ["mon", "tue", "wed", "thu", "fri", "sat", "sun"])

    assert len(list_schedules()) == 3
    assert len(list_schedules("app1")) == 2
    assert len(list_schedules("app2")) == 1


def test_overwrite_schedule():
    set_schedule("p", "dev", "09:00", "12:00", ["mon"])
    set_schedule("p", "dev", "13:00", "18:00", ["tue"])
    entries = list_schedules("p")
    assert len(entries) == 1
    assert entries[0]["start"] == "13:00"
    assert entries[0]["days"] == ["tue"]
