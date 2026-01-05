"""
Unit tests for project_context module.

Tests the project context loader, caching, merging, and helper functions
for lazy loading project metadata, workflows, patterns, and defaults.
"""

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add lib path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "lib"))

from jira_assistant_skills_lib import (
    ProjectContext,
    clear_context_cache,
    format_context_summary,
    get_common_labels,
    get_defaults_for_issue_type,
    get_statuses_for_issue_type,
    get_valid_transitions,
    suggest_assignee,
    validate_transition,
)
from jira_assistant_skills_lib.project_context import (
    _deep_merge,
    load_json_file,
    merge_contexts,
)


@pytest.fixture
def temp_skill_dir():
    """Create a temporary skill directory structure."""
    temp_dir = tempfile.mkdtemp(prefix="skill_test_")
    skill_dir = Path(temp_dir) / "skills" / "jira-project-TESTPROJ"
    skill_dir.mkdir(parents=True)
    (skill_dir / "context").mkdir()

    yield skill_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_metadata():
    """Sample metadata.json content."""
    return {
        "project_key": "TESTPROJ",
        "project_name": "Test Project",
        "discovered_at": "2025-12-26T10:30:00Z",
        "issue_types": [
            {"id": "10001", "name": "Bug", "subtask": False},
            {"id": "10002", "name": "Story", "subtask": False},
            {"id": "10003", "name": "Task", "subtask": False},
        ],
        "components": [
            {"id": "10100", "name": "Backend", "lead": "john@example.com"},
            {"id": "10101", "name": "Frontend"},
        ],
        "versions": [
            {"id": "10200", "name": "v1.0.0", "released": True, "archived": False},
            {"id": "10201", "name": "v2.0.0", "released": False, "archived": False},
        ],
        "priorities": [
            {"id": "1", "name": "Highest"},
            {"id": "2", "name": "High"},
            {"id": "3", "name": "Medium"},
        ],
        "assignable_users": [
            {
                "account_id": "user1",
                "display_name": "John Doe",
                "email": "john@example.com",
            },
            {
                "account_id": "user2",
                "display_name": "Jane Smith",
                "email": "jane@example.com",
            },
        ],
    }


@pytest.fixture
def sample_workflows():
    """Sample workflows.json content."""
    return {
        "project_key": "TESTPROJ",
        "discovered_at": "2025-12-26T10:30:00Z",
        "by_issue_type": {
            "Bug": {
                "statuses": [
                    {"id": "1", "name": "Open", "category": "TO_DO"},
                    {"id": "3", "name": "In Progress", "category": "IN_PROGRESS"},
                    {"id": "5", "name": "Done", "category": "DONE"},
                ],
                "transitions": {
                    "Open": [
                        {
                            "id": "11",
                            "name": "Start Progress",
                            "to_status": "In Progress",
                        }
                    ],
                    "In Progress": [
                        {"id": "21", "name": "Done", "to_status": "Done"},
                        {"id": "22", "name": "Reopen", "to_status": "Open"},
                    ],
                    "Done": [],
                },
            }
        },
    }


@pytest.fixture
def sample_patterns():
    """Sample patterns.json content."""
    return {
        "project_key": "TESTPROJ",
        "sample_size": 50,
        "sample_period_days": 30,
        "discovered_at": "2025-12-26T10:30:00Z",
        "by_issue_type": {
            "Bug": {
                "issue_count": 30,
                "assignees": {
                    "user1": {
                        "display_name": "John Doe",
                        "count": 20,
                        "percentage": 66.7,
                    },
                    "user2": {
                        "display_name": "Jane Smith",
                        "count": 10,
                        "percentage": 33.3,
                    },
                },
                "labels": {"backend": 15, "urgent": 8, "regression": 5},
                "components": {"Backend": 25, "Frontend": 5},
                "priorities": {
                    "High": {"count": 20, "percentage": 66.7},
                    "Medium": {"count": 10, "percentage": 33.3},
                },
            }
        },
        "common_labels": ["backend", "frontend", "urgent"],
        "top_assignees": [
            {
                "account_id": "user1",
                "display_name": "John Doe",
                "total_assignments": 35,
            },
            {
                "account_id": "user2",
                "display_name": "Jane Smith",
                "total_assignments": 15,
            },
        ],
    }


@pytest.fixture
def sample_defaults():
    """Sample defaults.json content."""
    return {
        "project_key": "TESTPROJ",
        "description": "Team defaults for TESTPROJ",
        "by_issue_type": {
            "Bug": {
                "priority": "High",
                "labels": ["needs-triage"],
                "components": ["Backend"],
            },
            "Story": {"story_points": 3, "labels": ["needs-refinement"]},
        },
        "global": {"labels": ["team-alpha"]},
    }


@pytest.mark.unit
class TestProjectContext:
    """Tests for ProjectContext dataclass."""

    def test_empty_context(self):
        """Test empty ProjectContext."""
        ctx = ProjectContext(project_key="PROJ")
        assert ctx.project_key == "PROJ"
        assert ctx.metadata == {}
        assert ctx.workflows == {}
        assert ctx.patterns == {}
        assert ctx.defaults == {}
        assert ctx.source == "none"
        assert ctx.has_context() is False

    def test_context_with_data(self, sample_metadata):
        """Test ProjectContext with data."""
        ctx = ProjectContext(
            project_key="PROJ", metadata=sample_metadata, source="skill"
        )
        assert ctx.has_context() is True
        assert len(ctx.get_issue_types()) == 3
        assert len(ctx.get_components()) == 2
        assert len(ctx.get_versions()) == 2
        assert len(ctx.get_priorities()) == 3
        assert len(ctx.get_assignable_users()) == 2

    def test_get_issue_types(self, sample_metadata):
        """Test get_issue_types method."""
        ctx = ProjectContext(project_key="PROJ", metadata=sample_metadata)
        types = ctx.get_issue_types()
        assert len(types) == 3
        type_names = [t["name"] for t in types]
        assert "Bug" in type_names
        assert "Story" in type_names


@pytest.mark.unit
class TestLoadJsonFile:
    """Tests for load_json_file function."""

    def test_load_existing_file(self, tmp_path):
        """Test loading existing JSON file."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value"}')
        result = load_json_file(json_file)
        assert result == {"key": "value"}

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading non-existent file returns None."""
        result = load_json_file(tmp_path / "nonexistent.json")
        assert result is None

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON returns None."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("not valid json")
        result = load_json_file(json_file)
        assert result is None


@pytest.mark.unit
class TestDeepMerge:
    """Tests for _deep_merge function."""

    def test_simple_merge(self):
        """Test simple dict merge."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        """Test nested dict merge."""
        base = {"a": {"x": 1, "y": 2}, "b": 1}
        override = {"a": {"y": 3, "z": 4}}
        result = _deep_merge(base, override)
        assert result == {"a": {"x": 1, "y": 3, "z": 4}, "b": 1}

    def test_list_override(self):
        """Test list is overridden, not merged."""
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        result = _deep_merge(base, override)
        assert result == {"items": [4, 5]}


@pytest.mark.unit
class TestMergeContexts:
    """Tests for merge_contexts function."""

    def test_both_none(self):
        """Test merge with both None."""
        result, source = merge_contexts(None, None)
        assert result == {}
        assert source == "none"

    def test_skill_only(self, sample_metadata):
        """Test merge with only skill context."""
        skill_ctx = {"metadata": sample_metadata}
        result, source = merge_contexts(skill_ctx, None)
        assert result == skill_ctx
        assert source == "skill"

    def test_settings_only(self, sample_defaults):
        """Test merge with only settings context."""
        settings_ctx = {"defaults": sample_defaults}
        result, source = merge_contexts(None, settings_ctx)
        assert result == settings_ctx
        assert source == "settings"

    def test_merged(self, sample_metadata, sample_defaults):
        """Test merge with both contexts."""
        skill_ctx = {"metadata": sample_metadata}
        settings_ctx = {"defaults": sample_defaults}
        result, source = merge_contexts(skill_ctx, settings_ctx)
        assert "metadata" in result
        assert "defaults" in result
        assert source == "merged"


@pytest.mark.unit
class TestGetDefaultsForIssueType:
    """Tests for get_defaults_for_issue_type function."""

    def test_global_defaults(self, sample_defaults):
        """Test getting global defaults."""
        ctx = ProjectContext(project_key="PROJ", defaults=sample_defaults)
        defaults = get_defaults_for_issue_type(ctx, "Unknown")
        assert defaults.get("labels") == ["team-alpha"]

    def test_type_specific_defaults(self, sample_defaults):
        """Test getting type-specific defaults merged with global."""
        ctx = ProjectContext(project_key="PROJ", defaults=sample_defaults)
        defaults = get_defaults_for_issue_type(ctx, "Bug")
        assert defaults.get("priority") == "High"
        # Labels should include both global and type-specific
        assert "needs-triage" in defaults.get("labels", [])
        assert "team-alpha" in defaults.get("labels", [])

    def test_story_points_for_story(self, sample_defaults):
        """Test story points default for Story type."""
        ctx = ProjectContext(project_key="PROJ", defaults=sample_defaults)
        defaults = get_defaults_for_issue_type(ctx, "Story")
        assert defaults.get("story_points") == 3


@pytest.mark.unit
class TestGetValidTransitions:
    """Tests for get_valid_transitions function."""

    def test_transitions_from_open(self, sample_workflows):
        """Test getting transitions from Open status."""
        ctx = ProjectContext(project_key="PROJ", workflows=sample_workflows)
        transitions = get_valid_transitions(ctx, "Bug", "Open")
        assert len(transitions) == 1
        assert transitions[0]["name"] == "Start Progress"
        assert transitions[0]["to_status"] == "In Progress"

    def test_transitions_from_in_progress(self, sample_workflows):
        """Test getting transitions from In Progress status."""
        ctx = ProjectContext(project_key="PROJ", workflows=sample_workflows)
        transitions = get_valid_transitions(ctx, "Bug", "In Progress")
        assert len(transitions) == 2
        transition_names = [t["name"] for t in transitions]
        assert "Done" in transition_names
        assert "Reopen" in transition_names

    def test_no_transitions_from_done(self, sample_workflows):
        """Test no transitions from Done status."""
        ctx = ProjectContext(project_key="PROJ", workflows=sample_workflows)
        transitions = get_valid_transitions(ctx, "Bug", "Done")
        assert transitions == []

    def test_unknown_status(self, sample_workflows):
        """Test unknown status returns empty list."""
        ctx = ProjectContext(project_key="PROJ", workflows=sample_workflows)
        transitions = get_valid_transitions(ctx, "Bug", "Unknown Status")
        assert transitions == []


@pytest.mark.unit
class TestGetStatusesForIssueType:
    """Tests for get_statuses_for_issue_type function."""

    def test_bug_statuses(self, sample_workflows):
        """Test getting statuses for Bug type."""
        ctx = ProjectContext(project_key="PROJ", workflows=sample_workflows)
        statuses = get_statuses_for_issue_type(ctx, "Bug")
        assert len(statuses) == 3
        status_names = [s["name"] for s in statuses]
        assert "Open" in status_names
        assert "In Progress" in status_names
        assert "Done" in status_names

    def test_unknown_type_returns_empty(self, sample_workflows):
        """Test unknown type returns empty list."""
        ctx = ProjectContext(project_key="PROJ", workflows=sample_workflows)
        statuses = get_statuses_for_issue_type(ctx, "Unknown")
        assert statuses == []


@pytest.mark.unit
class TestSuggestAssignee:
    """Tests for suggest_assignee function."""

    def test_suggest_for_type(self, sample_patterns):
        """Test suggesting assignee for specific type."""
        ctx = ProjectContext(project_key="PROJ", patterns=sample_patterns)
        assignee = suggest_assignee(ctx, "Bug")
        assert assignee == "user1"  # John has highest count

    def test_suggest_global(self, sample_patterns):
        """Test suggesting assignee from global top assignees."""
        ctx = ProjectContext(project_key="PROJ", patterns=sample_patterns)
        assignee = suggest_assignee(ctx)
        assert assignee == "user1"

    def test_no_patterns(self):
        """Test suggestion with no patterns."""
        ctx = ProjectContext(project_key="PROJ")
        assignee = suggest_assignee(ctx, "Bug")
        assert assignee is None


@pytest.mark.unit
class TestGetCommonLabels:
    """Tests for get_common_labels function."""

    def test_get_labels_for_type(self, sample_patterns):
        """Test getting labels for specific type."""
        ctx = ProjectContext(project_key="PROJ", patterns=sample_patterns)
        labels = get_common_labels(ctx, "Bug", limit=5)
        # Should be sorted by count: backend(15), urgent(8), regression(5)
        assert labels[0] == "backend"
        assert len(labels) == 3

    def test_get_all_labels(self, sample_patterns):
        """Test getting all labels (aggregated)."""
        ctx = ProjectContext(project_key="PROJ", patterns=sample_patterns)
        labels = get_common_labels(ctx, limit=5)
        assert "backend" in labels


@pytest.mark.unit
class TestValidateTransition:
    """Tests for validate_transition function."""

    def test_valid_transition(self, sample_workflows):
        """Test validating a valid transition."""
        ctx = ProjectContext(project_key="PROJ", workflows=sample_workflows)
        is_valid = validate_transition(ctx, "Bug", "Open", "In Progress")
        assert is_valid is True

    def test_invalid_transition(self, sample_workflows):
        """Test validating an invalid transition."""
        ctx = ProjectContext(project_key="PROJ", workflows=sample_workflows)
        is_valid = validate_transition(ctx, "Bug", "Open", "Done")
        assert is_valid is False


@pytest.mark.unit
class TestFormatContextSummary:
    """Tests for format_context_summary function."""

    def test_empty_context(self):
        """Test formatting empty context."""
        ctx = ProjectContext(project_key="PROJ")
        summary = format_context_summary(ctx)
        assert "Project: PROJ" in summary
        assert "Source: none" in summary

    def test_full_context(self, sample_metadata, sample_patterns, sample_defaults):
        """Test formatting context with all data."""
        ctx = ProjectContext(
            project_key="TESTPROJ",
            metadata=sample_metadata,
            patterns=sample_patterns,
            defaults=sample_defaults,
            source="skill",
            discovered_at="2025-12-26T10:30:00Z",
        )
        summary = format_context_summary(ctx)
        assert "Project: TESTPROJ" in summary
        assert "Source: skill" in summary
        assert "Issue Types:" in summary
        assert "Bug" in summary
        assert "Components:" in summary


@pytest.mark.unit
class TestContextCaching:
    """Tests for context caching functionality."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_context_cache()

    def test_clear_all_cache(self):
        """Test clearing all cache."""
        # Access would normally populate cache
        clear_context_cache()
        # This test just ensures no errors

    def test_clear_specific_project_cache(self):
        """Test clearing cache for specific project."""
        clear_context_cache("PROJ")
        # This test just ensures no errors
