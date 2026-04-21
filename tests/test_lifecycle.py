"""Tests for envctl.lifecycle."""

import pytest

from envctl.lifecycle import (
    LifecycleError,
    clear_hooks,
    fire,
    list_hooks,
    register,
    unregister,
)


@pytest.fixture(autouse=True)
def reset_hooks():
    yield
    clear_hooks()


def test_register_and_fire():
    calls = []
    register("post_apply", lambda project, profile: calls.append((project, profile)))
    fire("post_apply", project="myapp", profile="prod")
    assert calls == [("myapp", "prod")]


def test_register_invalid_event_raises():
    with pytest.raises(LifecycleError, match="Unknown event"):
        register("on_explode", lambda: None)


def test_fire_invalid_event_raises():
    with pytest.raises(LifecycleError, match="Unknown event"):
        fire("on_explode")


def test_multiple_hooks_all_called():
    results = []
    register("pre_add", lambda **kw: results.append("a"))
    register("pre_add", lambda **kw: results.append("b"))
    fire("pre_add", project="x", profile="y")
    assert results == ["a", "b"]


def test_unregister_removes_hook():
    calls = []

    def hook(**kw):
        calls.append(True)

    register("pre_delete", hook)
    unregister("pre_delete", hook)
    fire("pre_delete", project="x", profile="y")
    assert calls == []


def test_unregister_nonexistent_is_silent():
    unregister("pre_apply", lambda: None)  # should not raise


def test_list_hooks_returns_copy():
    fn = lambda **kw: None
    register("post_add", fn)
    hooks = list_hooks("post_add")
    assert fn in hooks
    hooks.clear()  # mutating the copy must not affect internal state
    assert len(list_hooks("post_add")) == 1


def test_clear_hooks_specific_event():
    register("post_delete", lambda **kw: None)
    register("pre_apply", lambda **kw: None)
    clear_hooks("post_delete")
    assert list_hooks("post_delete") == []
    assert len(list_hooks("pre_apply")) == 1


def test_clear_hooks_all():
    register("post_apply", lambda **kw: None)
    register("pre_add", lambda **kw: None)
    clear_hooks()
    assert list_hooks("post_apply") == []
    assert list_hooks("pre_add") == []
