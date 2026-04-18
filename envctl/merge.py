"""Merge two profiles into a new profile, with conflict resolution strategies."""

from envctl.profile import get_profile, add_profile
from envctl.audit import log_event

STRATEGY_OURS = "ours"
STRATEGY_THEIRS = "theirs"
STRATEGY_ERROR = "error"


def merge_profiles(
    project: str,
    base_profile: str,
    other_profile: str,
    dest_profile: str,
    strategy: str = STRATEGY_ERROR,
    password: str | None = None,
) -> dict:
    """Merge base_profile and other_profile into dest_profile.

    Returns the merged vars dict.
    Raises ValueError on conflicts when strategy is 'error'.
    """
    if strategy not in (STRATEGY_OURS, STRATEGY_THEIRS, STRATEGY_ERROR):
        raise ValueError(f"Unknown strategy: {strategy!r}")

    base_vars = get_profile(project, base_profile)
    other_vars = get_profile(project, other_profile)

    merged = dict(base_vars)
    conflicts = []

    for key, value in other_vars.items():
        if key in merged and merged[key] != value:
            if strategy == STRATEGY_ERROR:
                conflicts.append(key)
            elif strategy == STRATEGY_OURS:
                pass  # keep base value
            elif strategy == STRATEGY_THEIRS:
                merged[key] = value
        else:
            merged[key] = value

    if conflicts:
        raise ValueError(f"Merge conflict on keys: {', '.join(sorted(conflicts))}")

    add_profile(project, dest_profile, merged, password=password)
    log_event(
        project,
        dest_profile,
        "merge",
        {"base": base_profile, "other": other_profile, "strategy": strategy},
    )
    return merged
