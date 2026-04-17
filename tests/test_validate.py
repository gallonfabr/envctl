"""Tests for envctl.validate."""

import pytest
from envctl.validate import (
    validate_var_name,
    validate_vars,
    validate_profile_name,
    validate_project_name,
    assert_valid_profile,
)


def test_valid_var_names():
    assert validate_var_name("FOO") is True
    assert validate_var_name("FOO_BAR") is True
    assert validate_var_name("_PRIVATE") is True
    assert validate_var_name("A1_B2") is True


def test_invalid_var_names():
    assert validate_var_name("foo") is False
    assert validate_var_name("1FOO") is False
    assert validate_var_name("") is False
    assert validate_var_name("FOO-BAR") is False


def test_validate_vars_clean():
    errors = validate_vars({"FOO": "bar", "BAZ": "qux"})
    assert errors == []


def test_validate_vars_bad_key():
    errors = validate_vars({"bad_key": "value"})
    assert len(errors) == 1
    assert errors[0][0] == "bad_key"


def test_validate_vars_non_string_value():
    errors = validate_vars({"FOO": 123})  # type: ignore
    assert any(k == "FOO" for k, _ in errors)


def test_validate_profile_name_valid():
    assert validate_profile_name("dev") is True
    assert validate_profile_name("prod-eu") is True
    assert validate_profile_name("staging_2") is True


def test_validate_profile_name_invalid():
    assert validate_profile_name("") is False
    assert validate_profile_name("my profile") is False
    assert validate_profile_name("prof@1") is False


def test_validate_project_name():
    assert validate_project_name("my-app") is True
    assert validate_project_name("bad name") is False


def test_assert_valid_profile_passes():
    assert_valid_profile("my-app", "dev", {"FOO": "bar"})


def test_assert_valid_profile_bad_project():
    with pytest.raises(ValueError, match="project"):
        assert_valid_profile("bad project!", "dev", {})


def test_assert_valid_profile_bad_profile():
    with pytest.raises(ValueError, match="profile"):
        assert_valid_profile("app", "bad name", {})


def test_assert_valid_profile_bad_vars():
    with pytest.raises(ValueError, match="Invalid variables"):
        assert_valid_profile("app", "dev", {"lowercase": "val"})
