"""
Unit tests for screen listing scripts.

Tests list_screens.py, get_screen.py, list_screen_tabs.py, get_screen_fields.py
using mock JIRA client.

Usage:
    pytest plugins/jira-assistant-skills/skills/jira-admin/tests/unit/test_screen_listing.py -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

# Add scripts to path
_this_dir = Path(__file__).parent.parent
_scripts_path = _this_dir.parent / 'scripts'
sys.path.insert(0, str(_scripts_path))


@pytest.mark.unit
@pytest.mark.admin
class TestListScreens:
    """Tests for list_screens.py functionality."""

    def test_list_all_screens(self, mock_jira_client, screens_response):
        """Test listing all screens."""
        from list_screens import list_screens

        mock_jira_client.get_screens.return_value = screens_response

        result = list_screens(client=mock_jira_client)

        assert len(result) >= 1
        mock_jira_client.get_screens.assert_called_once()

    def test_list_screens_with_filter(self, mock_jira_client, screens_response):
        """Test listing screens with name filter."""
        from list_screens import list_screens

        mock_jira_client.get_screens.return_value = screens_response

        result = list_screens(
            client=mock_jira_client,
            filter_pattern='Default'
        )

        # Should filter to screens containing 'Default' in name
        for screen in result:
            assert 'default' in screen.get('name', '').lower()

    def test_list_screens_with_scope(self, mock_jira_client, screens_response):
        """Test listing screens filtered by scope."""
        from list_screens import list_screens

        mock_jira_client.get_screens.return_value = screens_response

        result = list_screens(
            client=mock_jira_client,
            scope=['GLOBAL']
        )

        mock_jira_client.get_screens.assert_called_with(
            start_at=0,
            max_results=100,
            scope=['GLOBAL'],
            query_string=None
        )

    def test_list_screens_fetch_all_pages(self, mock_jira_client, screens_page_1, screens_page_2):
        """Test fetching all pages of screens."""
        from list_screens import list_screens

        mock_jira_client.get_screens.side_effect = [screens_page_1, screens_page_2]

        result = list_screens(
            client=mock_jira_client,
            fetch_all=True
        )

        assert mock_jira_client.get_screens.call_count >= 1

    def test_list_screens_empty_result(self, mock_jira_client, empty_screens_response):
        """Test listing screens when none exist."""
        from list_screens import list_screens

        mock_jira_client.get_screens.return_value = empty_screens_response

        result = list_screens(client=mock_jira_client)

        assert result == []

    def test_format_screens_output_text(self, screens_response):
        """Test formatting screens for text output."""
        from list_screens import format_screens_output

        screens = screens_response.get('values', [])
        output = format_screens_output(screens, 'text')

        assert isinstance(output, str)
        assert 'ID' in output or len(screens) == 0

    def test_format_screens_output_json(self, screens_response):
        """Test formatting screens for JSON output."""
        from list_screens import format_screens_output

        screens = screens_response.get('values', [])
        output = format_screens_output(screens, 'json')

        assert isinstance(output, str)
        # Should be valid JSON
        import json
        parsed = json.loads(output)
        assert isinstance(parsed, list)

    def test_format_screens_empty(self):
        """Test formatting empty screens list."""
        from list_screens import format_screens_output

        output = format_screens_output([], 'text')

        assert 'No screens found' in output


@pytest.mark.unit
@pytest.mark.admin
class TestGetScreen:
    """Tests for get_screen.py functionality."""

    def test_get_screen_by_id(self, mock_jira_client, default_screen):
        """Test getting screen by ID."""
        from get_screen import get_screen

        mock_jira_client.get_screen.return_value = default_screen

        result = get_screen(
            client=mock_jira_client,
            screen_id='1'
        )

        assert result['id'] == default_screen['id']
        mock_jira_client.get_screen.assert_called_once_with('1')

    def test_get_screen_by_name(self, mock_jira_client, screens_response, default_screen):
        """Test getting screen by name."""
        from get_screen import get_screen

        mock_jira_client.get_screens.return_value = screens_response

        result = get_screen(
            client=mock_jira_client,
            name='Default Screen'
        )

        mock_jira_client.get_screens.assert_called()

    def test_get_screen_not_found(self, mock_jira_client, empty_screens_response):
        """Test getting non-existent screen."""
        from get_screen import get_screen
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_screens.return_value = empty_screens_response

        with pytest.raises((NotFoundError, ValueError)):
            get_screen(
                client=mock_jira_client,
                name='Non-existent Screen'
            )


@pytest.mark.unit
@pytest.mark.admin
class TestListScreenTabs:
    """Tests for list_screen_tabs.py functionality."""

    def test_list_screen_tabs(self, mock_jira_client, default_screen_tabs):
        """Test listing screen tabs."""
        from list_screen_tabs import list_screen_tabs

        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs

        result = list_screen_tabs(
            client=mock_jira_client,
            screen_id='1'
        )

        assert len(result) >= 1
        mock_jira_client.get_screen_tabs.assert_called_once_with('1')

    def test_list_screen_tabs_empty(self, mock_jira_client):
        """Test listing tabs for screen with no tabs."""
        from list_screen_tabs import list_screen_tabs

        mock_jira_client.get_screen_tabs.return_value = []

        result = list_screen_tabs(
            client=mock_jira_client,
            screen_id='1'
        )

        assert result == []


@pytest.mark.unit
@pytest.mark.admin
class TestGetScreenFields:
    """Tests for get_screen_fields.py functionality."""

    def test_get_screen_fields(self, mock_jira_client, field_tab_fields):
        """Test getting fields from a screen tab."""
        from get_screen_fields import get_screen_fields

        mock_jira_client.get_screen_tab_fields.return_value = field_tab_fields

        result = get_screen_fields(
            client=mock_jira_client,
            screen_id='1',
            tab_id='10000'
        )

        assert len(result) >= 1
        mock_jira_client.get_screen_tab_fields.assert_called_once()

    def test_get_all_screen_fields(self, mock_jira_client, default_screen_tabs, all_screen_fields):
        """Test getting all fields from all tabs."""
        from get_screen_fields import get_screen_fields

        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs
        mock_jira_client.get_screen_tab_fields.return_value = all_screen_fields

        result = get_screen_fields(
            client=mock_jira_client,
            screen_id='1'
        )

        # Should have fetched tabs first
        mock_jira_client.get_screen_tabs.assert_called()

    def test_get_screen_fields_empty(self, mock_jira_client):
        """Test getting fields from empty screen."""
        from get_screen_fields import get_screen_fields

        mock_jira_client.get_screen_tab_fields.return_value = []

        result = get_screen_fields(
            client=mock_jira_client,
            screen_id='1',
            tab_id='10000'
        )

        assert result == []


@pytest.mark.unit
@pytest.mark.admin
class TestAddFieldToScreen:
    """Tests for add_field_to_screen.py functionality."""

    def test_add_field_to_screen(self, mock_jira_client, added_field_response):
        """Test adding a field to a screen."""
        from add_field_to_screen import add_field_to_screen

        mock_jira_client.add_screen_tab_field.return_value = added_field_response

        result = add_field_to_screen(
            client=mock_jira_client,
            screen_id='1',
            tab_id='10000',
            field_id='customfield_10050'
        )

        assert result is not None
        mock_jira_client.add_screen_tab_field.assert_called_once()

    def test_add_field_to_default_tab(self, mock_jira_client, default_screen_tabs, added_field_response):
        """Test adding field to default (first) tab."""
        from add_field_to_screen import add_field_to_screen

        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs
        mock_jira_client.add_screen_tab_field.return_value = added_field_response

        result = add_field_to_screen(
            client=mock_jira_client,
            screen_id='1',
            field_id='customfield_10050'
        )

        mock_jira_client.get_screen_tabs.assert_called()


@pytest.mark.unit
@pytest.mark.admin
class TestRemoveFieldFromScreen:
    """Tests for remove_field_from_screen.py functionality."""

    def test_remove_field_from_screen(self, mock_jira_client):
        """Test removing a field from a screen."""
        from remove_field_from_screen import remove_field_from_screen

        mock_jira_client.remove_screen_tab_field.return_value = None

        result = remove_field_from_screen(
            client=mock_jira_client,
            screen_id='1',
            tab_id='10000',
            field_id='customfield_10050'
        )

        mock_jira_client.remove_screen_tab_field.assert_called_once()


@pytest.mark.unit
@pytest.mark.admin
class TestScreenSchemes:
    """Tests for screen scheme listing scripts."""

    def test_list_screen_schemes(self, mock_jira_client, screen_schemes_response):
        """Test listing screen schemes."""
        from list_screen_schemes import list_screen_schemes

        mock_jira_client.get_screen_schemes.return_value = screen_schemes_response

        result = list_screen_schemes(client=mock_jira_client)

        assert len(result) >= 1

    def test_list_screen_schemes_empty(self, mock_jira_client, empty_screen_schemes_response):
        """Test listing screen schemes when none exist."""
        from list_screen_schemes import list_screen_schemes

        mock_jira_client.get_screen_schemes.return_value = empty_screen_schemes_response

        result = list_screen_schemes(client=mock_jira_client)

        assert result == []

    def test_get_screen_scheme(self, mock_jira_client, default_screen_scheme):
        """Test getting a specific screen scheme."""
        from get_screen_scheme import get_screen_scheme

        mock_jira_client.get_screen_scheme.return_value = default_screen_scheme

        result = get_screen_scheme(
            client=mock_jira_client,
            scheme_id='1'
        )

        assert result['id'] == default_screen_scheme['id']


@pytest.mark.unit
@pytest.mark.admin
class TestIssueTypeScreenSchemes:
    """Tests for issue type screen scheme scripts."""

    def test_list_issue_type_screen_schemes(self, mock_jira_client, issue_type_screen_schemes_response):
        """Test listing issue type screen schemes."""
        from list_issue_type_screen_schemes import list_issue_type_screen_schemes

        mock_jira_client.get_issue_type_screen_schemes.return_value = issue_type_screen_schemes_response

        result = list_issue_type_screen_schemes(client=mock_jira_client)

        assert len(result) >= 1

    def test_list_issue_type_screen_schemes_empty(self, mock_jira_client, empty_issue_type_screen_schemes_response):
        """Test listing issue type screen schemes when none exist."""
        from list_issue_type_screen_schemes import list_issue_type_screen_schemes

        mock_jira_client.get_issue_type_screen_schemes.return_value = empty_issue_type_screen_schemes_response

        result = list_issue_type_screen_schemes(client=mock_jira_client)

        assert result == []

    def test_get_issue_type_screen_scheme(self, mock_jira_client, default_issue_type_screen_scheme):
        """Test getting a specific issue type screen scheme."""
        from get_issue_type_screen_scheme import get_issue_type_screen_scheme

        mock_jira_client.get_issue_type_screen_scheme.return_value = default_issue_type_screen_scheme

        result = get_issue_type_screen_scheme(
            client=mock_jira_client,
            scheme_id='1'
        )

        assert result['id'] == default_issue_type_screen_scheme['id']
