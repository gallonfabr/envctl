"""Audit log for tracking profile access and modifications."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

AUDIT_FILE = "audit.log"


def get_audit_path() -> Path:
    base = Path(os.environ.get("ENVCTL_HOME", Path.home() / ".envctl"))
    base.mkdir(parents=True, exist_ok=True)
    return base / AUDIT_FILE


def log_event(action: str, project: str, profile: str, extra: Optional[dict] = None) -> None:
    """Append an audit event to the log file."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "project": project,
        "profile": profile,
    }
    if extra:
        entry.update(extra)
    with open(get_audit_path(), "a") as f:
        f.write(json.dumps(entry) + "\n")


def read_events(project: Optional[str] = None, limit: int = 50) -> list:
    """Read audit events, optionally filtered by project."""
    path = get_audit_path()
    if not path.exists():
        return []
    events = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if project is None or event.get("project") == project:
                events.append(event)
    return events[-limit:]


def clear_audit_log() -> None:
    """Clear the audit log."""
    path = get_audit_path()
    if path.exists():
        path.unlink()
