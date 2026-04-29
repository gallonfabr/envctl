"""Quota alert thresholds — warn when profile/var counts approach quota limits."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envctl.quota import get_quota, QuotaError
from envctl.storage import load_profiles, list_profiles


class QuotaAlertError(Exception):
    pass


@dataclass
class AlertStatus:
    project: str
    quota: int
    current: int
    threshold: float          # 0.0–1.0
    triggered: bool
    pct_used: float

    @property
    def message(self) -> str:
        if self.triggered:
            return (
                f"[WARN] {self.project}: {self.current}/{self.quota} profiles used "
                f"({self.pct_used:.0%}) — threshold {self.threshold:.0%}"
            )
        return (
            f"[OK]   {self.project}: {self.current}/{self.quota} profiles used "
            f"({self.pct_used:.0%})"
        )


def check_alert(
    project: str,
    threshold: float = 0.8,
) -> Optional[AlertStatus]:
    """Return an AlertStatus if a quota is set for *project*, else None."""
    if not 0.0 < threshold <= 1.0:
        raise QuotaAlertError("threshold must be in (0.0, 1.0]")

    quota = get_quota(project)
    if quota is None:
        return None

    current = len(list_profiles(project))
    pct = current / quota if quota else 0.0
    return AlertStatus(
        project=project,
        quota=quota,
        current=current,
        threshold=threshold,
        triggered=pct >= threshold,
        pct_used=pct,
    )


def check_all_alerts(threshold: float = 0.8) -> list[AlertStatus]:
    """Check quota alerts for every project that has a quota configured."""
    store = load_profiles()
    results: list[AlertStatus] = []
    for project in store:
        status = check_alert(project, threshold=threshold)
        if status is not None:
            results.append(status)
    return results
