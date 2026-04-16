"""Tests for envctl.export module."""

import json
import os
import pytest

from envctl.export import export_profile, import_profile
from envctl.storage import load_profiles, save_profiles


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    store = tmp_path / "profiles.json"
    monkeypatch.setenv("ENVCTL_STORE", str(store))
    save_profiles({})
    yield


@pytest.fixture
def plain_profile():
    profiles = {
        "myapp": {
            "dev": {"encrypted": False, "vars": {"HOST": "localhost", "PORT": "8080"}}
        }
    }
    save_profiles(profiles)


def test_export_env_format(tmp_path, plain_profile):
    out = tmp_path / "dev.env"
    export_profile("myapp", "dev", str(out), fmt="env")
    content = out.read_text()
    assert "HOST=localhost" in content
    assert "PORT=8080" in content


def test_export_json_format(tmp_path, plain_profile):
    out = tmp_path / "dev.json"
    export_profile("myapp", "dev", str(out), fmt="json")
    data = json.loads(out.read_text())
    assert data == {"HOST": "localhost", "PORT": "8080"}


def test_export_missing_profile(tmp_path):
    with pytest.raises(KeyError):
        export_profile("myapp", "missing", str(tmp_path / "out.env"))


def test_export_unsupported_format(tmp_path, plain_profile):
    with pytest.raises(ValueError, match="Unsupported format"):
        export_profile("myapp", "dev", str(tmp_path / "out.xml"), fmt="xml")


def test_export_encrypted_profile_raises(tmp_path):
    profiles = {
        "myapp": {"prod": {"encrypted": True, "salt": "abc", "vars": {}}}
    }
    save_profiles(profiles)
    with pytest.raises(ValueError, match="encrypted"):
        export_profile("myapp", "prod", str(tmp_path / "out.env"))


def test_import_env_format(tmp_path):
    env_file = tmp_path / "vars.env"
    env_file.write_text("DB_HOST=db.local\nDB_PORT=5432\n# comment\n")
    import_profile("myapp", "staging", str(env_file), fmt="env")
    profiles = load_profiles()
    assert profiles["myapp"]["staging"]["vars"] == {"DB_HOST": "db.local", "DB_PORT": "5432"}


def test_import_json_format(tmp_path):
    json_file = tmp_path / "vars.json"
    json_file.write_text(json.dumps({"KEY": "value"}))
    import_profile("myapp", "prod", str(json_file), fmt="json")
    profiles = load_profiles()
    assert profiles["myapp"]["prod"]["vars"] == {"KEY": "value"}


def test_import_auto_detect_format(tmp_path):
    json_file = tmp_path / "vars.json"
    json_file.write_text(json.dumps({"AUTO": "yes"}))
    import_profile("myapp", "auto", str(json_file))
    profiles = load_profiles()
    assert profiles["myapp"]["auto"]["vars"]["AUTO"] == "yes"


def test_import_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        import_profile("myapp", "dev", str(tmp_path / "nonexistent.env"))


def test_import_invalid_env_line(tmp_path):
    bad_file = tmp_path / "bad.env"
    bad_file.write_text("INVALID_LINE_NO_EQUALS\n")
    with pytest.raises(ValueError, match="Invalid line"):
        import_profile("myapp", "dev", str(bad_file), fmt="env")
