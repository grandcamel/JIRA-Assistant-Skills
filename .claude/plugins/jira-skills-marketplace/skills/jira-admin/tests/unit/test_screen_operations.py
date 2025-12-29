"""
Unit tests for Screen Operations scripts (Phase 1).

Tests:
- list_screens.py
- get_screen.py
- list_screen_tabs.py
- get_screen_fields.py
- add_field_to_screen.py
- remove_field_from_screen.py
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path
import json

# Ensure paths are set up for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared' / 'scripts' / 'lib'))


# ========== Test list_screens.py ==========

@pytest.mark.admin
@pytest.mark.unit
class TestListScreens:
    """Tests for list_screens.py script."""

    def test_list_all_screens(self, mock_jira_client, screens_response):
        """Test listing all screens."""
        mock_jira_client.get_screens.return_value = screens_response

        from list_screens import list_screens
        result = list_screens(client=mock_jira_client)

        assert result is not None
        assert len(result) == 5
        mock_jira_client.get_screens.assert_called_once()

    def test_list_screens_with_pagination(self, mock_jira_client, screens_page_1, screens_page_2, screens_page_3):
        """Test handling paginated screen results."""
        # Mock paginated responses
        mock_jira_client.get_screens.side_effect = [
            screens_page_1,
            screens_page_2,
            screens_page_3
        ]

        from list_screens import list_screens
        result = list_screens(client=mock_jira_client, fetch_all=True)

        assert result is not None
        assert len(result) == 5
        assert mock_jira_client.get_screens.call_count == 3

    def test_filter_screens_by_name(self, mock_jira_client, screens_response):
        """Test filtering screens by name pattern."""
        mock_jira_client.get_screens.return_value = screens_response

        from list_screens import list_screens
        result = list_screens(client=mock_jira_client, filter_pattern="Default")

        # Should only return screens with "Default" in name
        assert all("Default" in screen['name'] for screen in result)

    def test_format_text_output(self, mock_jira_client, screens_response):
        """Test human-readable table output."""
        mock_jira_client.get_screens.return_value = screens_response

        from list_screens import list_screens, format_screens_output
        screens = list_screens(client=mock_jira_client)
        output = format_screens_output(screens, output_format='text')

        assert 'Default Screen' in output
        assert 'Resolve Issue Screen' in output

    def test_format_json_output(self, mock_jira_client, screens_response):
        """Test JSON output format."""
        mock_jira_client.get_screens.return_value = screens_response

        from list_screens import list_screens, format_screens_output
        screens = list_screens(client=mock_jira_client)
        output = format_screens_output(screens, output_format='json')

        # Should be valid JSON
        parsed = json.loads(output)
        assert isinstance(parsed, list)
        assert len(parsed) == 5

    def test_empty_screens(self, mock_jira_client, empty_screens_response):
        """Test output when no screens exist."""
        mock_jira_client.get_screens.return_value = empty_screens_response

        from list_screens import list_screens
        result = list_screens(client=mock_jira_client)

        assert result == []

    def test_screen_has_required_fields(self, mock_jira_client, screens_response):
        """Test that each screen has id, name, description."""
        mock_jira_client.get_screens.return_value = screens_response

        from list_screens import list_screens
        screens = list_screens(client=mock_jira_client)

        for screen in screens:
            assert 'id' in screen
            assert 'name' in screen
            # description may be optional


# ========== Test get_screen.py ==========

@pytest.mark.admin
@pytest.mark.unit
class TestGetScreen:
    """Tests for get_screen.py script."""

    def test_get_screen_basic(self, mock_jira_client, default_screen):
        """Test getting basic screen details."""
        mock_jira_client.get_screen.return_value = default_screen

        from get_screen import get_screen
        result = get_screen(screen_id=1, client=mock_jira_client)

        assert result is not None
        assert result['id'] == 1
        assert result['name'] == 'Default Screen'

    def test_get_screen_with_tabs(self, mock_jira_client, default_screen, default_screen_tabs):
        """Test including tabs in output."""
        mock_jira_client.get_screen.return_value = default_screen
        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs

        from get_screen import get_screen
        result = get_screen(screen_id=1, client=mock_jira_client, show_tabs=True)

        assert 'tabs' in result
        assert len(result['tabs']) == 2
        mock_jira_client.get_screen_tabs.assert_called_once_with(1)

    def test_get_screen_with_fields(self, mock_jira_client, default_screen, default_screen_tabs,
                                     field_tab_fields, custom_fields_tab_fields):
        """Test including all fields from all tabs."""
        mock_jira_client.get_screen.return_value = default_screen
        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs
        mock_jira_client.get_screen_tab_fields.side_effect = [
            field_tab_fields,
            custom_fields_tab_fields
        ]

        from get_screen import get_screen
        result = get_screen(screen_id=1, client=mock_jira_client, show_tabs=True, show_fields=True)

        assert 'tabs' in result
        assert 'fields' in result['tabs'][0]
        assert 'fields' in result['tabs'][1]

    def test_get_screen_by_id(self, mock_jira_client, default_screen):
        """Test fetching screen by numeric ID."""
        mock_jira_client.get_screen.return_value = default_screen

        from get_screen import get_screen
        result = get_screen(screen_id=1, client=mock_jira_client)

        mock_jira_client.get_screen.assert_called_once_with(1)
        assert result['id'] == 1

    def test_get_screen_not_found(self, mock_jira_client):
        """Test error handling for invalid screen ID."""
        from error_handler import NotFoundError
        mock_jira_client.get_screen.side_effect = NotFoundError("Screen with ID 999 not found")

        from get_screen import get_screen
        with pytest.raises(NotFoundError):
            get_screen(screen_id=999, client=mock_jira_client)

    def test_format_detailed_output(self, mock_jira_client, default_screen, default_screen_tabs,
                                     field_tab_fields, custom_fields_tab_fields):
        """Test detailed human-readable output with tabs and fields."""
        mock_jira_client.get_screen.return_value = default_screen
        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs
        mock_jira_client.get_screen_tab_fields.side_effect = [
            field_tab_fields,
            custom_fields_tab_fields
        ]

        from get_screen import get_screen, format_screen_output
        result = get_screen(screen_id=1, client=mock_jira_client, show_tabs=True, show_fields=True)
        output = format_screen_output(result, output_format='text')

        assert 'Default Screen' in output
        assert 'Field Tab' in output
        assert 'Summary' in output


# ========== Test list_screen_tabs.py ==========

@pytest.mark.admin
@pytest.mark.unit
class TestListScreenTabs:
    """Tests for list_screen_tabs.py script."""

    def test_list_screen_tabs(self, mock_jira_client, default_screen_tabs):
        """Test listing all tabs for a screen."""
        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs

        from list_screen_tabs import list_screen_tabs
        result = list_screen_tabs(screen_id=1, client=mock_jira_client)

        assert len(result) == 2
        assert result[0]['name'] == 'Field Tab'
        assert result[1]['name'] == 'Custom Fields'

    def test_list_tabs_with_field_count(self, mock_jira_client, default_screen_tabs,
                                         field_tab_fields, custom_fields_tab_fields):
        """Test including field count per tab."""
        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs
        mock_jira_client.get_screen_tab_fields.side_effect = [
            field_tab_fields,
            custom_fields_tab_fields
        ]

        from list_screen_tabs import list_screen_tabs
        result = list_screen_tabs(screen_id=1, client=mock_jira_client, show_field_count=True)

        assert 'field_count' in result[0]
        assert result[0]['field_count'] == 7
        assert result[1]['field_count'] == 2

    def test_list_tabs_format_text(self, mock_jira_client, default_screen_tabs):
        """Test human-readable table output."""
        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs

        from list_screen_tabs import list_screen_tabs, format_tabs_output
        tabs = list_screen_tabs(screen_id=1, client=mock_jira_client)
        output = format_tabs_output(tabs, screen_name="Default Screen", output_format='text')

        assert 'Field Tab' in output
        assert 'Custom Fields' in output

    def test_list_tabs_format_json(self, mock_jira_client, default_screen_tabs):
        """Test JSON output format."""
        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs

        from list_screen_tabs import list_screen_tabs, format_tabs_output
        tabs = list_screen_tabs(screen_id=1, client=mock_jira_client)
        output = format_tabs_output(tabs, screen_name="Default Screen", output_format='json')

        parsed = json.loads(output)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_screen_not_found(self, mock_jira_client):
        """Test error handling for invalid screen ID."""
        from error_handler import NotFoundError
        mock_jira_client.get_screen_tabs.side_effect = NotFoundError("Screen 999 not found")

        from list_screen_tabs import list_screen_tabs
        with pytest.raises(NotFoundError):
            list_screen_tabs(screen_id=999, client=mock_jira_client)


# ========== Test get_screen_fields.py ==========

@pytest.mark.admin
@pytest.mark.unit
class TestGetScreenFields:
    """Tests for get_screen_fields.py script."""

    def test_get_screen_tab_fields(self, mock_jira_client, field_tab_fields):
        """Test getting all fields for a specific tab."""
        mock_jira_client.get_screen_tab_fields.return_value = field_tab_fields

        from get_screen_fields import get_screen_fields
        result = get_screen_fields(screen_id=1, tab_id=10000, client=mock_jira_client)

        assert len(result) == 7
        assert result[0]['id'] == 'summary'

    def test_get_all_screen_fields(self, mock_jira_client, default_screen_tabs,
                                    field_tab_fields, custom_fields_tab_fields):
        """Test getting fields from all tabs when no tab specified."""
        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs
        mock_jira_client.get_screen_tab_fields.side_effect = [
            field_tab_fields,
            custom_fields_tab_fields
        ]

        from get_screen_fields import get_screen_fields
        result = get_screen_fields(screen_id=1, client=mock_jira_client)

        # Should get fields from both tabs
        assert len(result) == 9

    def test_filter_fields_by_type(self, mock_jira_client, default_screen_tabs,
                                    field_tab_fields, custom_fields_tab_fields):
        """Test filtering fields by type (system vs custom)."""
        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs
        mock_jira_client.get_screen_tab_fields.side_effect = [
            field_tab_fields,
            custom_fields_tab_fields
        ]

        from get_screen_fields import get_screen_fields
        result = get_screen_fields(screen_id=1, client=mock_jira_client, field_type='custom')

        # Should only get custom fields
        for field in result:
            assert field['id'].startswith('customfield_')

    def test_show_field_details(self, mock_jira_client, field_tab_fields):
        """Test showing detailed field information."""
        mock_jira_client.get_screen_tab_fields.return_value = field_tab_fields

        from get_screen_fields import get_screen_fields, format_fields_output
        fields = get_screen_fields(screen_id=1, tab_id=10000, client=mock_jira_client)
        output = format_fields_output(fields, output_format='text')

        assert 'Summary' in output
        assert 'summary' in output

    def test_format_text_output(self, mock_jira_client, field_tab_fields):
        """Test human-readable table output."""
        mock_jira_client.get_screen_tab_fields.return_value = field_tab_fields

        from get_screen_fields import get_screen_fields, format_fields_output
        fields = get_screen_fields(screen_id=1, tab_id=10000, client=mock_jira_client)
        output = format_fields_output(fields, output_format='text')

        assert 'Field ID' in output or 'summary' in output

    def test_format_json_output(self, mock_jira_client, field_tab_fields):
        """Test JSON output format."""
        mock_jira_client.get_screen_tab_fields.return_value = field_tab_fields

        from get_screen_fields import get_screen_fields, format_fields_output
        fields = get_screen_fields(screen_id=1, tab_id=10000, client=mock_jira_client)
        output = format_fields_output(fields, output_format='json')

        parsed = json.loads(output)
        assert isinstance(parsed, list)


# ========== Test add_field_to_screen.py ==========

@pytest.mark.admin
@pytest.mark.unit
class TestAddFieldToScreen:
    """Tests for add_field_to_screen.py script."""

    def test_add_field_to_tab(self, mock_jira_client, added_field_response):
        """Test adding field to specific tab."""
        mock_jira_client.add_field_to_screen_tab.return_value = added_field_response

        from add_field_to_screen import add_field_to_screen
        result = add_field_to_screen(
            screen_id=1,
            tab_id=10001,
            field_id='customfield_10020',
            client=mock_jira_client
        )

        assert result is not None
        assert result['id'] == 'customfield_10020'
        mock_jira_client.add_field_to_screen_tab.assert_called_once_with(1, 10001, 'customfield_10020')

    def test_add_field_to_default_tab(self, mock_jira_client, single_tab, added_field_response):
        """Test adding field to first tab when no tab specified."""
        mock_jira_client.get_screen_tabs.return_value = single_tab
        mock_jira_client.add_field_to_screen_tab.return_value = added_field_response

        from add_field_to_screen import add_field_to_screen
        result = add_field_to_screen(
            screen_id=1,
            field_id='customfield_10020',
            client=mock_jira_client
        )

        assert result is not None
        # Should use the first tab's ID
        mock_jira_client.add_field_to_screen_tab.assert_called_once_with(1, 10000, 'customfield_10020')

    def test_add_field_already_exists(self, mock_jira_client):
        """Test error handling when field already on screen."""
        from error_handler import ValidationError
        mock_jira_client.add_field_to_screen_tab.side_effect = ValidationError(
            "Field already exists on this screen"
        )

        from add_field_to_screen import add_field_to_screen
        with pytest.raises(ValidationError):
            add_field_to_screen(
                screen_id=1,
                tab_id=10001,
                field_id='summary',
                client=mock_jira_client
            )

    def test_add_field_invalid_field_id(self, mock_jira_client):
        """Test error handling for invalid field ID."""
        from error_handler import ValidationError
        mock_jira_client.add_field_to_screen_tab.side_effect = ValidationError(
            "Field does not exist"
        )

        from add_field_to_screen import add_field_to_screen
        with pytest.raises(ValidationError):
            add_field_to_screen(
                screen_id=1,
                tab_id=10001,
                field_id='invalid_field',
                client=mock_jira_client
            )

    def test_add_field_dry_run(self, mock_jira_client, default_screen_tabs, available_fields):
        """Test dry-run mode without making changes."""
        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs
        mock_jira_client.get_screen_available_fields.return_value = available_fields

        from add_field_to_screen import add_field_to_screen
        result = add_field_to_screen(
            screen_id=1,
            field_id='customfield_10020',
            client=mock_jira_client,
            dry_run=True
        )

        # Should not call the actual add method
        mock_jira_client.add_field_to_screen_tab.assert_not_called()
        assert result.get('dry_run', False) is True

    def test_add_field_with_tab_name(self, mock_jira_client, default_screen_tabs, added_field_response):
        """Test adding field by tab name instead of ID."""
        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs
        mock_jira_client.add_field_to_screen_tab.return_value = added_field_response

        from add_field_to_screen import add_field_to_screen
        result = add_field_to_screen(
            screen_id=1,
            tab_name='Custom Fields',
            field_id='customfield_10020',
            client=mock_jira_client
        )

        # Should find tab by name and use its ID
        mock_jira_client.add_field_to_screen_tab.assert_called_once_with(1, 10001, 'customfield_10020')


# ========== Test remove_field_from_screen.py ==========

@pytest.mark.admin
@pytest.mark.unit
class TestRemoveFieldFromScreen:
    """Tests for remove_field_from_screen.py script."""

    def test_remove_field_from_tab(self, mock_jira_client):
        """Test removing field from specific tab."""
        mock_jira_client.remove_field_from_screen_tab.return_value = None

        from remove_field_from_screen import remove_field_from_screen
        result = remove_field_from_screen(
            screen_id=1,
            tab_id=10001,
            field_id='customfield_10016',
            client=mock_jira_client
        )

        assert result is True
        mock_jira_client.remove_field_from_screen_tab.assert_called_once_with(1, 10001, 'customfield_10016')

    def test_remove_field_search_all_tabs(self, mock_jira_client, default_screen_tabs,
                                           field_tab_fields, custom_fields_tab_fields):
        """Test finding and removing field from any tab."""
        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs
        mock_jira_client.get_screen_tab_fields.side_effect = [
            field_tab_fields,
            custom_fields_tab_fields
        ]
        mock_jira_client.remove_field_from_screen_tab.return_value = None

        from remove_field_from_screen import remove_field_from_screen
        result = remove_field_from_screen(
            screen_id=1,
            field_id='customfield_10016',  # In Custom Fields tab
            client=mock_jira_client
        )

        assert result is True
        # Should find field in second tab and remove from there
        mock_jira_client.remove_field_from_screen_tab.assert_called_once_with(1, 10001, 'customfield_10016')

    def test_remove_field_not_found(self, mock_jira_client, default_screen_tabs,
                                     field_tab_fields, custom_fields_tab_fields):
        """Test error handling when field not on screen."""
        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs
        mock_jira_client.get_screen_tab_fields.side_effect = [
            field_tab_fields,
            custom_fields_tab_fields
        ]

        from remove_field_from_screen import remove_field_from_screen
        from error_handler import NotFoundError

        with pytest.raises(NotFoundError):
            remove_field_from_screen(
                screen_id=1,
                field_id='nonexistent_field',
                client=mock_jira_client
            )

    def test_remove_field_dry_run(self, mock_jira_client, default_screen_tabs, custom_fields_tab_fields):
        """Test dry-run mode without making changes."""
        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs
        mock_jira_client.get_screen_tab_fields.return_value = custom_fields_tab_fields

        from remove_field_from_screen import remove_field_from_screen
        result = remove_field_from_screen(
            screen_id=1,
            tab_id=10001,
            field_id='customfield_10016',
            client=mock_jira_client,
            dry_run=True
        )

        # Should not call the actual remove method
        mock_jira_client.remove_field_from_screen_tab.assert_not_called()
        assert result.get('dry_run', False) is True

    def test_remove_required_field_warning(self, mock_jira_client, field_tab_fields):
        """Test warning when removing required field."""
        mock_jira_client.get_screen_tab_fields.return_value = field_tab_fields

        from remove_field_from_screen import remove_field_from_screen, is_required_field

        # summary is typically a required field
        assert is_required_field('summary') is True

    def test_remove_field_force(self, mock_jira_client):
        """Test force removal without confirmation."""
        mock_jira_client.remove_field_from_screen_tab.return_value = None

        from remove_field_from_screen import remove_field_from_screen
        result = remove_field_from_screen(
            screen_id=1,
            tab_id=10001,
            field_id='summary',
            client=mock_jira_client,
            force=True
        )

        assert result is True
        mock_jira_client.remove_field_from_screen_tab.assert_called_once()
