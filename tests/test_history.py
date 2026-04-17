"""Tests for envctl.history."""

import pytest
from unittest.mock import patch
from pathlib import Path
import tempfile

from envctl import history as hist


@pytest.fixture(autouse=True)
def isolated_history(tmp_path):
    fake_store = tmp_path / "profiles.json"
    with patch("envctl.history.get_store_path", return_value=fake_store):
        yield tmp_path


def test_get_history_empty():
    assert hist.get_history() == []


def test_record_apply_returns_entry():
    entry = hist.record_apply("myapp", "dev")
    assert entry["project"] == "myapp"
    assert entry["profile"] == "dev"
    assert "applied_at" in entry


def test_record_apply_persists():
    hist.record_apply("myapp", "dev")
    hist.record_apply("myapp", "prod")
    entries = hist.get_history()
    assert len(entries) == 2


def test_get_history_returns_most_recent_first():
    hist.record_apply("myapp", "dev")
    hist.record_apply("myapp", "prod")
    entries = hist.get_history()
    assert entries[0]["profile"] == "prod"
    assert entries[1]["profile"] == "dev"


def test_get_history_filter_by_project():
    hist.record_apply("myapp", "dev")
    hist.record_apply("otherapp", "staging")
    entries = hist.get_history(project="myapp")
    assert len(entries) == 1
    assert entries[0]["project"] == "myapp"


def test_get_history_limit():
    for i in range(5):
        hist.record_apply("myapp", f"profile{i}")
    entries = hist.get_history(limit=3)
    assert len(entries) == 3


def test_clear_history_all():
    hist.record_apply("myapp", "dev")
    hist.record_apply("otherapp", "prod")
    removed = hist.clear_history()
    assert removed == 2
    assert hist.get_history() == []


def test_clear_history_by_project():
    hist.record_apply("myapp", "dev")
    hist.record_apply("otherapp", "prod")
    removed = hist.clear_history(project="myapp")
    assert removed == 1
    remaining = hist.get_history()
    assert len(remaining) == 1
    assert remaining[0]["project"] == "otherapp"
