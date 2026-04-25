"""Tests for envctl.shadow."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from envctl.shadow import (
    create_shadow,
    promote_shadow,
    discard_shadow,
    has_shadow,
    list_shadows,
    ShadowError,
    SHADOW_PREFIX,
    _shadow_name,
)

_VARS = {"KEY": "value", "PORT": "8080"}


@pytest.fixture()
def patch_deps():
    with (
        patch("envctl.shadow.get_profile") as mock_get,
        patch("envctl.shadow.add_profile") as mock_add,
        patch("envctl.shadow.delete_profile") as mock_del,
        patch("envctl.shadow.load_profiles") as mock_load,
        patch("envctl.shadow.log_event") as mock_log,
    ):
        yield {
            "get": mock_get,
            "add": mock_add,
            "del": mock_del,
            "load": mock_load,
            "log": mock_log,
        }


def test_shadow_name():
    assert _shadow_name("prod") == f"{SHADOW_PREFIX}prod"


def test_create_shadow_success(patch_deps):
    patch_deps["get"].return_value = _VARS
    shadow = create_shadow("myproject", "prod")
    assert shadow == _shadow_name("prod")
    patch_deps["add"].assert_called_once_with("myproject", shadow, _VARS, password=None)
    patch_deps["log"].assert_called_once()


def test_create_shadow_missing_profile_raises(patch_deps):
    patch_deps["get"].return_value = None
    with pytest.raises(ShadowError, match="not found"):
        create_shadow("myproject", "ghost")


def test_promote_shadow_success(patch_deps):
    shadow = _shadow_name("prod")
    patch_deps["get"].return_value = _VARS
    promote_shadow("myproject", "prod")
    patch_deps["add"].assert_called_once_with("myproject", "prod", _VARS, password=None)
    patch_deps["del"].assert_called_once_with("myproject", shadow)
    patch_deps["log"].assert_called_once()


def test_promote_shadow_missing_raises(patch_deps):
    patch_deps["get"].return_value = None
    with pytest.raises(ShadowError, match="No shadow found"):
        promote_shadow("myproject", "prod")


def test_discard_shadow_success(patch_deps):
    shadow = _shadow_name("prod")
    patch_deps["load"].return_value = {shadow: {}}
    discard_shadow("myproject", "prod")
    patch_deps["del"].assert_called_once_with("myproject", shadow)
    patch_deps["log"].assert_called_once()


def test_discard_shadow_missing_raises(patch_deps):
    patch_deps["load"].return_value = {}
    with pytest.raises(ShadowError, match="No shadow found"):
        discard_shadow("myproject", "prod")


def test_has_shadow_true(patch_deps):
    patch_deps["load"].return_value = {_shadow_name("prod"): {}}
    assert has_shadow("myproject", "prod") is True


def test_has_shadow_false(patch_deps):
    patch_deps["load"].return_value = {"prod": {}}
    assert has_shadow("myproject", "prod") is False


def test_list_shadows_returns_original_names(patch_deps):
    patch_deps["load"].return_value = {
        _shadow_name("prod"): {},
        _shadow_name("staging"): {},
        "dev": {},
    }
    result = list_shadows("myproject")
    assert sorted(result) == ["prod", "staging"]


def test_list_shadows_empty(patch_deps):
    patch_deps["load"].return_value = {"prod": {}, "dev": {}}
    assert list_shadows("myproject") == []
