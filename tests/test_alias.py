"""Tests for envctl.alias module."""

import pytest
from unittest.mock import patch

from envctl.alias import set_alias, remove_alias, get_alias, resolve_alias, list_aliases, AliasError

BASE_STORE = {
    "myapp": {
        "dev": {"vars": {"KEY": "val"}},
        "prod": {"vars": {"KEY": "prodval"}, "alias": "production"},
    }
}


def _store_copy():
    import copy
    return copy.deepcopy(BASE_STORE)


@pytest.fixture
def patch_storage(tmp_path):
    store = _store_copy()
    with patch("envctl.alias.load_profiles", return_value=store), \
         patch("envctl.alias.save_profiles") as mock_save:
        yield store, mock_save


def test_set_alias_persists(patch_storage):
    store, mock_save = patch_storage
    set_alias("myapp", "dev", "development")
    assert store["myapp"]["dev"]["alias"] == "development"
    mock_save.assert_called_once()


def test_set_alias_missing_profile(patch_storage):
    store, _ = patch_storage
    with pytest.raises(AliasError, match="not found"):
        set_alias("myapp", "staging", "stg")


def test_set_alias_duplicate_raises(patch_storage):
    store, _ = patch_storage
    with pytest.raises(AliasError, match="already used"):
        set_alias("myapp", "dev", "production")


def test_remove_alias(patch_storage):
    store, mock_save = patch_storage
    remove_alias("myapp", "prod")
    assert "alias" not in store["myapp"]["prod"]
    mock_save.assert_called_once()


def test_remove_alias_not_set(patch_storage):
    store, _ = patch_storage
    with pytest.raises(AliasError, match="has no alias"):
        remove_alias("myapp", "dev")


def test_get_alias_returns_value(patch_storage):
    store, _ = patch_storage
    assert get_alias("myapp", "prod") == "production"


def test_get_alias_none_when_unset(patch_storage):
    store, _ = patch_storage
    assert get_alias("myapp", "dev") is None


def test_resolve_alias_finds_profile(patch_storage):
    store, _ = patch_storage
    assert resolve_alias("myapp", "production") == "prod"


def test_resolve_alias_unknown_returns_none(patch_storage):
    store, _ = patch_storage
    assert resolve_alias("myapp", "unknown") is None


def test_list_aliases(patch_storage):
    store, _ = patch_storage
    aliases = list_aliases("myapp")
    assert aliases == {"prod": "production"}


def test_list_aliases_unknown_project(patch_storage):
    store, _ = patch_storage
    assert list_aliases("noproject") == {}
