"""Tests for the watermark CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envctl.cli_watermark import watermark_cmd


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCTL_STORE", str(tmp_path / "profiles.json"))
    from envctl.storage import save_profiles
    save_profiles({"proj": {"staging": {"vars": {"X": "1"}}}})
    yield


def test_set_shows_checksum(runner):
    result = runner.invoke(watermark_cmd, ["set", "proj", "staging", "--author", "alice"])
    assert result.exit_code == 0
    assert "Watermark set" in result.output
    assert "alice" in result.output


def test_set_missing_profile_exits_1(runner):
    result = runner.invoke(watermark_cmd, ["set", "proj", "ghost", "--author", "alice"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_show_no_watermark(runner):
    result = runner.invoke(watermark_cmd, ["show", "proj", "staging"])
    assert result.exit_code == 0
    assert "No watermark" in result.output


def test_show_after_set(runner):
    runner.invoke(watermark_cmd, ["set", "proj", "staging", "--author", "bob", "--note", "v1"])
    result = runner.invoke(watermark_cmd, ["show", "proj", "staging"])
    assert "bob" in result.output
    assert "v1" in result.output


def test_verify_ok(runner):
    runner.invoke(watermark_cmd, ["set", "proj", "staging", "--author", "carol"])
    result = runner.invoke(watermark_cmd, ["verify", "proj", "staging"])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_verify_no_watermark_exits_1(runner):
    result = runner.invoke(watermark_cmd, ["verify", "proj", "staging"])
    assert result.exit_code == 1


def test_clear_removes_watermark(runner):
    runner.invoke(watermark_cmd, ["set", "proj", "staging", "--author", "dave"])
    result = runner.invoke(watermark_cmd, ["clear", "proj", "staging"])
    assert result.exit_code == 0
    assert "cleared" in result.output


def test_clear_not_set_exits_1(runner):
    result = runner.invoke(watermark_cmd, ["clear", "proj", "staging"])
    assert result.exit_code == 1
