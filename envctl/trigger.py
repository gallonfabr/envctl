"""Trigger module: attach shell commands to profile lifecycle events."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Optional

from envctl.storage import load_profiles, save_profiles

VALID_EVENTS = ("pre_apply", "post_apply", "pre_delete", "post_delete")


class TriggerError(Exception):
    pass


def _meta(project: str, profile: str, data: dict) -> dict:
    return (
        data.get(project, {})
        .get("profiles", {})
        .get(profile, {})
        .get("_meta", {})
    )


def set_trigger(project: str, profile: str, event: str, command: str) -> None:
    """Attach *command* to *event* for the given profile."""
    if event not in VALID_EVENTS:
        raise TriggerError(f"Invalid event '{event}'. Valid events: {VALID_EVENTS}")
    if not command.strip():
        raise TriggerError("Command must not be empty.")
    data = load_profiles()
    if project not in data or profile not in data[project].get("profiles", {}):
        raise TriggerError(f"Profile '{project}/{profile}' not found.")
    meta = data[project]["profiles"][profile].setdefault("_meta", {})
    triggers = meta.setdefault("triggers", {})
    triggers[event] = command
    save_profiles(data)


def remove_trigger(project: str, profile: str, event: str) -> None:
    """Remove the trigger for *event* from the given profile."""
    data = load_profiles()
    triggers = (
        data.get(project, {})
        .get("profiles", {})
        .get(profile, {})
        .get("_meta", {})
        .get("triggers", {})
    )
    if event not in triggers:
        raise TriggerError(f"No trigger set for event '{event}' on '{project}/{profile}'.")
    del triggers[event]
    save_profiles(data)


def get_triggers(project: str, profile: str) -> dict:
    """Return all triggers for the given profile (may be empty)."""
    data = load_profiles()
    return (
        data.get(project, {})
        .get("profiles", {})
        .get(profile, {})
        .get("_meta", {})
        .get("triggers", {})
    )


def fire_trigger(project: str, profile: str, event: str) -> Optional[int]:
    """Run the command attached to *event*, if any. Returns exit code or None."""
    triggers = get_triggers(project, profile)
    command = triggers.get(event)
    if not command:
        return None
    result = subprocess.run(command, shell=True)  # noqa: S602
    return result.returncode
