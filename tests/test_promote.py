"""Tests for envctl.promote and envctl.cli_promote."""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from envctl.promote import promote_profile, PromoteError
from envctl.cli_promote import promote_cmd


SRC_VARS = {"API_KEY": "abc", "DEBUG": "true"}


def _patch(src_vars=SRC_VARS, dst_vars=None):
    def _get(project, profile, password=None):
        if project == "staging" and profile == "default":
            return src_vars
        if project == "production" and profile == "default":
            return dst_vars
        return None

    return patch("envctl.promote.get_profile", side_effect=_get)


@pytest.fixture()
def patch_deps():
    with _patch() as mock_get, \
         patch("envctl.promote.add_profile") as mock_add, \
         patch("envctl.promote.log_event") as mock_log:
        yield mock_get, mock_add, mock_log


def test_promote_success(patch_deps):
    _, mock_add, mock_log = patch_deps
    result = promote_profile("staging", "default", "production", "default", overwrite=True)
    assert result == SRC_VARS
    mock_add.assert_called_once_with("production", "default", SRC_VARS, password=None)
    mock_log.assert_called_once()


def test_promote_missing_src(patch_deps):
    with pytest.raises(PromoteError, match="not found"):
        promote_profile("staging", "missing", "production")


def test_promote_dst_exists_no_overwrite():
    with _patch(dst_vars={"X": "1"}), \
         patch("envctl.promote.add_profile"), \
         patch("envctl.promote.log_event"):
        with pytest.raises(PromoteError, match="already exists"):
            promote_profile("staging", "default", "production", "default", overwrite=False)


def test_promote_dst_exists_overwrite(patch_deps):
    _, mock_add, _ = patch_deps
    with patch("envctl.promote.get_profile", side_effect=lambda p, n, password=None: SRC_VARS):
        promote_profile("staging", "default", "production", "default", overwrite=True)
    # no exception raised


# CLI tests

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_promote_success(runner):
    with patch("envctl.cli_promote.promote_profile", return_value=SRC_VARS) as mock_p:
        result = runner.invoke(promote_cmd, ["run", "staging", "default", "production"])
    assert result.exit_code == 0
    assert "Promoted" in result.output
    assert "2 vars" in result.output


def test_cli_promote_error(runner):
    with patch("envctl.cli_promote.promote_profile", side_effect=PromoteError("oops")):
        result = runner.invoke(promote_cmd, ["run", "staging", "default", "production"])
    assert result.exit_code == 1
    assert "oops" in result.output


def test_cli_promote_with_dst_profile(runner):
    with patch("envctl.cli_promote.promote_profile", return_value=SRC_VARS) as mock_p:
        runner.invoke(promote_cmd, ["run", "staging", "default", "production", "--dst-profile", "v2"])
    mock_p.assert_called_once_with(
        "staging", "default", "production",
        dst_profile="v2", password=None, overwrite=False
    )
