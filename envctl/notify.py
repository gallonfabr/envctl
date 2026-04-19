"""Notification hooks for envctl events."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

from envctl.storage import get_store_path

_HOOKS_FILE = "hooks.json"


def _get_hooks_path() -> Path:
    return get_store_path().parent / _HOOKS_FILE


def _load() -> dict:
    p = _get_hooks_path()
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save(data: dict) -> None:
    _get_hooks_path().write_text(json.dumps(data, indent=2))


def set_hook(event: str, command: str) -> None:
    """Register a shell command to run when *event* fires."""
    hooks = _load()
    hooks[event] = command
    _save(hooks)


def remove_hook(event: str) -> None:
    """Remove the hook for *event*. Silently ignores missing events."""
    hooks = _load()
    hooks.pop(event, None)
    _save(hooks)


def get_hook(event: str) -> Optional[str]:
    """Return the command registered for *event*, or None."""
    return _load().get(event)


def list_hooks() -> dict[str, str]:
    """Return all registered hooks."""
    return _load()


def fire(event: str, env_vars: Optional[dict[str, str]] = None) -> Optional[int]:
    """Execute the hook command for *event* if one is registered.

    Extra *env_vars* are passed to the subprocess environment.
    Returns the process exit code, or None if no hook is registered.
    """
    import os
    command = get_hook(event)
    if command is None:
        return None
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
    result = subprocess.run(command, shell=True, env=env)
    return result.returncode
