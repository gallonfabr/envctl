"""Impact analysis: determine which profiles/projects are affected by a change."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envctl.storage import list_projects, list_profiles
from envctl.profile import get_profile
from envctl.audit import log_event


class ImpactError(Exception):
    pass


@dataclass
class ImpactResult:
    key: str
    affected: List[dict] = field(default_factory=list)  # [{project, profile}]

    @property
    def count(self) -> int:
        return len(self.affected)


def analyze_key_impact(key: str, password: str | None = None) -> ImpactResult:
    """Find all profiles across all projects that define *key*."""
    if not key:
        raise ImpactError("key must not be empty")

    result = ImpactResult(key=key)

    for project in list_projects():
        for profile_name in list_profiles(project):
            try:
                profile = get_profile(project, profile_name, password=password)
            except Exception:
                continue
            vars_ = profile.get("vars", {})
            if key in vars_:
                result.affected.append({"project": project, "profile": profile_name})

    log_event("impact_analysis", "__global__", f"key={key} affected={result.count}")
    return result


def analyze_value_impact(value: str, password: str | None = None) -> list[dict]:
    """Find all profiles across all projects that contain *value* in any var."""
    if value is None:
        raise ImpactError("value must not be None")

    hits: list[dict] = []
    for project in list_projects():
        for profile_name in list_profiles(project):
            try:
                profile = get_profile(project, profile_name, password=password)
            except Exception:
                continue
            vars_ = profile.get("vars", {})
            matching_keys = [k for k, v in vars_.items() if str(v) == value]
            if matching_keys:
                hits.append({"project": project, "profile": profile_name, "keys": matching_keys})

    log_event("impact_analysis", "__global__", f"value_scan hits={len(hits)}")
    return hits


def format_impact_report(result: ImpactResult) -> str:
    """Return a human-readable impact report."""
    lines = [f"Impact analysis for key: {result.key!r}",
             f"Affected profiles: {result.count}"]
    for entry in result.affected:
        lines.append(f"  - {entry['project']} / {entry['profile']}")
    return "\n".join(lines)
