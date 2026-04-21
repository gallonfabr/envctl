"""Profile dependency resolution — declare that one profile requires another."""

from __future__ import annotations

from typing import List

from envctl.storage import load_profiles, save_profiles


class DependencyError(Exception):
    """Raised when a dependency operation fails."""


def _meta(project: str, profile: str) -> dict:
    store = load_profiles()
    try:
        return store[project][profile]
    except KeyError:
        raise DependencyError(f"Profile '{project}/{profile}' not found")


def add_dependency(project: str, profile: str, dep_project: str, dep_profile: str) -> None:
    """Record that *profile* depends on *dep_project/dep_profile*."""
    store = load_profiles()
    if project not in store or profile not in store[project]:
        raise DependencyError(f"Profile '{project}/{profile}' not found")
    if dep_project not in store or dep_profile not in store[dep_project]:
        raise DependencyError(f"Dependency profile '{dep_project}/{dep_profile}' not found")

    deps: List[dict] = store[project][profile].setdefault("dependencies", [])
    entry = {"project": dep_project, "profile": dep_profile}
    if entry in deps:
        raise DependencyError(
            f"'{dep_project}/{dep_profile}' is already a dependency of '{project}/{profile}'"
        )
    deps.append(entry)
    save_profiles(store)


def remove_dependency(project: str, profile: str, dep_project: str, dep_profile: str) -> None:
    """Remove a declared dependency from *profile*."""
    store = load_profiles()
    if project not in store or profile not in store[project]:
        raise DependencyError(f"Profile '{project}/{profile}' not found")

    deps: List[dict] = store[project][profile].get("dependencies", [])
    entry = {"project": dep_project, "profile": dep_profile}
    if entry not in deps:
        raise DependencyError(
            f"'{dep_project}/{dep_profile}' is not a dependency of '{project}/{profile}'"
        )
    deps.remove(entry)
    store[project][profile]["dependencies"] = deps
    save_profiles(store)


def get_dependencies(project: str, profile: str) -> List[dict]:
    """Return the list of direct dependencies for *profile*."""
    return list(_meta(project, profile).get("dependencies", []))


def resolve_order(project: str, profile: str, _visited: set | None = None) -> List[dict]:
    """Return dependency profiles in topological order (dependencies first)."""
    if _visited is None:
        _visited = set()
    key = (project, profile)
    if key in _visited:
        raise DependencyError(f"Circular dependency detected at '{project}/{profile}'")
    _visited.add(key)

    result: List[dict] = []
    for dep in get_dependencies(project, profile):
        dp, dpf = dep["project"], dep["profile"]
        result.extend(resolve_order(dp, dpf, _visited))
        dep_entry = {"project": dp, "profile": dpf}
        if dep_entry not in result:
            result.append(dep_entry)
    return result
