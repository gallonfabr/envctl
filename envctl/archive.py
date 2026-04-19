"""Archive and restore entire project profiles to/from a zip bundle."""

import io
import json
import zipfile
from datetime import datetime, timezone

from envctl.storage import load_profiles, save_profiles
from envctl.audit import log_event


class ArchiveError(Exception):
    pass


def export_archive(project: str, dest_path: str) -> str:
    """Export all profiles for a project into a zip archive."""
    store = load_profiles()
    if project not in store:
        raise ArchiveError(f"Project '{project}' not found.")

    profiles = store[project]
    meta = {
        "project": project,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "profile_count": len(profiles),
    }

    with zipfile.ZipFile(dest_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("meta.json", json.dumps(meta, indent=2))
        zf.writestr("profiles.json", json.dumps(profiles, indent=2))

    log_event(project, "archive_export", {"dest": dest_path, "profiles": list(profiles.keys())})
    return dest_path


def import_archive(src_path: str, overwrite: bool = False) -> str:
    """Import profiles from a zip archive into the store."""
    if not zipfile.is_zipfile(src_path):
        raise ArchiveError(f"'{src_path}' is not a valid zip archive.")

    with zipfile.ZipFile(src_path, "r") as zf:
        try:
            meta = json.loads(zf.read("meta.json"))
            profiles = json.loads(zf.read("profiles.json"))
        except KeyError as e:
            raise ArchiveError(f"Archive missing required file: {e}")

    project = meta["project"]
    store = load_profiles()

    if project in store and not overwrite:
        raise ArchiveError(
            f"Project '{project}' already exists. Use overwrite=True to replace."
        )

    store[project] = profiles
    save_profiles(store)
    log_event(project, "archive_import", {"src": src_path, "profiles": list(profiles.keys())})
    return project
