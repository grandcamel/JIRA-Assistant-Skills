"""
Unit tests for get_issue.py script.

Tests cover:
- Retrieving issue details
- Retrieving issue with specific fields
- Detailed output (including description)
- Issue links display
- Time tracking display
- Validation errors (invalid issue key)
- Not found errors
- Authentication errors
- Output formatting (text and JSON)
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch
from copy import deepcopy

# Add scripts path
scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

# Import after path setup
import get_issue as get_issue_module
from jira_assistant_skills_lib import format_issue, format_json


@pytest.mark.unit
class TestGetIssueBasic:
    """Tests for basic issue retrieval."""

    def test_get_issue_success(self, mock_jira_client, sample_issue):
        """Test retrieving an issue successfully."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(issue_key="PROJ-123")

        mock_jira_client.get_issue.assert_called_once_with("PROJ-123", fields=None)
        assert result['key'] == "PROJ-123"
        assert result['fields']['summary'] == "Test Issue Summary"

    def test_get_issue_normalizes_key(self, mock_jira_client, sample_issue):
        """Test that issue key is normalized to uppercase."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(issue_key="proj-123")

        mock_jira_client.get_issue.assert_called_once_with("PROJ-123", fields=None)
        assert result['key'] == "PROJ-123"

    def test_get_issue_returns_all_fields(self, mock_jira_client, sample_issue):
        """Test that retrieved issue contains all expected fields."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(issue_key="PROJ-123")

        fields = result['fields']
        assert 'summary' in fields
        assert 'status' in fields
        assert 'issuetype' in fields
        assert 'priority' in fields
        assert 'assignee' in fields
        assert 'reporter' in fields


@pytest.mark.unit
class TestGetIssueWithFields:
    """Tests for retrieving issues with specific fields."""

    def test_get_issue_with_specific_fields(self, mock_jira_client, sample_issue_minimal):
        """Test retrieving an issue with specific fields."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue_minimal)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(
                issue_key="PROJ-124",
                fields=['summary', 'status']
            )

        mock_jira_client.get_issue.assert_called_once_with(
            "PROJ-124",
            fields=['summary', 'status']
        )
        assert result['key'] == "PROJ-124"


@pytest.mark.unit
class TestGetIssueWithLinks:
    """Tests for retrieving issues with links."""

    def test_get_issue_with_links(self, mock_jira_client, sample_issue_with_links):
        """Test retrieving an issue with issue links."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue_with_links)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(issue_key="PROJ-126")

        assert 'issuelinks' in result['fields']
        assert len(result['fields']['issuelinks']) == 2

    def test_get_issue_links_contains_blocks(self, mock_jira_client, sample_issue_with_links):
        """Test that issue links contain blocking relationships."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue_with_links)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(issue_key="PROJ-126")

        links = result['fields']['issuelinks']
        blocks_link = next((l for l in links if l['type']['name'] == 'Blocks'), None)
        assert blocks_link is not None
        assert 'outwardIssue' in blocks_link

    def test_get_issue_links_contains_relates(self, mock_jira_client, sample_issue_with_links):
        """Test that issue links contain relates relationships."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue_with_links)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(issue_key="PROJ-126")

        links = result['fields']['issuelinks']
        relates_link = next((l for l in links if l['type']['name'] == 'Relates'), None)
        assert relates_link is not None


@pytest.mark.unit
class TestGetIssueWithTimeTracking:
    """Tests for retrieving issues with time tracking."""

    def test_get_issue_with_time_tracking(self, mock_jira_client, sample_issue_with_time_tracking):
        """Test retrieving an issue with time tracking information."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue_with_time_tracking)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(issue_key="PROJ-125")

        tt = result['fields']['timetracking']
        assert tt['originalEstimate'] == "2d"
        assert tt['remainingEstimate'] == "1d 4h"
        assert tt['timeSpent'] == "4h"

    def test_get_issue_time_tracking_seconds(self, mock_jira_client, sample_issue_with_time_tracking):
        """Test that time tracking includes seconds values."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue_with_time_tracking)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(issue_key="PROJ-125")

        tt = result['fields']['timetracking']
        assert tt['originalEstimateSeconds'] == 57600
        assert tt['remainingEstimateSeconds'] == 36000
        assert tt['timeSpentSeconds'] == 14400


@pytest.mark.unit
class TestGetIssueWithAgile:
    """Tests for retrieving issues with Agile fields."""

    def test_get_issue_with_agile_fields(self, mock_jira_client, sample_issue_with_agile):
        """Test retrieving an issue with Agile fields."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue_with_agile)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(issue_key="PROJ-129")

        assert result['fields']['customfield_10014'] == "PROJ-100"  # Epic Link
        assert result['fields']['customfield_10016'] == 5.0  # Story Points


@pytest.mark.unit
class TestGetIssueValidation:
    """Tests for input validation."""

    def test_get_issue_invalid_key_raises_error(self, mock_jira_client):
        """Test that invalid issue key raises ValidationError."""
        from error_handler import ValidationError

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(ValidationError):
                get_issue_module.get_issue(issue_key="invalid-key")

    def test_get_issue_empty_key_raises_error(self, mock_jira_client):
        """Test that empty issue key raises ValidationError."""
        from error_handler import ValidationError

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(ValidationError):
                get_issue_module.get_issue(issue_key="")

    def test_get_issue_key_with_spaces_raises_error(self, mock_jira_client):
        """Test that issue key with spaces raises ValidationError."""
        from error_handler import ValidationError

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(ValidationError):
                get_issue_module.get_issue(issue_key="PROJ 123")


@pytest.mark.unit
class TestGetIssueErrors:
    """Tests for error handling."""

    def test_get_issue_not_found(self, mock_jira_client):
        """Test handling issue not found error."""
        from error_handler import NotFoundError
        mock_jira_client.get_issue.side_effect = NotFoundError(
            "Issue", "PROJ-999"
        )

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(NotFoundError) as exc_info:
                get_issue_module.get_issue(issue_key="PROJ-999")

        assert "not found" in str(exc_info.value).lower()

    def test_get_issue_permission_denied(self, mock_jira_client):
        """Test handling permission denied error."""
        from error_handler import PermissionError
        mock_jira_client.get_issue.side_effect = PermissionError(
            "You do not have permission to view this issue"
        )

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(PermissionError) as exc_info:
                get_issue_module.get_issue(issue_key="PROJ-123")

        assert "permission" in str(exc_info.value).lower()

    def test_get_issue_authentication_error(self, mock_jira_client):
        """Test handling authentication error."""
        from error_handler import AuthenticationError
        mock_jira_client.get_issue.side_effect = AuthenticationError(
            "Authentication failed"
        )

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(AuthenticationError):
                get_issue_module.get_issue(issue_key="PROJ-123")


@pytest.mark.unit
class TestGetIssueOutputFormatting:
    """Tests for output formatting."""

    def test_format_issue_text(self, mock_jira_client, sample_issue):
        """Test text output format for issue."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(issue_key="PROJ-123")
            output = format_issue(result, detailed=False)

        assert "PROJ-123" in output
        assert "Test Issue Summary" in output
        assert "Open" in output
        assert "Bug" in output

    def test_format_issue_text_detailed(self, mock_jira_client, sample_issue):
        """Test detailed text output format for issue."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(issue_key="PROJ-123")
            output = format_issue(result, detailed=True)

        assert "PROJ-123" in output
        assert "Reporter" in output
        assert "Created" in output
        assert "Description" in output

    def test_format_issue_json(self, mock_jira_client, sample_issue):
        """Test JSON output format for issue."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(issue_key="PROJ-123")
            output = format_json(result)

        parsed = json.loads(output)
        assert parsed['key'] == "PROJ-123"
        assert parsed['fields']['summary'] == "Test Issue Summary"

    def test_format_issue_with_links_text(self, mock_jira_client, sample_issue_with_links):
        """Test text output format for issue with links."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue_with_links)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(issue_key="PROJ-126")
            output = format_issue(result, detailed=True)

        assert "Links" in output
        assert "blocks" in output.lower() or "PROJ-127" in output


@pytest.mark.unit
class TestGetIssueProfile:
    """Tests for profile handling."""

    def test_get_issue_with_profile(self, mock_jira_client, sample_issue):
        """Test retrieving issue with specific profile."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client) as mock_get_client:
            get_issue_module.get_issue(issue_key="PROJ-123", profile="development")

        mock_get_client.assert_called_with("development")


@pytest.mark.unit
class TestGetIssueMinimal:
    """Tests for minimal issue responses."""

    def test_get_issue_minimal_fields(self, mock_jira_client, sample_issue_minimal):
        """Test retrieving an issue with minimal fields."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue_minimal)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(issue_key="PROJ-124")

        assert result['key'] == "PROJ-124"
        assert result['fields']['summary'] == "Minimal Issue"
        # Minimal issue should not have priority or assignee
        assert result['fields'].get('priority') is None
        assert result['fields'].get('assignee') is None

    def test_format_issue_handles_missing_fields(self, mock_jira_client, sample_issue_minimal):
        """Test that formatting handles missing optional fields gracefully."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue_minimal)

        with patch.object(get_issue_module, 'get_jira_client', return_value=mock_jira_client):
            result = get_issue_module.get_issue(issue_key="PROJ-124")
            output = format_issue(result, detailed=False)

        # Should not crash, should show reasonable defaults
        assert "PROJ-124" in output
        assert "Minimal Issue" in output
