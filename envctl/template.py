"""Template rendering for environment variable profiles."""
from __future__ import annotations
import re
from typing import Dict, Optional
from envctl.profile import get_profile

VAR_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def render_template(template: str, vars: Dict[str, str]) -> str:
    """Replace {{VAR}} placeholders with values from vars dict."""
    def replacer(match: re.Match) -> str:
        key = match.group(1)
        if key not in vars:
            raise KeyError(f"Template variable '{key}' not found in profile")
        return vars[key]

    return VAR_PATTERN.sub(replacer, template)


def render_profile_template(
    template: str,
    project: str,
    profile: str,
    password: Optional[str] = None,
) -> str:
    """Load a profile and render a template string with its variables."""
    vars = get_profile(project, profile, password=password)
    return render_template(template, vars)


def list_template_vars(template: str) -> list[str]:
    """Return list of unique variable names referenced in a template."""
    return list(dict.fromkeys(VAR_PATTERN.findall(template)))
