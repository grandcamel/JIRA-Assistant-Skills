"""
Tests for get_dependencies.py

TDD tests for finding all issue dependencies.
"""

import pytest
from unittest.mock import patch
import json


@pytest.mark.relationships
@pytest.mark.unit
class TestGetDependencies:
    """Tests for the get_dependencies function."""

    def test_get_all_dependencies(self, mock_jira_client, sample_issue_links):
        """Test finding all related issues (any link type)."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_dependencies
        with patch.object(get_dependencies, 'get_jira_client', return_value=mock_jira_client):
            result = get_dependencies.get_dependencies("PROJ-123")

        # Should find all 3 linked issues
        assert len(result['dependencies']) == 3

    def test_dependencies_by_type(self, mock_jira_client, sample_issue_links):
        """Test filtering dependencies by link type."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_dependencies
        with patch.object(get_dependencies, 'get_jira_client', return_value=mock_jira_client):
            result = get_dependencies.get_dependencies("PROJ-123", link_types=["Blocks"])

        # Should only find Blocks links (2 in sample)
        assert len(result['dependencies']) == 2
        for dep in result['dependencies']:
            assert dep['link_type'] == 'Blocks'

    def test_dependencies_with_status_summary(self, mock_jira_client, sample_issue_links):
        """Test showing dependency status summary."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_dependencies
        with patch.object(get_dependencies, 'get_jira_client', return_value=mock_jira_client):
            result = get_dependencies.get_dependencies("PROJ-123")

        # Should include status counts
        assert 'status_summary' in result
        # sample_issue_links has: Done (1), In Progress (1), To Do (1)

    def test_dependencies_mermaid_format(self, mock_jira_client, sample_issue_links):
        """Test Mermaid diagram output for visualization."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_dependencies
        with patch.object(get_dependencies, 'get_jira_client', return_value=mock_jira_client):
            result = get_dependencies.get_dependencies("PROJ-123")
            output = get_dependencies.format_dependencies(result, output_format='mermaid')

        # Should be valid Mermaid diagram starting with 'graph' or 'flowchart'
        # Mermaid diagrams typically start with one of these directives
        output_lower = output.lower()
        assert 'graph' in output_lower or 'flowchart' in output_lower
        assert 'PROJ-123' in output

    def test_dependencies_dot_format(self, mock_jira_client, sample_issue_links):
        """Test DOT/Graphviz output for visualization."""
        mock_jira_client.get_issue_links.return_value = sample_issue_links

        import get_dependencies
        with patch.object(get_dependencies, 'get_jira_client', return_value=mock_jira_client):
            result = get_dependencies.get_dependencies("PROJ-123")
            output = get_dependencies.format_dependencies(result, output_format='dot')

        # Should be valid DOT format
        assert 'digraph' in output
        assert 'PROJ' in output


@pytest.mark.relationships
@pytest.mark.unit
class TestGetDependenciesErrorHandling:
    """Test API error handling scenarios for get_dependencies."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError

        mock_jira_client.get_issue_links.side_effect = AuthenticationError("Invalid token")

        import get_dependencies
        with patch.object(get_dependencies, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(AuthenticationError):
                get_dependencies.get_dependencies("PROJ-123")

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError

        mock_jira_client.get_issue_links.side_effect = PermissionError("Insufficient permissions")

        import get_dependencies
        with patch.object(get_dependencies, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(PermissionError):
                get_dependencies.get_dependencies("PROJ-123")

    def test_issue_not_found_error(self, mock_jira_client):
        """Test handling of 404 issue not found."""
        from error_handler import NotFoundError

        mock_jira_client.get_issue_links.side_effect = NotFoundError("Issue not found")

        import get_dependencies
        with patch.object(get_dependencies, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(NotFoundError):
                get_dependencies.get_dependencies("PROJ-999")

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError

        mock_jira_client.get_issue_links.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        import get_dependencies
        with patch.object(get_dependencies, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(JiraError) as exc_info:
                get_dependencies.get_dependencies("PROJ-123")
            assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError

        mock_jira_client.get_issue_links.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        import get_dependencies
        with patch.object(get_dependencies, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(JiraError) as exc_info:
                get_dependencies.get_dependencies("PROJ-123")
            assert exc_info.value.status_code == 500
