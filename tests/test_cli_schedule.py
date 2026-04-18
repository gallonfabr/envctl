"""Tests for CLI schedule commands."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from envctl.cli_schedule import schedule_cmd
from envctl.schedule import ScheduleError


@pytest.fixture
def runner():
    return CliRunner()


def test_set_schedule_success(runner):
    with patch("envctl.cli_schedule.set_schedule", return_value={
        "project": "p", "profile": "dev", "start": "09:00", "end": "17:00", "days": ["mon"]
    }) as m:
        result = runner.invoke(schedule_cmd, ["set", "p", "dev", "--start", "09:00", "--end", "17:00", "--days", "mon"])
        assert result.exit_code == 0
        assert "Schedule set" in result.output
        m.assert_called_once_with("p", "dev", "09:00", "17:00", ["mon"])


def test_set_schedule_error(runner):
    with patch("envctl.cli_schedule.set_schedule", side_effect=ScheduleError("bad")):
        result = runner.invoke(schedule_cmd, ["set", "p", "dev", "--start", "bad", "--end", "17:00", "--days", "mon"])
        assert result.exit_code == 1
        assert "Error" in result.output


def test_remove_schedule_success(runner):
    with patch("envctl.cli_schedule.remove_schedule") as m:
        result = runner.invoke(schedule_cmd, ["remove", "p", "dev"])
        assert result.exit_code == 0
        assert "removed" in result.output


def test_remove_schedule_missing(runner):
    with patch("envctl.cli_schedule.remove_schedule", side_effect=ScheduleError("not found")):
        result = runner.invoke(schedule_cmd, ["remove", "p", "dev"])
        assert result.exit_code == 1


def test_list_schedules_empty(runner):
    with patch("envctl.cli_schedule.list_schedules", return_value=[]):
        result = runner.invoke(schedule_cmd, ["list"])
        assert "No schedules" in result.output


def test_list_schedules_entries(runner):
    entries = [{"project": "p", "profile": "dev", "start": "09:00", "end": "17:00", "days": ["mon"]}]
    with patch("envctl.cli_schedule.list_schedules", return_value=entries):
        result = runner.invoke(schedule_cmd, ["list"])
        assert "p/dev" in result.output


def test_check_active(runner):
    with patch("envctl.cli_schedule.active_now", return_value=True):
        result = runner.invoke(schedule_cmd, ["check", "p", "dev"])
        assert "ACTIVE" in result.output


def test_check_inactive(runner):
    with patch("envctl.cli_schedule.active_now", return_value=False):
        result = runner.invoke(schedule_cmd, ["check", "p", "dev"])
        assert "NOT active" in result.output
