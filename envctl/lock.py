"""Profile locking — prevent accidental modifications to profiles."""

from envctl.storage import load_profiles, save_profiles


class LockError(Exception):
    pass


def lock_profile(project: str, profile: str) -> None:
    """Mark a profile as locked."""
    data = load_profiles()
    if project not in data or profile not in data[project]:
        raise LockError(f"Profile '{project}/{profile}' not found.")
    data[project][profile]["_locked"] = True
    save_profiles(data)


def unlock_profile(project: str, profile: str) -> None:
    """Remove the lock from a profile."""
    data = load_profiles()
    if project not in data or profile not in data[project]:
        raise LockError(f"Profile '{project}/{profile}' not found.")
    data[project][profile].pop("_locked", None)
    save_profiles(data)


def is_locked(project: str, profile: str) -> bool:
    """Return True if the profile is locked."""
    data = load_profiles()
    return bool(
        data.get(project, {}).get(profile, {}).get("_locked", False)
    )


def assert_unlocked(project: str, profile: str) -> None:
    """Raise LockError if the profile is locked."""
    if is_locked(project, profile):
        raise LockError(
            f"Profile '{project}/{profile}' is locked. Unlock it first."
        )
