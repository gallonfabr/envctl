"""Tests for envctl.impact and envctl.cli_impact."""
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from envctl.impact import analyze_key_impact, analyze_value_impact, format_impact_report, ImpactError
from envctl.cli_impact import impact_cmd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_profile(vars_: dict) -> dict:
    return {"vars": vars_}


def _patch_deps(projects, profiles_map, profiles_data):
    """Return a context manager that patches storage + profile lookups."""
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        with patch("envctl.impact.list_projects", return_value=projects), \
             patch("envctl.impact.list_profiles", side_effect=lambda p: profiles_map.get(p, [])), \
             patch("envctl.impact.get_profile", side_effect=lambda proj, prof, **kw: profiles_data[(proj, prof)]), \
             patch("envctl.impact.log_event"):
            yield

    return _ctx()


# ---------------------------------------------------------------------------
# Unit tests — analyze_key_impact
# ---------------------------------------------------------------------------

def test_analyze_key_impact_finds_matching_profiles():
    data = {
        ("proj1", "dev"): _make_profile({"DB_URL": "postgres://", "SECRET": "x"}),
        ("proj1", "prod"): _make_profile({"DB_URL": "mysql://"}),
        ("proj2", "dev"): _make_profile({"API_KEY": "abc"}),
    }
    with _patch_deps(["proj1", "proj2"], {"proj1": ["dev", "prod"], "proj2": ["dev"]}, data):
        result = analyze_key_impact("DB_URL")

    assert result.key == "DB_URL"
    assert result.count == 2
    projects = {e["project"] for e in result.affected}
    assert "proj1" in projects


def test_analyze_key_impact_no_matches():
    data = {("proj1", "dev"): _make_profile({"FOO": "bar"})}
    with _patch_deps(["proj1"], {"proj1": ["dev"]}, data):
        result = analyze_key_impact("MISSING_KEY")
    assert result.count == 0


def test_analyze_key_impact_empty_key_raises():
    with pytest.raises(ImpactError, match="empty"):
        analyze_key_impact("")


def test_analyze_key_impact_skips_erroring_profiles():
    def _bad_get(proj, prof, **kw):
        raise RuntimeError("decryption failed")

    with patch("envctl.impact.list_projects", return_value=["proj1"]), \
         patch("envctl.impact.list_profiles", return_value=["dev"]), \
         patch("envctl.impact.get_profile", side_effect=_bad_get), \
         patch("envctl.impact.log_event"):
        result = analyze_key_impact("ANY")
    assert result.count == 0


# ---------------------------------------------------------------------------
# Unit tests — analyze_value_impact
# ---------------------------------------------------------------------------

def test_analyze_value_impact_finds_matching_profiles():
    data = {
        ("proj1", "dev"): _make_profile({"URL": "http://localhost", "OTHER": "nope"}),
        ("proj1", "prod"): _make_profile({"URL": "http://prod"}),
    }
    with _patch_deps(["proj1"], {"proj1": ["dev", "prod"]}, data):
        hits = analyze_value_impact("http://localhost")

    assert len(hits) == 1
    assert hits[0]["profile"] == "dev"
    assert "URL" in hits[0]["keys"]


def test_analyze_value_impact_none_raises():
    with pytest.raises(ImpactError):
        analyze_value_impact(None)


# ---------------------------------------------------------------------------
# Unit tests — format_impact_report
# ---------------------------------------------------------------------------

def test_format_impact_report_contains_key_and_count():
    from envctl.impact import ImpactResult
    result = ImpactResult(key="SECRET", affected=[
        {"project": "alpha", "profile": "dev"},
        {"project": "beta", "profile": "prod"},
    ])
    report = format_impact_report(result)
    assert "SECRET" in report
    assert "2" in report
    assert "alpha" in report
    assert "beta" in report


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
        return self._r.invoke(impact_cmd, *args, **kwargs)


def test_cli_key_success(runner):
    from envctl.impact import ImpactResult
    mock_result = ImpactResult(key="DB_URL", affected=[{"project": "p", "profile": "dev"}])
    with patch("envctl.cli_impact.analyze_key_impact", return_value=mock_result):
        res = runner.invoke(["key", "DB_URL"])
    assert res.exit_code == 0
    assert "DB_URL" in res.output


def test_cli_key_json(runner):
    from envctl.impact import ImpactResult
    mock_result = ImpactResult(key="X", affected=[])
    with patch("envctl.cli_impact.analyze_key_impact", return_value=mock_result):
        res = runner.invoke(["key", "X", "--json"])
    assert res.exit_code == 0
    import json
    data = json.loads(res.output)
    assert data["key"] == "X"


def test_cli_key_error(runner):
    with patch("envctl.cli_impact.analyze_key_impact", side_effect=ImpactError("bad")):
        res = runner.invoke(["key", ""])
    assert res.exit_code != 0


def test_cli_value_no_hits(runner):
    with patch("envctl.cli_impact.analyze_value_impact", return_value=[]), \
         patch("envctl.cli_impact.log_event", MagicMock()):
        res = runner.invoke(["value", "ghost"])
    assert res.exit_code == 0
    assert "No profiles" in res.output


def test_cli_value_with_hits(runner):
    hits = [{"project": "p", "profile": "dev", "keys": ["SECRET"]}]
    with patch("envctl.cli_impact.analyze_value_impact", return_value=hits):
        res = runner.invoke(["value", "mysecret"])
    assert res.exit_code == 0
    assert "p / dev" in res.output
    assert "SECRET" in res.output
