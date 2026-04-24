"""Tests for envctl.archive module."""

import json
import os
import zipfile
import pytest
from unittest.mock import patch

from envctl.archive import export_archive, import_archive, ArchiveError


SAMPLE_STORE = {
    "myproject": {
        "dev": {"vars": {"DEBUG": "1", "HOST": "localhost"}, "encrypted": False},
        "prod": {"vars": {"DEBUG": "0", "HOST": "example.com"}, "encrypted": False},
    }
}


@pytest.fixture()
def patch_deps(tmp_path):
    store = {k: dict(v) for k, v in SAMPLE_STORE.items()}
    with (
        patch("envctl.archive.load_profiles", return_value=store),
        patch("envctl.archive.save_profiles") as mock_save,
        patch("envctl.archive.log_event"),
    ):
        yield tmp_path, store, mock_save


def test_export_creates_zip(patch_deps):
    tmp_path, store, _ = patch_deps
    dest = str(tmp_path / "backup.zip")
    result = export_archive("myproject", dest)
    assert result == dest
    assert zipfile.is_zipfile(dest)


def test_export_zip_contains_expected_files(patch_deps):
    tmp_path, store, _ = patch_deps
    dest = str(tmp_path / "backup.zip")
    export_archive("myproject", dest)
    with zipfile.ZipFile(dest) as zf:
        names = zf.namelist()
    assert "meta.json" in names
    assert "profiles.json" in names


def test_export_meta_content(patch_deps):
    tmp_path, store, _ = patch_deps
    dest = str(tmp_path / "backup.zip")
    export_archive("myproject", dest)
    with zipfile.ZipFile(dest) as zf:
        meta = json.loads(zf.read("meta.json"))
    assert meta["project"] == "myproject"
    assert meta["profile_count"] == 2


def test_export_profiles_content(patch_deps):
    """Verify that profiles.json inside the archive matches the exported project data."""
    tmp_path, store, _ = patch_deps
    dest = str(tmp_path / "backup.zip")
    export_archive("myproject", dest)
    with zipfile.ZipFile(dest) as zf:
        profiles = json.loads(zf.read("profiles.json"))
    assert "dev" in profiles
    assert "prod" in profiles
    assert profiles["dev"]["vars"]["DEBUG"] == "1"
    assert profiles["prod"]["vars"]["HOST"] == "example.com"


def test_export_missing_project_raises(patch_deps):
    tmp_path, store, _ = patch_deps
    with pytest.raises(ArchiveError, match="not found"):
        export_archive("ghost", str(tmp_path / "out.zip"))


def test_import_restores_profiles(patch_deps):
    tmp_path, store, mock_save = patch_deps
    dest = str(tmp_path / "backup.zip")
    export_archive("myproject", dest)

    empty_store = {}
    with patch("envctl.archive.load_profiles", return_value=empty_store):
        with patch("envctl.archive.save_profiles") as ms:
            with patch("envctl.archive.log_event"):
                project = import_archive(dest)
    assert project == "myproject"
    assert "dev" in empty_store["myproject"]


def test_import_overwrite_false_raises_on_existing(patch_deps):
    tmp_path, store, _ = patch_deps
    dest = str(tmp_path / "backup.zip")
    export_archive("myproject", dest)
    with pytest.raises(ArchiveError, match="already exists"):
        with patch("envctl.archive.load_profiles", return_value={"myproject": {}}):
            with patch("envctl.archive.log_event"):
                import_archive(dest, overwrite=False)


def test_import_invalid_zip_raises(tmp_path):
    bad = tmp_path / "bad.zip"
    bad.write_text("not a zip")
    with pytest.raises(ArchiveError, match="valid zip"):
        import_archive(str(bad))
