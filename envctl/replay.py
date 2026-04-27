"""replay.py – re-apply a sequence of historical profile applies.

Allows users to replay the last N apply events for a project, useful
for reproducing environment states during debugging or auditing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from envctl.audit import log_event
from envctl.history import get_history
from envctl.profile import apply_profile


class ReplayError(Exception):
    """Raised when a replay operation cannot be completed."""


@dataclass
class ReplayResult:
    project: str
    replayed: List[str]   # profile names in replay order
    skipped: List[str]    # profiles that no longer exist


def replay_project(project: str, steps: int = 1, password: str | None = None) -> ReplayResult:
    """Re-apply the last *steps* distinct profiles applied to *project*.

    Args:
        project: Target project name.
        steps:   How many history entries to replay (default 1).
        password: Optional decryption password forwarded to apply_profile.

    Returns:
        ReplayResult describing what was replayed or skipped.

    Raises:
        ReplayError: If steps < 1 or no history is found.
    """
    if steps < 1:
        raise ReplayError("steps must be >= 1")

    history = get_history(project)
    if not history:
        raise ReplayError(f"No apply history found for project '{project}'")

    entries = history[:steps]
    replayed: List[str] = []
    skipped: List[str] = []

    for entry in reversed(entries):  # oldest first so final state matches newest
        profile = entry["profile"]
        try:
            apply_profile(project, profile, password=password)
            replayed.append(profile)
            log_event(project, profile, "replay")
        except KeyError:
            skipped.append(profile)

    return ReplayResult(project=project, replayed=replayed, skipped=skipped)


def replay_summary(result: ReplayResult) -> str:
    """Return a human-readable summary of a ReplayResult."""
    lines = [f"Replay for project '{result.project}':"]
    if result.replayed:
        lines.append("  Replayed: " + ", ".join(result.replayed))
    else:
        lines.append("  Nothing replayed.")
    if result.skipped:
        lines.append("  Skipped (missing): " + ", ".join(result.skipped))
    return "\n".join(lines)
