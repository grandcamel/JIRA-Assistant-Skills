"""
Unit tests for Screen Schemes scripts (Phase 2).

Tests:
- list_screen_schemes.py
- get_screen_scheme.py
"""

import pytest
from unittest.mock import Mock
import sys
from pathlib import Path
import json

# Ensure paths are set up for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))


# ========== Test list_screen_schemes.py ==========

@pytest.mark.admin
@pytest.mark.unit
class TestListScreenSchemes:
    """Tests for list_screen_schemes.py script."""

    def test_list_all_screen_schemes(self, mock_jira_client, screen_schemes_response):
        """Test listing all screen schemes."""
        mock_jira_client.get_screen_schemes.return_value = screen_schemes_response

        from list_screen_schemes import list_screen_schemes
        result = list_screen_schemes(client=mock_jira_client)

        assert result is not None
        assert len(result) == 3
        mock_jira_client.get_screen_schemes.assert_called_once()

    def test_list_schemes_with_pagination(self, mock_jira_client):
        """Test handling paginated results."""
        page1 = {
            "maxResults": 2,
            "startAt": 0,
            "total": 3,
            "isLast": False,
            "values": [
                {"id": 1, "name": "Default Screen Scheme", "description": "Default"},
                {"id": 2, "name": "Bug Screen Scheme", "description": "Bugs"}
            ]
        }
        page2 = {
            "maxResults": 2,
            "startAt": 2,
            "total": 3,
            "isLast": True,
            "values": [
                {"id": 3, "name": "Software Dev Scheme", "description": "Software"}
            ]
        }
        mock_jira_client.get_screen_schemes.side_effect = [page1, page2]

        from list_screen_schemes import list_screen_schemes
        result = list_screen_schemes(client=mock_jira_client, fetch_all=True)

        assert len(result) == 3
        assert mock_jira_client.get_screen_schemes.call_count == 2

    def test_filter_schemes_by_name(self, mock_jira_client, screen_schemes_response):
        """Test filtering schemes by name pattern."""
        mock_jira_client.get_screen_schemes.return_value = screen_schemes_response

        from list_screen_schemes import list_screen_schemes
        result = list_screen_schemes(client=mock_jira_client, filter_pattern="Default")

        assert all("Default" in scheme['name'] for scheme in result)

    def test_show_scheme_mappings(self, mock_jira_client, screen_schemes_response):
        """Test showing screen mappings (create/edit/view)."""
        mock_jira_client.get_screen_schemes.return_value = screen_schemes_response

        from list_screen_schemes import list_screen_schemes, format_schemes_output
        schemes = list_screen_schemes(client=mock_jira_client)
        output = format_schemes_output(schemes, show_screens=True, output_format='text')

        # Should show screen mappings
        assert 'Default Screen Scheme' in output

    def test_format_text_output(self, mock_jira_client, screen_schemes_response):
        """Test human-readable table output."""
        mock_jira_client.get_screen_schemes.return_value = screen_schemes_response

        from list_screen_schemes import list_screen_schemes, format_schemes_output
        schemes = list_screen_schemes(client=mock_jira_client)
        output = format_schemes_output(schemes, output_format='text')

        assert 'Default Screen Scheme' in output
        assert 'Bug Screen Scheme' in output

    def test_format_json_output(self, mock_jira_client, screen_schemes_response):
        """Test JSON output format."""
        mock_jira_client.get_screen_schemes.return_value = screen_schemes_response

        from list_screen_schemes import list_screen_schemes, format_schemes_output
        schemes = list_screen_schemes(client=mock_jira_client)
        output = format_schemes_output(schemes, output_format='json')

        parsed = json.loads(output)
        assert isinstance(parsed, list)
        assert len(parsed) == 3

    def test_empty_screen_schemes(self, mock_jira_client, empty_screen_schemes_response):
        """Test output when no screen schemes exist."""
        mock_jira_client.get_screen_schemes.return_value = empty_screen_schemes_response

        from list_screen_schemes import list_screen_schemes
        result = list_screen_schemes(client=mock_jira_client)

        assert result == []


# ========== Test get_screen_scheme.py ==========

@pytest.mark.admin
@pytest.mark.unit
class TestGetScreenScheme:
    """Tests for get_screen_scheme.py script."""

    def test_get_screen_scheme_basic(self, mock_jira_client, default_screen_scheme):
        """Test getting basic scheme details."""
        mock_jira_client.get_screen_scheme.return_value = default_screen_scheme

        from get_screen_scheme import get_screen_scheme
        result = get_screen_scheme(scheme_id=1, client=mock_jira_client)

        assert result is not None
        assert result['id'] == 1
        assert result['name'] == 'Default Screen Scheme'

    def test_get_screen_scheme_with_screens(self, mock_jira_client, default_screen_scheme, screens_response):
        """Test including screen details for each operation."""
        mock_jira_client.get_screen_scheme.return_value = default_screen_scheme
        mock_jira_client.get_screens.return_value = screens_response

        from get_screen_scheme import get_screen_scheme
        result = get_screen_scheme(scheme_id=1, client=mock_jira_client, show_screen_details=True)

        assert 'screens' in result
        # Should resolve screen IDs to names if show_screen_details is True

    def test_get_screen_scheme_by_id(self, mock_jira_client, default_screen_scheme):
        """Test fetching scheme by numeric ID."""
        mock_jira_client.get_screen_scheme.return_value = default_screen_scheme

        from get_screen_scheme import get_screen_scheme
        result = get_screen_scheme(scheme_id=1, client=mock_jira_client)

        mock_jira_client.get_screen_scheme.assert_called_once_with(1)
        assert result['id'] == 1

    def test_get_screen_scheme_not_found(self, mock_jira_client):
        """Test error handling for invalid scheme ID."""
        from error_handler import NotFoundError
        mock_jira_client.get_screen_scheme.side_effect = NotFoundError("Screen scheme 999 not found")

        from get_screen_scheme import get_screen_scheme
        with pytest.raises(NotFoundError):
            get_screen_scheme(scheme_id=999, client=mock_jira_client)

    def test_format_detailed_output(self, mock_jira_client, default_screen_scheme):
        """Test detailed human-readable output."""
        mock_jira_client.get_screen_scheme.return_value = default_screen_scheme

        from get_screen_scheme import get_screen_scheme, format_scheme_output
        scheme = get_screen_scheme(scheme_id=1, client=mock_jira_client)
        output = format_scheme_output(scheme, output_format='text')

        assert 'Default Screen Scheme' in output
        assert 'The default screen scheme' in output
