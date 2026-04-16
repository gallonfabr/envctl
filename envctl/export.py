"""Export and import environment variable profiles to/from files."""

import json
import os
from typing import Optional

from envctl.storage import load_profiles, save_profiles


SUPPORTED_FORMATS = ("json", "env")


def export_profile(project: str, profile: str, output_path: str, fmt: str = "env") -> None:
    """Export a profile's variables to a file."""
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{fmt}'. Choose from: {SUPPORTED_FORMATS}")

    profiles = load_profiles()
    try:
        data = profiles[project][profile]
    except KeyError:
        raise KeyError(f"Profile '{profile}' not found for project '{project}'")

    if data.get("encrypted"):
        raise ValueError("Cannot export encrypted profiles directly. Decrypt first.")

    variables = data.get("vars", {})

    with open(output_path, "w") as f:
        if fmt == "json":
            json.dump(variables, f, indent=2)
            f.write("\n")
        else:  # env format
            for key, value in variables.items():
                f.write(f"{key}={value}\n")


def import_profile(project: str, profile: str, input_path: str, fmt: Optional[str] = None) -> None:
    """Import a profile's variables from a file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    if fmt is None:
        ext = os.path.splitext(input_path)[1].lstrip(".")
        fmt = ext if ext in SUPPORTED_FORMATS else "env"

    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{fmt}'. Choose from: {SUPPORTED_FORMATS}")

    with open(input_path, "r") as f:
        content = f.read()

    variables = {}
    if fmt == "json":
        variables = json.loads(content)
        if not isinstance(variables, dict):
            raise ValueError("JSON file must contain a top-level object")
    else:  # env format
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ValueError(f"Invalid line in env file: '{line}'")
            key, _, value = line.partition("=")
            variables[key.strip()] = value.strip()

    profiles = load_profiles()
    profiles.setdefault(project, {})
    profiles[project][profile] = {"encrypted": False, "vars": variables}
    save_profiles(profiles)
