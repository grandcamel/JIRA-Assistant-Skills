"""
Tests for get_notification_scheme.py - TDD approach.

Test cases per implementation plan:
1. test_get_notification_scheme_by_id - Test fetching scheme by ID
2. test_scheme_details - Test that all detail fields are present
3. test_show_event_configurations - Test showing event-to-recipient mappings
4. test_format_text_output - Test human-readable output with full details
5. test_format_json_output - Test JSON output format
6. test_scheme_not_found - Test error when scheme ID doesn't exist
7. test_show_projects_using_scheme - Test showing which projects use this scheme
8. test_group_by_event_type - Test grouping notifications by event type
9. test_show_recipient_details - Test expanding recipient details
"""

import json
import sys
from pathlib import Path

import pytest

# Add scripts and shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestGetNotificationSchemeById:
    """Test fetching notification scheme by ID."""

    def test_get_notification_scheme_by_id(
        self, mock_jira_client, sample_notification_scheme_detail
    ):
        """Test fetching notification scheme by ID."""
        from get_notification_scheme import get_notification_scheme

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = (
            sample_notification_scheme_detail
        )

        # Execute
        result = get_notification_scheme(client=mock_jira_client, scheme_id="10000")

        # Verify
        assert result["id"] == "10000"
        assert result["name"] == "Default Notification Scheme"
        mock_jira_client.get_notification_scheme.assert_called_once_with(
            "10000", expand="notificationSchemeEvents"
        )


class TestSchemeDetails:
    """Test that all detail fields are present."""

    def test_scheme_details(self, mock_jira_client, sample_notification_scheme_detail):
        """Test that all detail fields are present."""
        from get_notification_scheme import get_notification_scheme

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = (
            sample_notification_scheme_detail
        )

        # Execute
        result = get_notification_scheme(client=mock_jira_client, scheme_id="10000")

        # Verify all detail fields
        assert "id" in result
        assert "name" in result
        assert "description" in result
        assert "notificationSchemeEvents" in result
        assert len(result["notificationSchemeEvents"]) > 0


class TestShowEventConfigurations:
    """Test showing event-to-recipient mappings."""

    def test_show_event_configurations(
        self, mock_jira_client, sample_notification_scheme_detail
    ):
        """Test showing event-to-recipient mappings."""
        from get_notification_scheme import get_notification_scheme

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = (
            sample_notification_scheme_detail
        )

        # Execute
        result = get_notification_scheme(client=mock_jira_client, scheme_id="10000")

        # Verify events have notifications
        events = result["notificationSchemeEvents"]
        assert len(events) >= 2

        # Check first event has expected structure
        first_event = events[0]
        assert "event" in first_event
        assert "notifications" in first_event
        assert len(first_event["notifications"]) > 0


class TestFormatTextOutput:
    """Test human-readable output with full details."""

    def test_format_text_output(
        self, mock_jira_client, sample_notification_scheme_detail
    ):
        """Test human-readable output with full details."""
        from get_notification_scheme import format_text_output, get_notification_scheme

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = (
            sample_notification_scheme_detail
        )

        # Execute
        result = get_notification_scheme(client=mock_jira_client, scheme_id="10000")
        output = format_text_output(result)

        # Verify output contains expected content
        assert "Default Notification Scheme" in output
        assert "10000" in output
        assert "Issue created" in output
        assert "Current Assignee" in output
        assert "Reporter" in output


class TestFormatJsonOutput:
    """Test JSON output format."""

    def test_format_json_output(
        self, mock_jira_client, sample_notification_scheme_detail
    ):
        """Test JSON output format."""
        from get_notification_scheme import format_json_output, get_notification_scheme

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = (
            sample_notification_scheme_detail
        )

        # Execute
        result = get_notification_scheme(client=mock_jira_client, scheme_id="10000")
        output = format_json_output(result)

        # Verify valid JSON
        parsed = json.loads(output)
        assert parsed["id"] == "10000"
        assert "notificationSchemeEvents" in parsed


class TestSchemeNotFound:
    """Test error when scheme ID doesn't exist."""

    def test_scheme_not_found(self, mock_jira_client):
        """Test error when scheme ID doesn't exist."""
        from get_notification_scheme import get_notification_scheme

        from jira_assistant_skills_lib import NotFoundError

        # Setup mock to raise NotFoundError
        mock_jira_client.get_notification_scheme.side_effect = NotFoundError(
            resource_type="Notification scheme", resource_id="99999"
        )

        # Execute and verify exception
        with pytest.raises(NotFoundError):
            get_notification_scheme(client=mock_jira_client, scheme_id="99999")


class TestShowProjectsUsingScheme:
    """Test showing which projects use this scheme."""

    def test_show_projects_using_scheme(
        self, mock_jira_client, sample_notification_scheme_detail
    ):
        """Test showing which projects use this scheme."""
        from get_notification_scheme import get_notification_scheme

        # Setup mock with filtered project mappings (only for scheme 10000)
        filtered_mappings = {
            "values": [
                {"projectId": "10000", "notificationSchemeId": "10000"},
                {"projectId": "10001", "notificationSchemeId": "10000"},
            ],
            "startAt": 0,
            "maxResults": 50,
            "total": 2,
            "isLast": True,
        }
        mock_jira_client.get_notification_scheme.return_value = (
            sample_notification_scheme_detail
        )
        mock_jira_client.get_notification_scheme_projects.return_value = (
            filtered_mappings
        )

        # Execute with show_projects=True
        result = get_notification_scheme(
            client=mock_jira_client, scheme_id="10000", show_projects=True
        )

        # Verify projects info is included
        assert "projects" in result
        assert result["project_count"] == 2  # Two projects use scheme 10000

    def test_show_projects_in_output(
        self,
        mock_jira_client,
        sample_notification_scheme_detail,
        sample_project_mappings,
    ):
        """Test that project count appears in text output."""
        from get_notification_scheme import format_text_output, get_notification_scheme

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = (
            sample_notification_scheme_detail
        )
        mock_jira_client.get_notification_scheme_projects.return_value = (
            sample_project_mappings
        )

        # Execute
        result = get_notification_scheme(
            client=mock_jira_client, scheme_id="10000", show_projects=True
        )
        output = format_text_output(result, show_projects=True)

        # Verify project info in output
        assert "project" in output.lower()
        assert "2" in output


class TestGroupByEventType:
    """Test grouping notifications by event type."""

    def test_group_by_event_type(
        self, mock_jira_client, sample_notification_scheme_detail
    ):
        """Test grouping notifications by event type."""
        from get_notification_scheme import format_text_output, get_notification_scheme

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = (
            sample_notification_scheme_detail
        )

        # Execute
        result = get_notification_scheme(client=mock_jira_client, scheme_id="10000")
        output = format_text_output(result)

        # Verify events are grouped in output
        assert "Issue created" in output
        assert "Issue updated" in output
        assert "Issue assigned" in output


class TestShowRecipientDetails:
    """Test expanding recipient details."""

    def test_show_recipient_details(
        self, mock_jira_client, sample_notification_scheme_with_all_types
    ):
        """Test expanding recipient details (group names, user names, etc.)."""
        from get_notification_scheme import format_text_output, get_notification_scheme

        # Setup mock with comprehensive scheme
        mock_jira_client.get_notification_scheme.return_value = (
            sample_notification_scheme_with_all_types
        )

        # Execute
        result = get_notification_scheme(client=mock_jira_client, scheme_id="10005")
        output = format_text_output(result)

        # Verify various recipient types are shown
        assert "Current Assignee" in output
        assert "Reporter" in output
        assert "All Watchers" in output
        # Check parameterized types show their parameters
        assert "jira-administrators" in output  # Group parameter

    def test_lookup_by_name(
        self,
        mock_jira_client,
        sample_notification_scheme_detail,
        sample_notification_schemes,
    ):
        """Test looking up scheme by name instead of ID."""
        from get_notification_scheme import get_notification_scheme

        # Setup mock
        mock_jira_client.lookup_notification_scheme_by_name.return_value = {
            "id": "10000",
            "name": "Default Notification Scheme",
        }
        mock_jira_client.get_notification_scheme.return_value = (
            sample_notification_scheme_detail
        )

        # Execute with name instead of ID
        result = get_notification_scheme(
            client=mock_jira_client, scheme_name="Default Notification Scheme"
        )

        # Verify
        assert result["id"] == "10000"
        mock_jira_client.lookup_notification_scheme_by_name.assert_called_once()
