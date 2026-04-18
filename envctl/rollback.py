"""Rollback to a previously applied profile using apply history."""

from envctl.history import get_history
from envctl.profile import apply_profile
from envctl.audit import log_event


class RollbackError(Exception):
    pass


def rollback(project: str, steps: int = 1, password: str | None = None) -> dict:
    """Rollback to a previously applied profile.

    Args:
        project: project name
        steps: how many steps back to go (default 1 = previous)
        password: optional decryption password

    Returns:
        The history entry that was restored.
    """
    if steps < 1:
        raise RollbackError("steps must be >= 1")

    history = get_history(project)
    # history[0] is current, history[steps] is target
    if len(history) <= steps:
        raise RollbackError(
            f"Not enough history to roll back {steps} step(s) for project '{project}'. "
            f"Only {len(history)} entr{'y' if len(history) == 1 else 'ies'} available."
        )

    target = history[steps]
    profile_name = target["profile"]

    vars_ = apply_profile(project, profile_name, password=password)

    log_event(
        project=project,
        action="rollback",
        profile=profile_name,
        details={"steps": steps},
    )

    return {"project": project, "profile": profile_name, "vars": vars_}


def rollback_to(project: str, profile: str, password: str | None = None) -> dict:
    """Rollback to a specific profile by name (must exist in history)."""
    history = get_history(project)
    names = [e["profile"] for e in history]

    if profile not in names:
        raise RollbackError(
            f"Profile '{profile}' not found in apply history for project '{project}'."
        )

    vars_ = apply_profile(project, profile, password=password)

    log_event(
        project=project,
        action="rollback_to",
        profile=profile,
    )

    return {"project": project, "profile": profile, "vars": vars_}
