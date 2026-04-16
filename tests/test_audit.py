"""Tests for audit logging."""

import pytest
from pathlib import Path
from unittest.mock import patch

from envctl.audit import log_event, read_events, clear_audit_log, get_audit_path


@pytest.fixture(autouse=True)
def isolated_audit(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCTL_HOME", str(tmp_path))
    yield
    clear_audit_log()


def test_log_and_read_event():
    log_event("get", "myapp", "dev")
    events = read_events()
    assert len(events) == 1
    assert events[0]["action"] == "get"
    assert events[0]["project"] == "myapp"
    assert events[0]["profile"] == "dev"
    assert "timestamp" in events[0]


def test_log_multiple_events():
    log_event("add", "myapp", "dev")
    log_event("get", "myapp", "prod")
    log_event("delete", "other", "staging")
    events = read_events()
    assert len(events) == 3


def test_filter_by_project():
    log_event("add", "myapp", "dev")
    log_event("get", "other", "prod")
    events = read_events(project="myapp")
    assert len(events) == 1
    assert events[0]["project"] == "myapp"


def test_limit():
    for i in range(10):
        log_event("get", "myapp", f"profile{i}")
    events = read_events(limit=5)
    assert len(events) == 5
    assert events[-1]["profile"] == "profile9"


def test_read_empty_log():
    events = read_events()
    assert events == []


def test_log_with_extra():
    log_event("apply", "myapp", "dev", extra={"encrypted": True})
    events = read_events()
    assert events[0]["encrypted"] is True


def test_clear_audit_log():
    log_event("get", "myapp", "dev")
    clear_audit_log()
    assert not get_audit_path().exists()
