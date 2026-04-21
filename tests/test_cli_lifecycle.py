"""Tests for envctl.cli_lifecycle."""

import pytest
from click.testing import CliRunner

from envctl.cli_lifecycle import lifecycle_cmd
from envctl.lifecycle import clear_hooks, register


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def reset():
    yield
    clear_hooks()


def test_events_lists_all(runner):
    result = runner.invoke(lifecycle_cmd, ["events"])
    assert result.exit_code == 0
    for event in ("pre_apply", "post_apply", "pre_add", "post_add", "pre_delete", "post_delete"):
        assert event in result.output


def test_hooks_no_hooks_registered(runner):
    result = runner.invoke(lifecycle_cmd, ["hooks", "post_apply"])
    assert result.exit_code == 0
    assert "No hooks registered" in result.output


def test_hooks_shows_registered(runner):
    def my_hook(**kw):
        pass

    register("post_apply", my_hook)
    result = runner.invoke(lifecycle_cmd, ["hooks", "post_apply"])
    assert result.exit_code == 0
    assert "1 hook(s)" in result.output
    assert "my_hook" in result.output


def test_hooks_unknown_event_exits_nonzero(runner):
    result = runner.invoke(lifecycle_cmd, ["hooks", "on_explode"])
    assert result.exit_code != 0
    assert "unknown event" in result.output
