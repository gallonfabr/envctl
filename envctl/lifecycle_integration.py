"""Wire lifecycle hooks into profile operations.

Import this module once (e.g. in cli.py) to activate audit logging
and any other side-effects on profile lifecycle events.
"""

from __future__ import annotations

from envctl.audit import log_event
from envctl.lifecycle import register


def _on_post_apply(project: str, profile: str, **_) -> None:
    log_event("lifecycle.post_apply", project=project, profile=profile)


def _on_post_add(project: str, profile: str, **_) -> None:
    log_event("lifecycle.post_add", project=project, profile=profile)


def _on_post_delete(project: str, profile: str, **_) -> None:
    log_event("lifecycle.post_delete", project=project, profile=profile)


def _on_pre_delete(project: str, profile: str, **_) -> None:
    """Guard: could raise to abort deletion (not enforced here, just logged)."""
    log_event("lifecycle.pre_delete", project=project, profile=profile)


def activate() -> None:
    """Register all built-in lifecycle hooks. Safe to call multiple times."""
    register("post_apply", _on_post_apply)
    register("post_add", _on_post_add)
    register("pre_delete", _on_pre_delete)
    register("post_delete", _on_post_delete)
