"""Tests for envctl.diff module."""

import pytest
from unittest.mock import patch
from envctl.diff import diff_profiles, format_diff


PROFILE_DEV = {"DB_HOST": "localhost", "DB_PORT": "5432", "DEBUG": "true"}
PROFILE_PROD = {"DB_HOST": "prod.db.example.com", "DB_PORT": "5432", "LOG_LEVEL": "warn"}


def _mock_get_profile(project, profile, password=None):
    if profile == "dev":
        return PROFILE_DEV
    if profile == "prod":
        return PROFILE_PROD
    return None


@pytest.fixture(autouse=True)
def mock_get_profile():
    with patch("envctl.diff.get_profile", side_effect=_mock_get_profile):
        yield


def test_diff_added_keys():
    result = diff_profiles("myapp", "dev", "prod")
    assert "LOG_LEVEL" in result["added"]
    assert result["added"]["LOG_LEVEL"] == "warn"


def test_diff_removed_keys():
    result = diff_profiles("myapp", "dev", "prod")
    assert "DEBUG" in result["removed"]
    assert result["removed"]["DEBUG"] == "true"


def test_diff_changed_keys():
    result = diff_profiles("myapp", "dev", "prod")
    assert "DB_HOST" in result["changed"]
    assert result["changed"]["DB_HOST"]["from"] == "localhost"
    assert result["changed"]["DB_HOST"]["to"] == "prod.db.example.com"


def test_diff_unchanged_keys():
    result = diff_profiles("myapp", "dev", "prod")
    assert "DB_PORT" in result["unchanged"]
    assert result["unchanged"]["DB_PORT"] == "5432"


def test_diff_missing_profile_raises():
    with pytest.raises(ValueError, match="Profile 'missing'"):
        diff_profiles("myapp", "missing", "prod")


def test_format_diff_shows_changes():
    result = diff_profiles("myapp", "dev", "prod")
    output = format_diff(result)
    assert "+ LOG_LEVEL=warn" in output
    assert "- DEBUG=true" in output
    assert "~ DB_HOST: localhost -> prod.db.example.com" in output
    assert "DB_PORT" not in output


def test_format_diff_show_unchanged():
    result = diff_profiles("myapp", "dev", "prod")
    output = format_diff(result, show_unchanged=True)
    assert "DB_PORT=5432" in output


def test_format_diff_no_differences():
    with patch("envctl.diff.get_profile", return_value={"KEY": "val"}):
        result = diff_profiles("myapp", "a", "b")
        output = format_diff(result)
        assert output == "No differences found."
