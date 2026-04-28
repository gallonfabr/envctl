"""Tests for envctl.quota_ceiling."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from envctl.quota_ceiling import (
    check_var_ceiling,
    check_project_quota,
    enforce_var_ceiling,
    enforce_project_quota,
    QuotaCeilingError,
)
from envctl.quota import QuotaError


PROJECT = "myproject"
PROFILE = "staging"


def _patch(ceiling=None, quota_raises=False, current_vars=None):
    """Return a context-manager stack that patches the three dependencies."""
    profiles_data = {PROFILE: {"vars": current_vars or {}}}
    patches = [
        patch("envctl.quota_ceiling.get_ceiling", return_value=ceiling),
        patch("envctl.quota_ceiling.load_profiles", return_value=profiles_data),
    ]
    if quota_raises:
        patches.append(
            patch(
                "envctl.quota_ceiling.check_quota",
                side_effect=QuotaError("quota exceeded"),
            )
        )
    else:
        patches.append(patch("envctl.quota_ceiling.check_quota", return_value=None))
    return patches


def _apply(patches):
    started = [p.start() for p in patches]
    return started, patches


def _stop(patches):
    for p in patches:
        p.stop()


# --- check_var_ceiling ---

def test_no_ceiling_always_allowed():
    ps = _patch(ceiling=None, current_vars={"A": "1", "B": "2"})
    _, ps = _apply(ps)
    try:
        result = check_var_ceiling(PROJECT, PROFILE, 99)
        assert result.allowed is True
        assert result.reason is None
    finally:
        _stop(ps)


def test_under_ceiling_allowed():
    ps = _patch(ceiling=5, current_vars={"A": "1"})
    _, ps = _apply(ps)
    try:
        result = check_var_ceiling(PROJECT, PROFILE, 3)
        assert result.allowed is True
    finally:
        _stop(ps)


def test_at_ceiling_denied():
    ps = _patch(ceiling=3, current_vars={"A": "1", "B": "2", "C": "3"})
    _, ps = _apply(ps)
    try:
        result = check_var_ceiling(PROJECT, PROFILE, 1)
        assert result.allowed is False
        assert "ceiling of 3" in result.reason
    finally:
        _stop(ps)


def test_exceeds_ceiling_denied():
    ps = _patch(ceiling=4, current_vars={"A": "1", "B": "2", "C": "3"})
    _, ps = _apply(ps)
    try:
        result = check_var_ceiling(PROJECT, PROFILE, 2)
        assert result.allowed is False
    finally:
        _stop(ps)


def test_missing_profile_raises():
    with patch("envctl.quota_ceiling.get_ceiling", return_value=5), \
         patch("envctl.quota_ceiling.load_profiles", return_value={}):
        with pytest.raises(QuotaCeilingError, match="not found"):
            check_var_ceiling(PROJECT, "ghost", 1)


# --- check_project_quota ---

def test_quota_ok():
    ps = _patch(quota_raises=False)
    _, ps = _apply(ps)
    try:
        result = check_project_quota(PROJECT)
        assert result.allowed is True
    finally:
        _stop(ps)


def test_quota_exceeded():
    ps = _patch(quota_raises=True)
    _, ps = _apply(ps)
    try:
        result = check_project_quota(PROJECT)
        assert result.allowed is False
        assert "quota exceeded" in result.reason
    finally:
        _stop(ps)


# --- enforce helpers ---

def test_enforce_var_ceiling_raises_on_violation():
    ps = _patch(ceiling=1, current_vars={"A": "1"})
    _, ps = _apply(ps)
    try:
        with pytest.raises(QuotaCeilingError):
            enforce_var_ceiling(PROJECT, PROFILE, 1)
    finally:
        _stop(ps)


def test_enforce_var_ceiling_passes_when_ok():
    ps = _patch(ceiling=10, current_vars={"A": "1"})
    _, ps = _apply(ps)
    try:
        enforce_var_ceiling(PROJECT, PROFILE, 3)  # should not raise
    finally:
        _stop(ps)


def test_enforce_project_quota_raises():
    ps = _patch(quota_raises=True)
    _, ps = _apply(ps)
    try:
        with pytest.raises(QuotaCeilingError):
            enforce_project_quota(PROJECT)
    finally:
        _stop(ps)
