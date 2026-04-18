"""Profile alias management for envctl."""

from envctl.storage import load_profiles, save_profiles


class AliasError(Exception):
    pass


def set_alias(project: str, profile: str, alias: str) -> None:
    """Set an alias for a profile."""
    store = load_profiles()
    if project not in store or profile not in store[project]:
        raise AliasError(f"Profile '{project}/{profile}' not found.")
    # Check alias not already used in this project
    for pname, pdata in store[project].items():
        if pname != profile and pdata.get("alias") == alias:
            raise AliasError(f"Alias '{alias}' already used by profile '{pname}' in project '{project}'.")
    store[project][profile]["alias"] = alias
    save_profiles(store)


def remove_alias(project: str, profile: str) -> None:
    """Remove alias from a profile."""
    store = load_profiles()
    if project not in store or profile not in store[project]:
        raise AliasError(f"Profile '{project}/{profile}' not found.")
    if "alias" not in store[project][profile]:
        raise AliasError(f"Profile '{project}/{profile}' has no alias.")
    del store[project][profile]["alias"]
    save_profiles(store)


def get_alias(project: str, profile: str) -> str | None:
    """Get alias for a profile, or None."""
    store = load_profiles()
    if project not in store or profile not in store[project]:
        raise AliasError(f"Profile '{project}/{profile}' not found.")
    return store[project][profile].get("alias")


def resolve_alias(project: str, alias: str) -> str | None:
    """Return profile name matching alias in project, or None."""
    store = load_profiles()
    if project not in store:
        return None
    for pname, pdata in store[project].items():
        if pdata.get("alias") == alias:
            return pname
    return None


def list_aliases(project: str) -> dict[str, str]:
    """Return mapping of profile -> alias for a project."""
    store = load_profiles()
    if project not in store:
        return {}
    return {
        pname: pdata["alias"]
        for pname, pdata in store[project].items()
        if "alias" in pdata
    }
