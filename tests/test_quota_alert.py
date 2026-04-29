"""Tests for envctl.quota_alert."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from envctl.quota_alert import check_alert, check_all_alerts, AlertStatus, QuotaAlertError
from envctl.cli_quota_alert import quota_alert_cmd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patch(quota, profiles):
    """Return a context manager that patches quota + list_profiles."""
    return patch.multiple(
        "envctl.quota_alert",
        get_quota=MagicMock(return_value=quota),
        list_profiles=MagicMock(return_value=profiles),
        load_profiles=MagicMock(return_value={p: {} for p in {"proj"}}),
    )


# ---------------------------------------------------------------------------
# Unit tests — check_alert
# ---------------------------------------------------------------------------

def test_check_alert_no_quota_returns_none():
    with patch("envctl.quota_alert.get_quota", return_value=None):
        result = check_alert("myproject")
    assert result is None


def test_check_alert_below_threshold_not_triggered():
    with patch("envctl.quota_alert.get_quota", return_value=10), \
         patch("envctl.quota_alert.list_profiles", return_value=["a", "b"]):
        status = check_alert("proj", threshold=0.8)
    assert status is not None
    assert not status.triggered
    assert status.pct_used == pytest.approx(0.2)


def test_check_alert_at_threshold_triggers():
    with patch("envctl.quota_alert.get_quota", return_value=10), \
         patch("envctl.quota_alert.list_profiles", return_value=list(range(8))):
        status = check_alert("proj", threshold=0.8)
    assert status.triggered
    assert status.pct_used == pytest.approx(0.8)


def test_check_alert_above_threshold_triggers():
    with patch("envctl.quota_alert.get_quota", return_value=5), \
         patch("envctl.quota_alert.list_profiles", return_value=list(range(5))):
        status = check_alert("proj", threshold=0.8)
    assert status.triggered


def test_check_alert_invalid_threshold_raises():
    with pytest.raises(QuotaAlertError):
        check_alert("proj", threshold=0.0)

    with pytest.raises(QuotaAlertError):
        check_alert("proj", threshold=1.5)


def test_alert_status_message_ok():
    s = AlertStatus(project="p", quota=10, current=3, threshold=0.8,
                    triggered=False, pct_used=0.3)
    assert "[OK]" in s.message
    assert "3/10" in s.message


def test_alert_status_message_warn():
    s = AlertStatus(project="p", quota=10, current=9, threshold=0.8,
                    triggered=True, pct_used=0.9)
    assert "[WARN]" in s.message


# ---------------------------------------------------------------------------
# Unit tests — check_all_alerts
# ---------------------------------------------------------------------------

def test_check_all_alerts_skips_projects_without_quota():
    with patch("envctl.quota_alert.load_profiles", return_value={"a": {}, "b": {}}), \
         patch("envctl.quota_alert.get_quota", return_value=None), \
         patch("envctl.quota_alert.list_profiles", return_value=[]):
        results = check_all_alerts()
    assert results == []


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    return Runner()


class Runner:
    def __init__(self):
        self._r = CliRunner()

    def invoke(self, *args, **kwargs):
        return self._r.invoke(quota_alert_cmd, *args, **kwargs)


def test_cli_check_no_quota(runner):
    with patch("envctl.quota_alert.get_quota", return_value=None):
        result = runner.invoke(["check", "myproject"])
    assert result.exit_code == 0
    assert "No quota" in result.output


def test_cli_check_triggered_exits_1(runner):
    with patch("envctl.quota_alert.get_quota", return_value=5), \
         patch("envctl.quota_alert.list_profiles", return_value=list(range(5))):
        result = runner.invoke(["check", "myproject", "--threshold", "0.8"])
    assert result.exit_code == 1
    assert "WARN" in result.output


def test_cli_check_all_no_projects(runner):
    with patch("envctl.quota_alert.load_profiles", return_value={}), \
         patch("envctl.quota_alert.get_quota", return_value=None):
        result = runner.invoke(["check-all"])
    assert result.exit_code == 0
    assert "No quota-configured" in result.output
