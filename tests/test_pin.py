"""Tests for envctl.pin module."""

import pytest
from unittest.mock import patch, MagicMock

from envctl.pin import pin_profile, unpin_profile, get_pinned


BASE_STORE = {
    "myproject": {
        "dev": {"vars": {"KEY": "val"}},
        "prod": {"vars": {"KEY": "prodval"}},
    }
}


def _store_copy():
    import copy
    return copy.deepcopy(BASE_STORE)


@patch("envctl.pin.log_event")
@patch("envctl.pin.save_profiles")
@patch("envctl.pin.load_profiles")
def test_pin_profile(mock_load, mock_save, mock_log):
    store = _store_copy()
    mock_load.return_value = store
    pin_profile("myproject", "dev")
    assert store["myproject"]["__pinned__"] == "dev"
    mock_save.assert_called_once_with(store)
    mock_log.assert_called_once_with("myproject", "dev", "pin")


@patch("envctl.pin.log_event")
@patch("envctl.pin.save_profiles")
@patch("envctl.pin.load_profiles")
def test_pin_missing_project(mock_load, mock_save, mock_log):
    mock_load.return_value = _store_copy()
    with pytest.raises(KeyError):
        pin_profile("ghost", "dev")


@patch("envctl.pin.log_event")
@patch("envctl.pin.save_profiles")
@patch("envctl.pin.load_profiles")
def test_pin_missing_profile(mock_load, mock_save, mock_log):
    mock_load.return_value = _store_copy()
    with pytest.raises(KeyError):
        pin_profile("myproject", "staging")


@patch("envctl.pin.log_event")
@patch("envctl.pin.save_profiles")
@patch("envctl.pin.load_profiles")
def test_pin_overwrites_existing_pin(mock_load, mock_save, mock_log):
    """Pinning a new profile when one is already pinned should update the pin."""
    store = _store_copy()
    store["myproject"]["__pinned__"] = "dev"
    mock_load.return_value = store
    pin_profile("myproject", "prod")
    assert store["myproject"]["__pinned__"] == "prod"
    mock_save.assert_called_once_with(store)
    mock_log.assert_called_once_with("myproject", "prod", "pin")


@patch("envctl.pin.log_event")
@patch("envctl.pin.save_profiles")
@patch("envctl.pin.load_profiles")
def test_unpin_profile(mock_load, mock_save, mock_log):
    store = _store_copy()
    store["myproject"]["__pinned__"] = "dev"
    mock_load.return_value = store
    unpin_profile("myproject")
    assert "__pinned__" not in store["myproject"]
    mock_log.assert_called_once_with("myproject", "dev", "unpin")


@patch("envctl.pin.load_profiles")
def test_unpin_no_pin_raises(mock_load):
    mock_load.return_value = _store_copy()
    with pytest.raises(ValueError):
        unpin_profile("myproject")


@patch("envctl.pin.load_profiles")
def test_get_pinned_returns_name(mock_load):
    store = _store_copy()
    store["myproject"]["__pinned__"] = "prod"
    mock_load.return_value = store
    assert get_pinned("myproject") == "prod"


@patch("envctl.pin.load_profiles")
def test_get_pinned_none_when_unset(mock_load):
    mock_load.return_value = _store_copy()
    assert get_pinned("myproject") is None


@patch("envctl.pin.load_profiles")
def test_get_pinned_missing_project(mock_load):
    mock_load.return_value = _store_copy()
    with pytest.raises(KeyError):
        get_pinned("ghost")
