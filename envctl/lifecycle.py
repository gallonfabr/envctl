"""Profile lifecycle hooks: pre/post apply, add, delete events."""

from __future__ import annotations

from typing import Callable, Dict, List

_hooks: Dict[str, List[Callable[..., None]]] = {}

VALID_EVENTS = (
    "pre_apply",
    "post_apply",
    "pre_add",
    "post_add",
    "pre_delete",
    "post_delete",
)


class LifecycleError(Exception):
    pass


def register(event: str, fn: Callable[..., None]) -> None:
    """Register a callback for a lifecycle event."""
    if event not in VALID_EVENTS:
        raise LifecycleError(
            f"Unknown event '{event}'. Valid events: {', '.join(VALID_EVENTS)}"
        )
    _hooks.setdefault(event, []).append(fn)


def unregister(event: str, fn: Callable[..., None]) -> None:
    """Remove a previously registered callback."""
    if event not in _hooks:
        return
    try:
        _hooks[event].remove(fn)
    except ValueError:
        pass


def fire(event: str, **kwargs) -> None:
    """Invoke all callbacks registered for the given event."""
    if event not in VALID_EVENTS:
        raise LifecycleError(f"Unknown event '{event}'.")
    for fn in list(_hooks.get(event, [])):
        fn(**kwargs)


def list_hooks(event: str) -> List[Callable[..., None]]:
    """Return a copy of registered callbacks for an event."""
    return list(_hooks.get(event, []))


def clear_hooks(event: str | None = None) -> None:
    """Clear hooks for a specific event, or all hooks if event is None."""
    global _hooks
    if event is None:
        _hooks.clear()
    else:
        _hooks.pop(event, None)
