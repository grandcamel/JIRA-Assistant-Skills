"""
Tests for get_link_types.py

TDD tests for listing available issue link types.
"""

import pytest
from unittest.mock import patch
import json


@pytest.mark.relationships
@pytest.mark.unit
class TestGetLinkTypes:
    """Tests for the get_link_types function."""

    def test_get_all_link_types(self, mock_jira_client, sample_link_types):
        """Test fetching all available link types."""
        mock_jira_client.get_link_types.return_value = sample_link_types

        # Import after patching
        import get_link_types
        with patch.object(get_link_types, 'get_jira_client', return_value=mock_jira_client):
            result = get_link_types.get_link_types()

        assert len(result) == 4
        assert result[0]['name'] == 'Blocks'
        mock_jira_client.get_link_types.assert_called_once()

    def test_link_type_has_required_fields(self, mock_jira_client, sample_link_types):
        """Test that each link type has id, name, inward, outward."""
        mock_jira_client.get_link_types.return_value = sample_link_types

        import get_link_types
        with patch.object(get_link_types, 'get_jira_client', return_value=mock_jira_client):
            result = get_link_types.get_link_types()

        for link_type in result:
            assert 'id' in link_type
            assert 'name' in link_type
            assert 'inward' in link_type
            assert 'outward' in link_type

    def test_format_text_output(self, mock_jira_client, sample_link_types):
        """Test human-readable table output."""
        mock_jira_client.get_link_types.return_value = sample_link_types

        import get_link_types
        with patch.object(get_link_types, 'get_jira_client', return_value=mock_jira_client):
            output = get_link_types.format_link_types(sample_link_types, output_format='text')

        # Should contain link type names
        assert 'Blocks' in output
        assert 'Duplicate' in output
        assert 'Relates' in output
        # Should contain inward/outward descriptions
        assert 'is blocked by' in output
        assert 'blocks' in output

    def test_format_json_output(self, mock_jira_client, sample_link_types):
        """Test JSON output format."""
        mock_jira_client.get_link_types.return_value = sample_link_types

        import get_link_types
        with patch.object(get_link_types, 'get_jira_client', return_value=mock_jira_client):
            output = get_link_types.format_link_types(sample_link_types, output_format='json')

        # Should be valid JSON
        parsed = json.loads(output)
        assert isinstance(parsed, list)
        assert len(parsed) == 4
        assert parsed[0]['name'] == 'Blocks'

    def test_filter_by_name(self, mock_jira_client, sample_link_types):
        """Test filtering link types by name pattern."""
        mock_jira_client.get_link_types.return_value = sample_link_types

        import get_link_types
        with patch.object(get_link_types, 'get_jira_client', return_value=mock_jira_client):
            result = get_link_types.get_link_types(filter_pattern='block')

        # Should only return Blocks (case-insensitive)
        assert len(result) == 1
        assert result[0]['name'] == 'Blocks'


@pytest.mark.relationships
@pytest.mark.unit
class TestGetLinkTypesErrorHandling:
    """Test API error handling scenarios for get_link_types."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError

        mock_jira_client.get_link_types.side_effect = AuthenticationError("Invalid token")

        import get_link_types
        with patch.object(get_link_types, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(AuthenticationError):
                get_link_types.get_link_types()

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError

        mock_jira_client.get_link_types.side_effect = PermissionError("Insufficient permissions")

        import get_link_types
        with patch.object(get_link_types, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(PermissionError):
                get_link_types.get_link_types()

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError

        mock_jira_client.get_link_types.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        import get_link_types
        with patch.object(get_link_types, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(JiraError) as exc_info:
                get_link_types.get_link_types()
            assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError

        mock_jira_client.get_link_types.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        import get_link_types
        with patch.object(get_link_types, 'get_jira_client', return_value=mock_jira_client):
            with pytest.raises(JiraError) as exc_info:
                get_link_types.get_link_types()
            assert exc_info.value.status_code == 500
