"""Storage module for managing environment profiles on disk."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_STORE_DIR = Path.home() / ".config" / "envctl"
PROFILES_FILE = "profiles.json"


def get_store_path() -> Path:
    """Return the path to the profiles store directory."""
    store_dir = Path(os.environ.get("ENVCTL_STORE_DIR", DEFAULT_STORE_DIR))
    store_dir.mkdir(parents=True, exist_ok=True)
    return store_dir


def load_profiles() -> Dict[str, Dict[str, Dict[str, str]]]:
    """Load all profiles from disk. Returns a dict keyed by project name."""
    profiles_path = get_store_path() / PROFILES_FILE
    if not profiles_path.exists():
        return {}
    with profiles_path.open("r") as f:
        return json.load(f)


def save_profiles(profiles: Dict[str, Dict[str, Dict[str, str]]]) -> None:
    """Persist all profiles to disk."""
    profiles_path = get_store_path() / PROFILES_FILE
    with profiles_path.open("w") as f:
        json.dump(profiles, f, indent=2)


def list_projects() -> List[str]:
    """Return a list of all project names."""
    return list(load_profiles().keys())


def list_profiles(project: str) -> List[str]:
    """Return profile names for a given project."""
    profiles = load_profiles()
    return list(profiles.get(project, {}).keys())


def get_profile(project: str, profile: str) -> Optional[Dict[str, str]]:
    """Retrieve env vars for a specific project/profile combo."""
    profiles = load_profiles()
    return profiles.get(project, {}).get(profile)


def save_profile(project: str, profile: str, env_vars: Dict[str, str]) -> None:
    """Save or overwrite a profile for a project."""
    profiles = load_profiles()
    profiles.setdefault(project, {})[profile] = env_vars
    save_profiles(profiles)


def delete_profile(project: str, profile: str) -> bool:
    """Delete a profile. Returns True if deleted, False if not found."""
    profiles = load_profiles()
    if project in profiles and profile in profiles[project]:
        del profiles[project][profile]
        if not profiles[project]:
            del profiles[project]
        save_profiles(profiles)
        return True
    return False
