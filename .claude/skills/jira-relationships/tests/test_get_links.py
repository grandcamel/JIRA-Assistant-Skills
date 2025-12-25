"""
Tests for get_links.py

TDD tests for viewing issue links.
"""

import pytest
from unittest.mock import Mock, patch
import json


class TestGetLinks:
    """Tests for the get_links function."""

    def test_get_all_links(self, mock_jira_client, sample_issue_links):
        """Test fetching all links for an issue."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_links
        with patch.object(get_links, 'get_jira_client', return_value=mock_jira_client):
            result = get_links.get_links("PROJ-123")

        assert len(result) == 3
        mock_jira_client.get_issue_links.assert_called_once_with("PROJ-123")

    def test_get_outward_links(self, mock_jira_client, sample_issue_links):
        """Test filtering to only outward links."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_links
        with patch.object(get_links, 'get_jira_client', return_value=mock_jira_client):
            result = get_links.get_links("PROJ-123", direction="outward")

        # sample_issue_links has 2 outward links
        assert len(result) == 2
        for link in result:
            assert 'outwardIssue' in link

    def test_get_inward_links(self, mock_jira_client, sample_issue_links):
        """Test filtering to only inward links."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_links
        with patch.object(get_links, 'get_jira_client', return_value=mock_jira_client):
            result = get_links.get_links("PROJ-123", direction="inward")

        # sample_issue_links has 1 inward link
        assert len(result) == 1
        for link in result:
            assert 'inwardIssue' in link

    def test_filter_by_link_type(self, mock_jira_client, sample_issue_links):
        """Test filtering by specific link type (e.g., blocks)."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_links
        with patch.object(get_links, 'get_jira_client', return_value=mock_jira_client):
            result = get_links.get_links("PROJ-123", link_type="Blocks")

        # sample_issue_links has 2 Blocks links
        assert len(result) == 2
        for link in result:
            assert link['type']['name'] == 'Blocks'

    def test_format_text_output(self, mock_jira_client, sample_issue_links):
        """Test human-readable output."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_links
        with patch.object(get_links, 'get_jira_client', return_value=mock_jira_client):
            output = get_links.format_links(sample_issue_links, "PROJ-123", output_format='text')

        # Should contain issue keys
        assert 'PROJ-456' in output
        assert 'PROJ-789' in output
        assert 'PROJ-100' in output
        # Should show link directions
        assert 'blocks' in output or 'Blocks' in output

    def test_format_json_output(self, mock_jira_client, sample_issue_links):
        """Test JSON output format."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_links
        with patch.object(get_links, 'get_jira_client', return_value=mock_jira_client):
            output = get_links.format_links(sample_issue_links, "PROJ-123", output_format='json')

        # Should be valid JSON
        parsed = json.loads(output)
        assert isinstance(parsed, list)
        assert len(parsed) == 3

    def test_issue_no_links(self, mock_jira_client):
        """Test output when issue has no links."""
        mock_jira_client.get_issue_links.return_value = []

        import get_links
        with patch.object(get_links, 'get_jira_client', return_value=mock_jira_client):
            result = get_links.get_links("PROJ-124")

        assert len(result) == 0

    def test_issue_not_found(self, mock_jira_client):
        """Test error when issue doesn't exist."""
        from error_handler import NotFoundError
        mock_jira_client.get_issue_links.side_effect = NotFoundError("Issue not found")

        import get_links
        with patch.object(get_links, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(NotFoundError):
                get_links.get_links("PROJ-999")
