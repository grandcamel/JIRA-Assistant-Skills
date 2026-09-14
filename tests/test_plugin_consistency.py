"""
Offline consistency checks for the shipped plugin (review fix, JAS-55).

No external dependencies beyond what CI already installs for the offline
suite (pytest, pyyaml): no `jira-as` CLI, no Claude Code, no network. This
is the "~10-line schema/consistency test" the independent review asked
for, so that criteria 1 (skill under twenty lines, names the dependency
range) and 8 (manifests agree on one version) cannot silently regress --
nothing else in the offline suite validates skills/jira/SKILL.md's
frontmatter or the manifests agreeing.
"""

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = REPO_ROOT / "skills" / "jira" / "SKILL.md"

MAX_NON_BLANK_LINES = 20
REQUIRED_DEPENDENCY_RANGE = "jira-as>=2,<3"


def _read_skill_md() -> tuple[dict, str]:
    """Return (parsed frontmatter, full raw file text) for skills/jira/SKILL.md."""
    text = SKILL_MD.read_text()
    assert text.startswith("---\n"), (
        "skills/jira/SKILL.md must start with YAML frontmatter (---)"
    )
    _, _, rest = text.partition("---\n")
    frontmatter_text, sep, _ = rest.partition("\n---")
    assert sep, "skills/jira/SKILL.md frontmatter is never closed with ---"
    frontmatter = yaml.safe_load(frontmatter_text)
    return frontmatter, text


def test_skill_frontmatter_parses_and_names_jira():
    """skills/jira/SKILL.md's frontmatter parses and names the skill 'jira'."""
    frontmatter, _ = _read_skill_md()
    assert isinstance(frontmatter, dict)
    assert frontmatter.get("name") == "jira"


def test_skill_is_at_most_twenty_non_blank_lines():
    """
    The whole file (frontmatter included) has at most twenty non-blank
    lines -- the harshest reading of criterion 1's "under twenty technical
    lines", counted with the frontmatter rather than excluding it.
    """
    _, text = _read_skill_md()
    non_blank = [line for line in text.splitlines() if line.strip()]
    assert len(non_blank) <= MAX_NON_BLANK_LINES, (
        f"skills/jira/SKILL.md has {len(non_blank)} non-blank lines "
        f"(frontmatter included); expected at most {MAX_NON_BLANK_LINES}"
    )


def test_skill_names_the_dependency_range():
    """The skill names the jira-as major-version range it requires."""
    _, text = _read_skill_md()
    assert REQUIRED_DEPENDENCY_RANGE in text


def _pyproject_version(text: str) -> str:
    """
    Minimal extraction of [project].version without a TOML parser
    dependency: tomllib is Python 3.11+ only, and this repo's CI matrix
    still tests 3.10.
    """
    in_project = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_project = stripped == "[project]"
            continue
        if in_project and stripped.startswith("version"):
            _, _, value = stripped.partition("=")
            return value.strip().strip('"').strip("'")
    raise AssertionError("pyproject.toml: no version = ... found under [project]")


def _manifest_versions() -> dict[str, str]:
    """Read every manifest's version field, by name, for comparison."""
    version_file = (REPO_ROOT / "VERSION").read_text().strip()

    manifest = json.loads((REPO_ROOT / ".release-please-manifest.json").read_text())
    manifest_version = manifest["."]

    pyproject_version = _pyproject_version((REPO_ROOT / "pyproject.toml").read_text())

    plugin_json = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    plugin_version = plugin_json["version"]

    marketplace = json.loads(
        (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text()
    )
    marketplace_metadata_version = marketplace["metadata"]["version"]
    marketplace_plugin_version = marketplace["plugins"][0]["version"]

    return {
        "VERSION": version_file,
        ".release-please-manifest.json": manifest_version,
        "pyproject.toml": pyproject_version,
        ".claude-plugin/plugin.json": plugin_version,
        ".claude-plugin/marketplace.json (metadata)": marketplace_metadata_version,
        ".claude-plugin/marketplace.json (plugins[0])": marketplace_plugin_version,
    }


def test_manifests_agree_on_one_version():
    """VERSION, the release-please manifest, pyproject.toml, plugin.json
    and both version fields of marketplace.json must all agree."""
    versions = _manifest_versions()
    unique = set(versions.values())
    assert len(unique) == 1, f"manifest versions disagree: {versions}"
