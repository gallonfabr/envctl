"""Checkpoint module: named save-points for profiles with restore support."""
from __future__ import annotations

import time
from typing import Optional

from envctl.storage import load_profiles, save_profiles
from envctl.audit import log_event


class CheckpointError(Exception):
    pass


def _meta(project: str, profile: str, data: dict) -> dict:
    return (
        data
        .setdefault("projects", {})
        .setdefault(project, {})
        .setdefault(profile, {})
        .setdefault("_meta", {})
    )


def create_checkpoint(project: str, profile: str, name: str) -> dict:
    """Save the current vars of a profile as a named checkpoint."""
    data = load_profiles()
    profiles = data.get("projects", {}).get(project, {})
    if profile not in profiles:
        raise CheckpointError(f"Profile '{profile}' not found in project '{project}'")
    if not name or not name.strip():
        raise CheckpointError("Checkpoint name must not be empty")

    meta = _meta(project, profile, data)
    checkpoints = meta.setdefault("checkpoints", {})
    entry = {
        "vars": dict(profiles[profile].get("vars", {})),
        "created_at": time.time(),
    }
    checkpoints[name] = entry
    save_profiles(data)
    log_event(project, profile, "checkpoint_created", {"name": name})
    return entry


def restore_checkpoint(project: str, profile: str, name: str) -> dict:
    """Restore profile vars from a named checkpoint."""
    data = load_profiles()
    meta = _meta(project, profile, data)
    checkpoints = meta.get("checkpoints", {})
    if name not in checkpoints:
        raise CheckpointError(f"Checkpoint '{name}' not found for '{project}/{profile}'")

    saved_vars = checkpoints[name]["vars"]
    data["projects"][project][profile]["vars"] = dict(saved_vars)
    save_profiles(data)
    log_event(project, profile, "checkpoint_restored", {"name": name})
    return saved_vars


def list_checkpoints(project: str, profile: str) -> list[dict]:
    """Return all checkpoints for a profile, sorted newest first."""
    data = load_profiles()
    meta = _meta(project, profile, data)
    checkpoints = meta.get("checkpoints", {})
    return sorted(
        [{"name": k, **v} for k, v in checkpoints.items()],
        key=lambda x: x["created_at"],
        reverse=True,
    )


def delete_checkpoint(project: str, profile: str, name: str) -> None:
    """Remove a named checkpoint."""
    data = load_profiles()
    meta = _meta(project, profile, data)
    checkpoints = meta.get("checkpoints", {})
    if name not in checkpoints:
        raise CheckpointError(f"Checkpoint '{name}' not found for '{project}/{profile}'")
    del checkpoints[name]
    save_profiles(data)
    log_event(project, profile, "checkpoint_deleted", {"name": name})
