"""Tests for envctl.dependency."""

from __future__ import annotations

import pytest

from envctl.dependency import (
    DependencyError,
    add_dependency,
    get_dependencies,
    remove_dependency,
    resolve_order,
)
from envctl.storage import load_profiles, save_profiles


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    store_file = tmp_path / "profiles.json"
    monkeypatch.setattr("envctl.storage.get_store_path", lambda: store_file)
    # Seed two projects with two profiles each
    store = {
        "proj_a": {
            "dev": {"vars": {"A": "1"}},
            "prod": {"vars": {"A": "2"}},
        },
        "proj_b": {
            "dev": {"vars": {"B": "3"}},
        },
    }
    save_profiles(store)
    yield


def test_add_dependency_persists():
    add_dependency("proj_a", "dev", "proj_b", "dev")
    deps = get_dependencies("proj_a", "dev")
    assert {"project": "proj_b", "profile": "dev"} in deps


def test_add_dependency_duplicate_raises():
    add_dependency("proj_a", "dev", "proj_b", "dev")
    with pytest.raises(DependencyError, match="already a dependency"):
        add_dependency("proj_a", "dev", "proj_b", "dev")


def test_add_dependency_missing_profile_raises():
    with pytest.raises(DependencyError, match="not found"):
        add_dependency("proj_a", "ghost", "proj_b", "dev")


def test_add_dependency_missing_dep_raises():
    with pytest.raises(DependencyError, match="not found"):
        add_dependency("proj_a", "dev", "proj_b", "ghost")


def test_remove_dependency():
    add_dependency("proj_a", "dev", "proj_b", "dev")
    remove_dependency("proj_a", "dev", "proj_b", "dev")
    assert get_dependencies("proj_a", "dev") == []


def test_remove_dependency_not_present_raises():
    with pytest.raises(DependencyError, match="not a dependency"):
        remove_dependency("proj_a", "dev", "proj_b", "dev")


def test_get_dependencies_empty():
    assert get_dependencies("proj_a", "dev") == []


def test_get_dependencies_missing_profile_raises():
    with pytest.raises(DependencyError):
        get_dependencies("proj_a", "ghost")


def test_resolve_order_no_deps():
    assert resolve_order("proj_a", "dev") == []


def test_resolve_order_single_dep():
    add_dependency("proj_a", "dev", "proj_b", "dev")
    order = resolve_order("proj_a", "dev")
    assert order == [{"project": "proj_b", "profile": "dev"}]


def test_resolve_order_transitive():
    # proj_a/dev -> proj_a/prod -> proj_b/dev
    add_dependency("proj_a", "prod", "proj_b", "dev")
    add_dependency("proj_a", "dev", "proj_a", "prod")
    order = resolve_order("proj_a", "dev")
    assert order.index({"project": "proj_b", "profile": "dev"}) < order.index(
        {"project": "proj_a", "profile": "prod"}
    )


def test_resolve_order_circular_raises():
    # Manually create a cycle via raw storage
    store = load_profiles()
    store["proj_a"]["dev"]["dependencies"] = [{"project": "proj_a", "profile": "prod"}]
    store["proj_a"]["prod"]["dependencies"] = [{"project": "proj_a", "profile": "dev"}]
    save_profiles(store)
    with pytest.raises(DependencyError, match="Circular"):
        resolve_order("proj_a", "dev")
