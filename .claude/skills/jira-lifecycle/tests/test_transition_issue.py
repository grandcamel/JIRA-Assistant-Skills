"""
Tests for transition_issue.py

TDD tests for transitioning issues through workflow states,
including the new sprint integration feature.
"""

import pytest
from unittest.mock import Mock, patch

# Import the module under test
import transition_issue
from transition_issue import find_transition_by_name, transition_issue as do_transition
from error_handler import ValidationError


class TestFindTransitionByName:
    """Tests for transition name matching logic."""

    def test_exact_match(self, sample_transitions):
        """Test finding transition by exact name match."""
        result = find_transition_by_name(sample_transitions, "In Progress")
        assert result['id'] == "21"
        assert result['name'] == "In Progress"

    def test_case_insensitive_match(self, sample_transitions):
        """Test case-insensitive matching."""
        result = find_transition_by_name(sample_transitions, "in progress")
        assert result['id'] == "21"

    def test_partial_match(self, sample_transitions):
        """Test partial name matching."""
        result = find_transition_by_name(sample_transitions, "Progress")
        assert result['id'] == "21"

    def test_not_found_raises(self, sample_transitions):
        """Test error when transition not found."""
        with pytest.raises(ValidationError) as exc_info:
            find_transition_by_name(sample_transitions, "Review")
        assert "not found" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)

    def test_ambiguous_raises(self):
        """Test error when multiple transitions match."""
        transitions = [
            {"id": "1", "name": "Review Code"},
            {"id": "2", "name": "Code Review Complete"}
        ]
        with pytest.raises(ValidationError) as exc_info:
            find_transition_by_name(transitions, "Code")
        assert "Ambiguous" in str(exc_info.value)


class TestTransitionIssue:
    """Tests for the transition_issue function."""

    def test_transition_by_name(self, mock_jira_client, sample_transitions):
        """Test transitioning issue by transition name."""
        mock_jira_client.get_transitions.return_value = sample_transitions

        with patch.object(transition_issue, 'get_jira_client', return_value=mock_jira_client):
            do_transition(
                issue_key="PROJ-123",
                transition_name="In Progress"
            )

        mock_jira_client.transition_issue.assert_called_once_with(
            "PROJ-123", "21", fields=None
        )

    def test_transition_by_id(self, mock_jira_client, sample_transitions):
        """Test transitioning issue by transition ID."""
        mock_jira_client.get_transitions.return_value = sample_transitions

        with patch.object(transition_issue, 'get_jira_client', return_value=mock_jira_client):
            do_transition(
                issue_key="PROJ-123",
                transition_id="31"
            )

        mock_jira_client.transition_issue.assert_called_once_with(
            "PROJ-123", "31", fields=None
        )

    def test_transition_with_resolution(self, mock_jira_client, sample_transitions):
        """Test setting resolution during transition."""
        mock_jira_client.get_transitions.return_value = sample_transitions

        with patch.object(transition_issue, 'get_jira_client', return_value=mock_jira_client):
            do_transition(
                issue_key="PROJ-123",
                transition_name="Done",
                resolution="Fixed"
            )

        call_args = mock_jira_client.transition_issue.call_args
        assert call_args[1]['fields']['resolution'] == {'name': 'Fixed'}

    def test_requires_id_or_name(self, mock_jira_client):
        """Test error when neither ID nor name specified."""
        with pytest.raises(ValidationError) as exc_info:
            do_transition(issue_key="PROJ-123")
        assert "--id or --name" in str(exc_info.value)

    def test_invalid_transition_id(self, mock_jira_client, sample_transitions):
        """Test error when transition ID not available."""
        mock_jira_client.get_transitions.return_value = sample_transitions

        with patch.object(transition_issue, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(ValidationError) as exc_info:
                do_transition(
                    issue_key="PROJ-123",
                    transition_id="999"
                )
        assert "not available" in str(exc_info.value)


class TestTransitionWithSprint:
    """Tests for the sprint integration feature."""

    def test_transition_and_move_to_sprint(self, mock_jira_client, sample_transitions):
        """Test transitioning issue and moving to sprint in one operation."""
        mock_jira_client.get_transitions.return_value = sample_transitions

        with patch.object(transition_issue, 'get_jira_client', return_value=mock_jira_client):
            do_transition(
                issue_key="PROJ-123",
                transition_name="In Progress",
                sprint_id=42
            )

        # Verify transition happened
        mock_jira_client.transition_issue.assert_called_once()

        # Verify issue was moved to sprint
        mock_jira_client.move_issues_to_sprint.assert_called_once_with(42, ["PROJ-123"])

    def test_transition_without_sprint(self, mock_jira_client, sample_transitions):
        """Test that sprint move is not called when not specified."""
        mock_jira_client.get_transitions.return_value = sample_transitions

        with patch.object(transition_issue, 'get_jira_client', return_value=mock_jira_client):
            do_transition(
                issue_key="PROJ-123",
                transition_name="In Progress"
            )

        # Verify sprint move was NOT called
        mock_jira_client.move_issues_to_sprint.assert_not_called()

    def test_transition_with_sprint_and_resolution(self, mock_jira_client, sample_transitions):
        """Test combining sprint, resolution, and transition."""
        mock_jira_client.get_transitions.return_value = sample_transitions

        with patch.object(transition_issue, 'get_jira_client', return_value=mock_jira_client):
            do_transition(
                issue_key="PROJ-123",
                transition_name="Done",
                resolution="Fixed",
                sprint_id=42
            )

        # Verify transition with resolution
        call_args = mock_jira_client.transition_issue.call_args
        assert call_args[1]['fields']['resolution'] == {'name': 'Fixed'}

        # Verify sprint move
        mock_jira_client.move_issues_to_sprint.assert_called_once_with(42, ["PROJ-123"])

    def test_sprint_move_happens_after_transition(self, mock_jira_client, sample_transitions):
        """Test that sprint move happens after successful transition."""
        call_order = []

        def track_transition(*args, **kwargs):
            call_order.append('transition')

        def track_sprint_move(*args, **kwargs):
            call_order.append('sprint_move')

        mock_jira_client.get_transitions.return_value = sample_transitions
        mock_jira_client.transition_issue.side_effect = track_transition
        mock_jira_client.move_issues_to_sprint.side_effect = track_sprint_move

        with patch.object(transition_issue, 'get_jira_client', return_value=mock_jira_client):
            do_transition(
                issue_key="PROJ-123",
                transition_name="In Progress",
                sprint_id=42
            )

        # Verify order: transition first, then sprint move
        assert call_order == ['transition', 'sprint_move']
