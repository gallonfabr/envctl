import pytest
from unittest.mock import patch
from envctl.lint import lint_profile, lint_project


def _mock_get(project, profile, password=None):
    profiles = {
        ("myapp", "good"): {"DATABASE_URL": "postgres://localhost", "SECRET_KEY": "abc123"},
        ("myapp", "bad"): {
            "database_url": "",
            "tmp_token": "CHANGEME",
            "OK_VAR": "real_value",
        },
    }
    return profiles[(project, profile)]


@pytest.fixture
def patch_get():
    with patch("envctl.lint.get_profile", side_effect=_mock_get):
        yield


def test_lint_clean_profile(patch_get):
    warnings = lint_profile("myapp", "good")
    assert warnings == []


def test_lint_detects_non_uppercase(patch_get):
    warnings = lint_profile("myapp", "bad")
    keys = [w["key"] for w in warnings]
    assert "database_url" in keys


def test_lint_detects_empty_value(patch_get):
    warnings = lint_profile("myapp", "bad")
    empty_warns = [w for w in warnings if w["key"] == "database_url" and w["level"] == "error"]
    assert len(empty_warns) >= 1


def test_lint_detects_placeholder_value(patch_get):
    warnings = lint_profile("myapp", "bad")
    changeme = [w for w in warnings if w["key"] == "tmp_token" and "placeholder" in w["message"]]
    assert len(changeme) >= 1


def test_lint_detects_temp_prefix(patch_get):
    warnings = lint_profile("myapp", "bad")
    tmp_warns = [w for w in warnings if w["key"] == "tmp_token" and "temporary" in w["message"]]
    assert len(tmp_warns) >= 1


def test_lint_ok_var_no_warnings(patch_get):
    warnings = lint_profile("myapp", "bad")
    ok_warns = [w for w in warnings if w["key"] == "OK_VAR"]
    assert ok_warns == []


def test_lint_project(patch_get):
    with patch("envctl.lint.list_profiles", return_value=["good", "bad"]):
        results = lint_project("myapp")
    assert "good" in results
    assert "bad" in results
    assert results["good"] == []
    assert len(results["bad"]) > 0


def test_lint_project_handles_error():
    with patch("envctl.lint.list_profiles", return_value=["broken"]), \
         patch("envctl.lint.get_profile", side_effect=ValueError("decryption failed")):
        results = lint_project("myapp")
    assert results["broken"][0]["level"] == "error"
    assert "decryption failed" in results["broken"][0]["message"]
