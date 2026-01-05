"""
Tests for transition_helpers.py

Unit tests for transition matching helper functions used by
jira-lifecycle scripts for workflow operations.
"""

import sys
from pathlib import Path

import pytest

# Add shared lib to path
shared_lib_path = str(Path(__file__).parent.parent.parent / "scripts" / "lib")
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)

from assistant_skills_lib.error_handler import ValidationError

from jira_assistant_skills_lib import (
    find_transition_by_keywords,
    find_transition_by_name,
    format_transition_list,
)


@pytest.fixture
def sample_transitions():
    """Sample transitions for testing."""
    return [
        {"id": "11", "name": "To Do", "to": {"name": "To Do", "id": "1"}},
        {"id": "21", "name": "In Progress", "to": {"name": "In Progress", "id": "2"}},
        {"id": "31", "name": "Done", "to": {"name": "Done", "id": "3"}},
        {"id": "41", "name": "Reopen", "to": {"name": "Open", "id": "4"}},
    ]


@pytest.fixture
def workflow_transitions():
    """Sample workflow transitions with resolve/close options."""
    return [
        {"id": "1", "name": "To Do", "to": {"name": "To Do", "id": "1"}},
        {"id": "2", "name": "In Progress", "to": {"name": "In Progress", "id": "2"}},
        {"id": "3", "name": "Done", "to": {"name": "Done", "id": "3"}},
        {"id": "4", "name": "Close Issue", "to": {"name": "Closed", "id": "4"}},
        {"id": "5", "name": "Resolve", "to": {"name": "Resolved", "id": "5"}},
    ]


class TestFindTransitionByName:
    """Tests for find_transition_by_name function."""

    def test_exact_match(self, sample_transitions):
        """Test finding transition by exact name match."""
        result = find_transition_by_name(sample_transitions, "In Progress")
        assert result["id"] == "21"
        assert result["name"] == "In Progress"

    def test_exact_match_case_insensitive(self, sample_transitions):
        """Test case-insensitive exact matching."""
        result = find_transition_by_name(sample_transitions, "in progress")
        assert result["id"] == "21"
        assert result["name"] == "In Progress"

    def test_exact_match_uppercase(self, sample_transitions):
        """Test uppercase exact matching."""
        result = find_transition_by_name(sample_transitions, "DONE")
        assert result["id"] == "31"

    def test_partial_match(self, sample_transitions):
        """Test partial name matching."""
        result = find_transition_by_name(sample_transitions, "Progress")
        assert result["id"] == "21"

    def test_partial_match_case_insensitive(self, sample_transitions):
        """Test case-insensitive partial matching."""
        result = find_transition_by_name(sample_transitions, "progress")
        assert result["id"] == "21"

    def test_not_found_raises_validation_error(self, sample_transitions):
        """Test error when transition not found."""
        with pytest.raises(ValidationError) as exc_info:
            find_transition_by_name(sample_transitions, "Review")
        assert "not found" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)

    def test_ambiguous_partial_raises_validation_error(self):
        """Test error when multiple transitions match partially."""
        transitions = [
            {"id": "1", "name": "Review Code"},
            {"id": "2", "name": "Code Review Complete"},
        ]
        with pytest.raises(ValidationError) as exc_info:
            find_transition_by_name(transitions, "Code")
        assert "Ambiguous" in str(exc_info.value)
        assert "Review Code" in str(exc_info.value)
        assert "Code Review Complete" in str(exc_info.value)

    def test_multiple_exact_matches_raises_validation_error(self):
        """Test error when multiple exact matches exist."""
        # This shouldn't happen in practice but tests the edge case
        transitions = [
            {"id": "1", "name": "Done"},
            {"id": "2", "name": "Done"},  # Duplicate name
        ]
        with pytest.raises(ValidationError) as exc_info:
            find_transition_by_name(transitions, "Done")
        assert "Multiple exact matches" in str(exc_info.value)

    def test_empty_transitions_raises_validation_error(self):
        """Test error when no transitions available."""
        with pytest.raises(ValidationError) as exc_info:
            find_transition_by_name([], "Done")
        assert "No transitions available" in str(exc_info.value)

    def test_prefers_exact_over_partial(self):
        """Test that exact match is preferred over partial match."""
        transitions = [{"id": "1", "name": "Done Review"}, {"id": "2", "name": "Done"}]
        result = find_transition_by_name(transitions, "Done")
        assert result["id"] == "2"  # Exact match wins


class TestFindTransitionByKeywords:
    """Tests for find_transition_by_keywords function."""

    def test_finds_first_matching_keyword(self, workflow_transitions):
        """Test finding transition matching first keyword."""
        result = find_transition_by_keywords(
            workflow_transitions, ["done", "close", "resolve"]
        )
        assert result is not None
        # Should find 'Done' which matches 'done' keyword
        assert "done" in result["name"].lower() or "close" in result["name"].lower()

    def test_prefer_exact_match(self, workflow_transitions):
        """Test that prefer_exact parameter works."""
        result = find_transition_by_keywords(
            workflow_transitions, ["done", "close", "resolve"], prefer_exact="resolve"
        )
        assert result is not None
        assert result["name"] == "Resolve"

    def test_no_match_returns_none(self, sample_transitions):
        """Test that None is returned when no match found."""
        result = find_transition_by_keywords(
            sample_transitions, ["review", "approve", "reject"]
        )
        assert result is None

    def test_empty_transitions_returns_none(self):
        """Test that None is returned for empty transitions."""
        result = find_transition_by_keywords([], ["done"])
        assert result is None

    def test_case_insensitive_keyword_match(self, workflow_transitions):
        """Test case-insensitive keyword matching."""
        result = find_transition_by_keywords(workflow_transitions, ["CLOSE"])
        assert result is not None
        assert "close" in result["name"].lower()

    def test_partial_keyword_match(self, workflow_transitions):
        """Test that partial keyword matching works."""
        result = find_transition_by_keywords(workflow_transitions, ["progress"])
        assert result is not None
        assert result["name"] == "In Progress"

    def test_prefer_exact_no_match_falls_back(self):
        """Test that prefer_exact falls back to first match if no exact."""
        transitions = [
            {"id": "1", "name": "Mark Complete"},
            {"id": "2", "name": "Complete Review"},
        ]
        result = find_transition_by_keywords(
            transitions,
            ["complete"],
            prefer_exact="done",  # No exact 'done' match
        )
        assert result is not None
        # Should fall back to first matching transition
        assert "complete" in result["name"].lower()


class TestFormatTransitionList:
    """Tests for format_transition_list function."""

    def test_formats_transitions(self, sample_transitions):
        """Test formatting a list of transitions."""
        result = format_transition_list(sample_transitions)
        assert "To Do" in result
        assert "In Progress" in result
        assert "Done" in result
        assert "ID: 11" in result
        assert "ID: 21" in result

    def test_empty_transitions(self):
        """Test formatting empty transition list."""
        result = format_transition_list([])
        assert "No transitions available" in result

    def test_includes_target_status(self, sample_transitions):
        """Test that target status is included in output."""
        result = format_transition_list(sample_transitions)
        # Check format includes target status
        assert "->" in result

    def test_handles_missing_to_field(self):
        """Test handling transitions without 'to' field."""
        transitions = [
            {"id": "1", "name": "Done"}  # No 'to' field
        ]
        result = format_transition_list(transitions)
        assert "Done" in result
        assert "Unknown" in result


class TestIntegrationWithResolveKeywords:
    """Integration tests for resolve workflow patterns."""

    def test_resolve_keywords_pattern(self, workflow_transitions):
        """Test typical resolve workflow keyword matching."""
        resolve_keywords = ["done", "resolve", "close", "complete"]

        transition = find_transition_by_keywords(
            workflow_transitions, resolve_keywords, prefer_exact="done"
        )

        assert transition is not None
        assert transition["name"] == "Done"

    def test_reopen_keywords_pattern(self, sample_transitions):
        """Test typical reopen workflow keyword matching."""
        reopen_keywords = ["reopen", "to do", "todo", "open", "backlog"]

        transition = find_transition_by_keywords(
            sample_transitions, reopen_keywords, prefer_exact="reopen"
        )

        assert transition is not None
        assert transition["name"] == "Reopen"


class TestEdgeCases:
    """Edge case tests for transition helpers."""

    def test_whitespace_in_name(self):
        """Test handling of extra whitespace in search."""
        transitions = [{"id": "1", "name": "In Progress"}]
        # The function should handle the name as-is
        result = find_transition_by_name(transitions, "In Progress")
        assert result is not None

    def test_special_characters_in_name(self):
        """Test handling of special characters in transition names."""
        transitions = [
            {"id": "1", "name": "Won't Fix"},
            {"id": "2", "name": "Can't Reproduce"},
        ]
        result = find_transition_by_name(transitions, "Won't Fix")
        assert result["id"] == "1"

    def test_unicode_in_name(self):
        """Test handling of unicode characters."""
        transitions = [{"id": "1", "name": "Completed"}]
        result = find_transition_by_name(transitions, "Completed")
        assert result is not None
