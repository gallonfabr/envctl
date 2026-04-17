"""Tests for envctl.search and cli_search."""

import pytest
from unittest.mock import patch
from click.testing import CliRunner

from envctl.cli_search import search_cmd


PROFILES = {
    ("proj1", "dev"): {"DB_HOST": "localhost", "DB_PORT": "5432"},
    ("proj1", "prod"): {"DB_HOST": "prod.db", "API_KEY": "secret"},
    ("proj2", "dev"): {"CACHE_URL": "redis://localhost"},
}


def _mock_list_projects():
    return list({p for p, _ in PROFILES})


def _mock_list_profiles(project):
    return [prof for proj, prof in PROFILES if proj == project]


def _mock_get_profile(project, profile, password=None):
    return PROFILES[(project, profile)]


@pytest.fixture(autouse=True)
def patch_deps():
    with patch("envctl.search.list_projects", side_effect=_mock_list_projects), \
         patch("envctl.search.list_profiles", side_effect=_mock_list_profiles), \
         patch("envctl.search.get_profile", side_effect=_mock_get_profile):
        yield


@pytest.fixture
def runner():
    return CliRunner()


def test_search_by_key_exact():
    from envctl.search import search_by_key
    results = search_by_key("DB_HOST")
    keys = [(r["project"], r["profile"], r["key"]) for r in results]
    assert ("proj1", "dev", "DB_HOST") in keys
    assert ("proj1", "prod", "DB_HOST") in keys


def test_search_by_key_glob():
    from envctl.search import search_by_key
    results = search_by_key("DB_*")
    assert len(results) == 3  # DB_HOST x2, DB_PORT x1


def test_search_by_key_scoped_to_project():
    from envctl.search import search_by_key
    results = search_by_key("DB_*", project="proj2")
    assert results == []


def test_search_by_value_glob():
    from envctl.search import search_by_value
    results = search_by_value("*localhost*")
    values = [r["value"] for r in results]
    assert "localhost" in values
    assert "redis://localhost" in values


def test_search_by_value_no_match():
    from envctl.search import search_by_value
    results = search_by_value("nonexistent")
    assert results == []


def test_cli_search_key(runner):
    result = runner.invoke(search_cmd, ["key", "DB_HOST"])
    assert result.exit_code == 0
    assert "DB_HOST" in result.output


def test_cli_search_key_no_match(runner):
    result = runner.invoke(search_cmd, ["key", "NOTHING"])
    assert result.exit_code == 0
    assert "No matches found" in result.output


def test_cli_search_value(runner):
    result = runner.invoke(search_cmd, ["value", "*localhost*"])
    assert result.exit_code == 0
    assert "localhost" in result.output
