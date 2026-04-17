"""Tests for envctl.template module."""
import pytest
from unittest.mock import patch
from envctl.template import render_template, render_profile_template, list_template_vars


def test_render_template_simple():
    result = render_template("Hello {{NAME}}", {"NAME": "world"})
    assert result == "Hello world"


def test_render_template_multiple_vars():
    tmpl = "{{HOST}}:{{PORT}}/{{DB}}"
    result = render_template(tmpl, {"HOST": "localhost", "PORT": "5432", "DB": "mydb"})
    assert result == "localhost:5432/mydb"


def test_render_template_missing_var_raises():
    with pytest.raises(KeyError, match="MISSING"):
        render_template("{{MISSING}}", {})


def test_render_template_extra_vars_ignored():
    result = render_template("{{A}}", {"A": "1", "B": "2"})
    assert result == "1"


def test_render_template_no_placeholders():
    result = render_template("plain string", {"X": "y"})
    assert result == "plain string"


def test_render_template_whitespace_in_placeholder():
    result = render_template("{{ NAME }}", {"NAME": "Alice"})
    assert result == "Alice"


def test_list_template_vars():
    tmpl = "{{A}} and {{B}} and {{A}}"
    assert list_template_vars(tmpl) == ["A", "B"]


def test_list_template_vars_empty():
    assert list_template_vars("no vars here") == []


def test_render_profile_template():
    fake_vars = {"HOST": "db.example.com", "PORT": "5432"}
    with patch("envctl.template.get_profile", return_value=fake_vars):
        result = render_profile_template("{{HOST}}:{{PORT}}", "myproject", "prod")
    assert result == "db.example.com:5432"


def test_render_profile_template_missing_var():
    fake_vars = {"HOST": "db.example.com"}
    with patch("envctl.template.get_profile", return_value=fake_vars):
        with pytest.raises(KeyError):
            render_profile_template("{{HOST}}:{{PORT}}", "myproject", "prod")
