"""Tests for envctl.group and envctl.cli_group."""
import pytest
from unittest.mock import patch
from click.testing import CliRunner
from envctl.group import (
    create_group, delete_group, get_group, list_groups,
    add_to_group, remove_from_group, GroupError
)
from envctl.cli_group import group_cmd

BASE_DATA = {
    "myproject": {
        "dev": {"vars": {"KEY": "val"}},
        "prod": {"vars": {"KEY": "prodval"}},
    }
}


@pytest.fixture(autouse=True)
def reset_profiles():
    import copy
    data = copy.deepcopy(BASE_DATA)
    with patch("envctl.group.load_profiles", return_value=data), \
         patch("envctl.group.save_profiles") as mock_save, \
         patch("envctl.group.log_event"):
        yield mock_save


def test_create_group_success(reset_profiles):
    create_group("g1", [("myproject", "dev"), ("myproject", "prod")])
    saved = reset_profiles.call_args[0][0]
    assert "g1" in saved["__groups__"]
    assert len(saved["__groups__"]["g1"]) == 2


def test_create_group_missing_profile():
    with patch("envctl.group.load_profiles", return_value={"myproject": {"dev": {}}}), \
         patch("envctl.group.save_profiles"), patch("envctl.group.log_event"):
        with pytest.raises(GroupError, match="not found"):
            create_group("g1", [("myproject", "missing")])


def test_create_group_empty_name():
    with pytest.raises(GroupError, match="empty"):
        create_group("", [("myproject", "dev")])


def test_delete_group(reset_profiles):
    import copy
    data = copy.deepcopy(BASE_DATA)
    data["__groups__"] = {"g1": [{"project": "myproject", "profile": "dev"}]}
    with patch("envctl.group.load_profiles", return_value=data), \
         patch("envctl.group.save_profiles") as ms, patch("envctl.group.log_event"):
        delete_group("g1")
        saved = ms.call_args[0][0]
        assert "g1" not in saved["__groups__"]


def test_delete_group_missing():
    with patch("envctl.group.load_profiles", return_value={}), \
         patch("envctl.group.save_profiles"), patch("envctl.group.log_event"):
        with pytest.raises(GroupError):
            delete_group("nope")


def test_list_groups(reset_profiles):
    import copy
    data = copy.deepcopy(BASE_DATA)
    data["__groups__"] = {"alpha": [], "beta": []}
    with patch("envctl.group.load_profiles", return_value=data):
        result = list_groups()
    assert set(result) == {"alpha", "beta"}


def test_add_to_group(reset_profiles):
    import copy
    data = copy.deepcopy(BASE_DATA)
    data["__groups__"] = {"g1": []}
    with patch("envctl.group.load_profiles", return_value=data), \
         patch("envctl.group.save_profiles") as ms, patch("envctl.group.log_event"):
        add_to_group("g1", "myproject", "dev")
        saved = ms.call_args[0][0]
        assert {"project": "myproject", "profile": "dev"} in saved["__groups__"]["g1"]


def test_remove_from_group(reset_profiles):
    import copy
    data = copy.deepcopy(BASE_DATA)
    data["__groups__"] = {"g1": [{"project": "myproject", "profile": "dev"}]}
    with patch("envctl.group.load_profiles", return_value=data), \
         patch("envctl.group.save_profiles") as ms, patch("envctl.group.log_event"):
        remove_from_group("g1", "myproject", "dev")
        saved = ms.call_args[0][0]
        assert saved["__groups__"]["g1"] == []


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_list_empty(runner):
    with patch("envctl.cli_group.list_groups", return_value=[]):
        result = runner.invoke(group_cmd, ["list"])
    assert "No groups" in result.output


def test_cli_show(runner):
    members = [{"project": "myproject", "profile": "dev"}]
    with patch("envctl.cli_group.get_group", return_value=members):
        result = runner.invoke(group_cmd, ["show", "g1"])
    assert "myproject:dev" in result.output


def test_cli_create_bad_format(runner):
    result = runner.invoke(group_cmd, ["create", "g1", "badformat"])
    assert result.exit_code != 0
