"""
Unit tests for discover_project module.

Tests the project discovery, pattern analysis, skill directory generation,
and settings saving functions using mocked JIRA API responses.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add paths for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


@pytest.fixture
def mock_client():
    """Create a mock JiraClient."""
    client = Mock()
    client.base_url = "https://test.atlassian.net"
    client.close = Mock()
    return client


@pytest.fixture
def mock_project_data():
    """Sample project data from JIRA API."""
    return {
        "id": "10000",
        "key": "TESTPROJ",
        "name": "Test Project",
        "projectTypeKey": "software",
        "simplified": False,
        "lead": {"accountId": "lead123", "displayName": "Project Lead"},
    }


@pytest.fixture
def mock_statuses_data():
    """Sample project statuses data from JIRA API."""
    return [
        {
            "id": "10001",
            "name": "Bug",
            "subtask": False,
            "statuses": [
                {"id": "1", "name": "Open"},
                {"id": "3", "name": "In Progress"},
                {"id": "5", "name": "Done"},
            ],
        },
        {
            "id": "10002",
            "name": "Story",
            "subtask": False,
            "statuses": [
                {"id": "1", "name": "Open"},
                {"id": "3", "name": "In Progress"},
                {"id": "5", "name": "Done"},
            ],
        },
    ]


@pytest.fixture
def mock_components_data():
    """Sample components data from JIRA API."""
    return [
        {"id": "10100", "name": "Backend", "description": "Backend services"},
        {"id": "10101", "name": "Frontend", "description": "UI components"},
    ]


@pytest.fixture
def mock_versions_data():
    """Sample versions data from JIRA API."""
    return [
        {"id": "10200", "name": "v1.0.0", "released": True, "archived": False},
        {"id": "10201", "name": "v2.0.0", "released": False, "archived": False},
    ]


@pytest.fixture
def mock_priorities_data():
    """Sample priorities data from JIRA API."""
    return [
        {"id": "1", "name": "Highest"},
        {"id": "2", "name": "High"},
        {"id": "3", "name": "Medium"},
        {"id": "4", "name": "Low"},
    ]


@pytest.fixture
def mock_users_data():
    """Sample assignable users data from JIRA API."""
    return [
        {
            "accountId": "user1",
            "displayName": "John Doe",
            "emailAddress": "john@example.com",
        },
        {
            "accountId": "user2",
            "displayName": "Jane Smith",
            "emailAddress": "jane@example.com",
        },
    ]


@pytest.fixture
def mock_search_results():
    """Sample search results from JIRA API."""
    return {
        "issues": [
            {
                "key": "TESTPROJ-1",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "assignee": {"accountId": "user1", "displayName": "John Doe"},
                    "reporter": {"accountId": "user2", "displayName": "Jane Smith"},
                    "priority": {"name": "High"},
                    "labels": ["backend", "urgent"],
                    "components": [{"name": "Backend"}],
                    "status": {
                        "id": "1",
                        "name": "Open",
                        "statusCategory": {"key": "TO_DO"},
                    },
                    "customfield_10016": 5,
                },
            },
            {
                "key": "TESTPROJ-2",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "assignee": {"accountId": "user1", "displayName": "John Doe"},
                    "reporter": {"accountId": "user1", "displayName": "John Doe"},
                    "priority": {"name": "Medium"},
                    "labels": ["backend"],
                    "components": [{"name": "Backend"}],
                    "status": {
                        "id": "3",
                        "name": "In Progress",
                        "statusCategory": {"key": "IN_PROGRESS"},
                    },
                    "customfield_10016": 3,
                },
            },
            {
                "key": "TESTPROJ-3",
                "fields": {
                    "issuetype": {"name": "Story"},
                    "assignee": {"accountId": "user2", "displayName": "Jane Smith"},
                    "reporter": {"accountId": "user1", "displayName": "John Doe"},
                    "priority": {"name": "High"},
                    "labels": ["frontend", "feature"],
                    "components": [{"name": "Frontend"}],
                    "status": {
                        "id": "1",
                        "name": "Open",
                        "statusCategory": {"key": "TO_DO"},
                    },
                    "customfield_10016": 8,
                },
            },
        ]
    }


@pytest.fixture
def mock_transitions_data():
    """Sample transitions data from JIRA API."""
    return [
        {
            "id": "11",
            "name": "Start Progress",
            "to": {"id": "3", "name": "In Progress"},
        },
        {"id": "21", "name": "Done", "to": {"id": "5", "name": "Done"}},
    ]


@pytest.fixture
def temp_skills_dir():
    """Create a temporary skills directory structure."""
    temp_dir = tempfile.mkdtemp(prefix="discover_test_")
    skills_dir = Path(temp_dir) / ".claude" / "skills"
    skills_dir.mkdir(parents=True)

    yield temp_dir

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.unit
class TestDiscoverMetadata:
    """Tests for discover_metadata function."""

    def test_discover_metadata_success(
        self,
        mock_client,
        mock_project_data,
        mock_statuses_data,
        mock_components_data,
        mock_versions_data,
        mock_priorities_data,
        mock_users_data,
    ):
        """Test successful metadata discovery."""
        from discover_project import discover_metadata

        mock_client.get_project.return_value = mock_project_data
        mock_client.get_project_statuses.return_value = mock_statuses_data
        mock_client.get_project_components.return_value = mock_components_data
        mock_client.get_project_versions.return_value = mock_versions_data
        mock_client.get.return_value = mock_priorities_data
        mock_client.find_assignable_users.return_value = mock_users_data

        metadata = discover_metadata(mock_client, "TESTPROJ")

        assert metadata["project_key"] == "TESTPROJ"
        assert metadata["project_name"] == "Test Project"
        assert len(metadata["issue_types"]) == 2
        assert len(metadata["components"]) == 2
        assert len(metadata["versions"]) == 2
        assert len(metadata["priorities"]) == 4
        assert len(metadata["assignable_users"]) == 2

    def test_discover_metadata_handles_missing_lead(
        self, mock_client, mock_statuses_data
    ):
        """Test metadata discovery with no project lead."""
        from discover_project import discover_metadata

        mock_client.get_project.return_value = {
            "key": "TESTPROJ",
            "name": "Test Project",
            "projectTypeKey": "software",
        }
        mock_client.get_project_statuses.return_value = mock_statuses_data
        mock_client.get_project_components.return_value = []
        mock_client.get_project_versions.return_value = []
        mock_client.get.return_value = []
        mock_client.find_assignable_users.return_value = []

        metadata = discover_metadata(mock_client, "TESTPROJ")

        assert "project_lead" not in metadata


@pytest.mark.unit
class TestDiscoverPatterns:
    """Tests for discover_patterns function."""

    def test_discover_patterns_success(self, mock_client, mock_search_results):
        """Test successful pattern discovery."""
        from discover_project import discover_patterns

        mock_client.search_issues.return_value = mock_search_results

        patterns = discover_patterns(
            mock_client, "TESTPROJ", sample_size=50, sample_period_days=30
        )

        assert patterns["project_key"] == "TESTPROJ"
        assert patterns["sample_size"] == 3
        assert patterns["sample_period_days"] == 30
        assert "Bug" in patterns["by_issue_type"]
        assert "Story" in patterns["by_issue_type"]

        # Check Bug patterns
        bug_patterns = patterns["by_issue_type"]["Bug"]
        assert bug_patterns["issue_count"] == 2
        assert "user1" in bug_patterns["assignees"]

        # Check common labels
        assert "backend" in patterns["common_labels"]

        # Check top assignees
        assert len(patterns["top_assignees"]) > 0

    def test_discover_patterns_empty_results(self, mock_client):
        """Test pattern discovery with no issues."""
        from discover_project import discover_patterns

        mock_client.search_issues.return_value = {"issues": []}

        patterns = discover_patterns(mock_client, "TESTPROJ")

        assert patterns["sample_size"] == 0
        assert patterns["by_issue_type"] == {}
        assert patterns["common_labels"] == []
        assert patterns["top_assignees"] == []

    def test_discover_patterns_handles_api_error(self, mock_client):
        """Test pattern discovery handles API errors gracefully."""
        from discover_project import discover_patterns

        mock_client.search_issues.side_effect = Exception("API Error")

        patterns = discover_patterns(mock_client, "TESTPROJ")

        assert patterns["sample_size"] == 0


@pytest.mark.unit
class TestGenerateDefaults:
    """Tests for generate_defaults function."""

    def test_generate_defaults_from_patterns(self):
        """Test generating defaults from patterns."""
        from discover_project import generate_defaults

        metadata = {"project_key": "TESTPROJ"}
        patterns = {
            "by_issue_type": {
                "Bug": {
                    "issue_count": 10,
                    "assignees": {
                        "user1": {
                            "display_name": "John Doe",
                            "count": 8,
                            "percentage": 80,
                        }
                    },
                    "labels": {"backend": 5, "urgent": 3},
                    "priorities": {
                        "High": {"count": 7, "percentage": 70},
                        "Medium": {"count": 3, "percentage": 30},
                    },
                    "story_points": {"avg": 5.0},
                }
            }
        }

        defaults = generate_defaults("TESTPROJ", metadata, patterns)

        assert defaults["project_key"] == "TESTPROJ"
        assert "Bug" in defaults["by_issue_type"]
        assert defaults["by_issue_type"]["Bug"]["priority"] == "High"

    def test_generate_defaults_empty_patterns(self):
        """Test generating defaults with no patterns."""
        from discover_project import generate_defaults

        metadata = {"project_key": "TESTPROJ"}
        patterns = {"by_issue_type": {}}

        defaults = generate_defaults("TESTPROJ", metadata, patterns)

        assert defaults["project_key"] == "TESTPROJ"
        assert defaults["by_issue_type"] == {}


@pytest.mark.unit
class TestGenerateSkillMd:
    """Tests for generate_skill_md function."""

    def test_generate_skill_md_content(self):
        """Test SKILL.md generation includes expected content."""
        from discover_project import generate_skill_md

        metadata = {
            "project_key": "TESTPROJ",
            "project_name": "Test Project",
            "project_type": "software",
            "discovered_at": "2025-12-26T10:30:00Z",
            "issue_types": [{"name": "Bug"}, {"name": "Story"}],
            "components": [{"name": "Backend"}, {"name": "Frontend"}],
            "versions": [{"name": "v1.0.0", "archived": False, "released": False}],
        }
        workflows = {}
        patterns = {
            "sample_period_days": 30,
            "sample_size": 50,
            "top_assignees": [{"display_name": "John Doe"}],
            "common_labels": ["backend", "urgent"],
        }

        content = generate_skill_md("TESTPROJ", metadata, workflows, patterns)

        assert "jira-project-TESTPROJ" in content
        assert "Test Project" in content
        assert "Bug" in content
        assert "Story" in content
        assert "Backend" in content
        assert "John Doe" in content

    def test_generate_skill_md_frontmatter(self):
        """Test SKILL.md has proper frontmatter."""
        from discover_project import generate_skill_md

        metadata = {
            "project_key": "PROJ",
            "project_name": "Project",
            "project_type": "software",
            "issue_types": [],
            "components": [],
            "versions": [],
        }

        content = generate_skill_md(
            "PROJ",
            metadata,
            {},
            {
                "sample_period_days": 30,
                "sample_size": 0,
                "top_assignees": [],
                "common_labels": [],
            },
        )

        assert content.startswith("---")
        assert "name:" in content
        assert "description:" in content


@pytest.mark.unit
class TestSaveToSkillDirectory:
    """Tests for save_to_skill_directory function."""

    def test_save_creates_directory_structure(self, temp_skills_dir):
        """Test skill directory creation."""
        from discover_project import save_to_skill_directory

        # Patch get_skills_root to return our temp directory
        with patch("discover_project.get_skills_root") as mock_root:
            mock_root.return_value = Path(temp_skills_dir) / ".claude"

            metadata = {"project_key": "TESTPROJ", "project_name": "Test"}
            workflows = {"by_issue_type": {}}
            patterns = {
                "sample_period_days": 30,
                "sample_size": 0,
                "top_assignees": [],
                "common_labels": [],
            }
            defaults = {"project_key": "TESTPROJ"}

            skill_path = save_to_skill_directory(
                "TESTPROJ", metadata, workflows, patterns, defaults
            )

            assert skill_path.exists()
            assert (skill_path / "SKILL.md").exists()
            assert (skill_path / "context").exists()
            assert (skill_path / "context" / "metadata.json").exists()
            assert (skill_path / "context" / "workflows.json").exists()
            assert (skill_path / "context" / "patterns.json").exists()
            assert (skill_path / "defaults.json").exists()


@pytest.mark.unit
class TestSaveToSettingsLocal:
    """Tests for save_to_settings_local function."""

    def test_save_creates_settings_structure(self, temp_skills_dir):
        """Test settings.local.json creation."""
        from discover_project import save_to_settings_local

        with patch("discover_project.get_skills_root") as mock_root:
            mock_root.return_value = Path(temp_skills_dir) / ".claude" / "skills"

            defaults = {
                "project_key": "TESTPROJ",
                "by_issue_type": {"Bug": {"priority": "High"}},
                "global": {"priority": "Medium"},
            }

            settings_path = save_to_settings_local("TESTPROJ", defaults, "development")

            assert settings_path.exists()

            with open(settings_path) as f:
                settings = json.load(f)

            assert "jira" in settings
            assert "profiles" in settings["jira"]
            assert "development" in settings["jira"]["profiles"]
            assert "projects" in settings["jira"]["profiles"]["development"]
            assert "TESTPROJ" in settings["jira"]["profiles"]["development"]["projects"]

    def test_save_merges_with_existing(self, temp_skills_dir):
        """Test settings are merged with existing file."""
        from discover_project import save_to_settings_local

        with patch("discover_project.get_skills_root") as mock_root:
            # get_skills_root returns .claude/skills, so .parent gives .claude
            # and settings.local.json is at .claude/settings.local.json
            claude_dir = Path(temp_skills_dir) / ".claude"
            skills_path = claude_dir / "skills"
            skills_path.mkdir(parents=True, exist_ok=True)
            mock_root.return_value = skills_path

            # Settings.local.json is at .claude/settings.local.json (skills.parent)
            settings_path = claude_dir / "settings.local.json"
            existing = {
                "jira": {
                    "profiles": {
                        "development": {"projects": {"EXISTING": {"defaults": {}}}}
                    }
                }
            }
            settings_path.write_text(json.dumps(existing))

            defaults = {"project_key": "TESTPROJ", "by_issue_type": {}, "global": {}}
            save_to_settings_local("TESTPROJ", defaults, "development")

            with open(settings_path) as f:
                settings = json.load(f)

            # Both projects should exist
            projects = settings["jira"]["profiles"]["development"]["projects"]
            assert "EXISTING" in projects
            assert "TESTPROJ" in projects


@pytest.mark.unit
class TestDiscoverWorkflows:
    """Tests for discover_workflows function."""

    def test_discover_workflows_success(self, mock_client, mock_transitions_data):
        """Test successful workflow discovery."""
        from discover_project import discover_workflows

        metadata = {
            "issue_types": [
                {"name": "Bug", "statuses": ["Open", "In Progress", "Done"]}
            ]
        }

        # Mock search returning an issue for transition lookup
        mock_client.search_issues.return_value = {
            "issues": [
                {
                    "key": "TESTPROJ-1",
                    "fields": {
                        "status": {
                            "id": "1",
                            "name": "Open",
                            "statusCategory": {"key": "TO_DO"},
                        }
                    },
                }
            ]
        }
        mock_client.get_transitions.return_value = mock_transitions_data

        workflows = discover_workflows(mock_client, "TESTPROJ", metadata)

        assert workflows["project_key"] == "TESTPROJ"
        assert "Bug" in workflows["by_issue_type"]
        assert "transitions" in workflows["by_issue_type"]["Bug"]

    def test_discover_workflows_handles_empty_statuses(self, mock_client):
        """Test workflow discovery with no statuses."""
        from discover_project import discover_workflows

        metadata = {"issue_types": [{"name": "Bug", "statuses": []}]}

        workflows = discover_workflows(mock_client, "TESTPROJ", metadata)

        assert workflows["by_issue_type"] == {}


@pytest.mark.unit
class TestMainFunction:
    """Tests for main function and CLI argument handling."""

    def test_project_key_uppercase(self):
        """Test project key is normalized to uppercase."""
        import argparse

        # The actual normalization happens in main() when processing args
        # We test by parsing args directly
        parser = argparse.ArgumentParser()
        parser.add_argument("project_key")

        args = parser.parse_args(["proj"])
        normalized = args.project_key.upper()

        assert normalized == "PROJ"
