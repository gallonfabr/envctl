"""Tag management for environment profiles."""

from envctl.storage import load_profiles, save_profiles


def add_tag(project: str, profile: str, tag: str) -> None:
    """Add a tag to a profile."""
    data = load_profiles()
    try:
        prof = data[project][profile]
    except KeyError:
        raise KeyError(f"Profile '{profile}' not found in project '{project}'")
    tags = prof.setdefault("tags", [])
    if tag not in tags:
        tags.append(tag)
    save_profiles(data)


def remove_tag(project: str, profile: str, tag: str) -> None:
    """Remove a tag from a profile."""
    data = load_profiles()
    try:
        prof = data[project][profile]
    except KeyError:
        raise KeyError(f"Profile '{profile}' not found in project '{project}'")
    tags = prof.get("tags", [])
    if tag not in tags:
        raise ValueError(f"Tag '{tag}' not found on profile '{profile}'")
    tags.remove(tag)
    prof["tags"] = tags
    save_profiles(data)


def list_tags(project: str, profile: str) -> list[str]:
    """List all tags on a profile."""
    data = load_profiles()
    try:
        prof = data[project][profile]
    except KeyError:
        raise KeyError(f"Profile '{profile}' not found in project '{project}'")
    return prof.get("tags", [])


def find_by_tag(tag: str) -> list[tuple[str, str]]:
    """Return (project, profile) pairs that have the given tag."""
    data = load_profiles()
    results = []
    for project, profiles in data.items():
        for profile_name, prof in profiles.items():
            if isinstance(prof, dict) and tag in prof.get("tags", []):
                results.append((project, profile_name))
    return results
