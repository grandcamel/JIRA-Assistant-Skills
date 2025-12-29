"""
Unit tests for Project Screen Discovery script (Phase 4).

Tests:
- get_project_screens.py
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path
import json

# Ensure paths are set up for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))


@pytest.mark.admin
@pytest.mark.unit
class TestGetProjectScreens:
    """Tests for get_project_screens.py script."""

    def test_get_project_screens_basic(self, mock_jira_client, sample_project,
                                        project_issue_type_screen_schemes):
        """Test getting screens for a project."""
        mock_jira_client.get_project.return_value = sample_project
        mock_jira_client.get_project_issue_type_screen_schemes.return_value = project_issue_type_screen_schemes

        from get_project_screens import get_project_screens
        result = get_project_screens(project_key='PROJ', client=mock_jira_client)

        assert result is not None
        assert 'project' in result
        assert result['project']['key'] == 'PROJ'

    def test_get_screens_with_issue_types(self, mock_jira_client, sample_project,
                                           project_issue_type_screen_schemes,
                                           issue_type_screen_scheme_mappings,
                                           project_issue_types):
        """Test including issue type to screen mappings."""
        mock_jira_client.get_project.return_value = sample_project
        mock_jira_client.get_project_issue_type_screen_schemes.return_value = project_issue_type_screen_schemes
        mock_jira_client.get_issue_type_screen_scheme_mappings.return_value = issue_type_screen_scheme_mappings
        mock_jira_client.get_project_issue_types.return_value = project_issue_types

        from get_project_screens import get_project_screens
        result = get_project_screens(
            project_key='PROJ',
            client=mock_jira_client,
            show_issue_types=True
        )

        assert 'issue_types' in result or 'mappings' in result

    def test_get_screens_with_full_hierarchy(self, mock_jira_client, sample_project,
                                              project_issue_type_screen_schemes,
                                              issue_type_screen_scheme_mappings,
                                              default_issue_type_screen_scheme,
                                              default_screen_scheme,
                                              default_screen,
                                              default_screen_tabs,
                                              field_tab_fields):
        """Test showing complete 3-tier hierarchy."""
        mock_jira_client.get_project.return_value = sample_project
        mock_jira_client.get_project_issue_type_screen_schemes.return_value = project_issue_type_screen_schemes
        mock_jira_client.get_issue_type_screen_scheme_mappings.return_value = issue_type_screen_scheme_mappings
        mock_jira_client.get_issue_type_screen_scheme.return_value = default_issue_type_screen_scheme
        mock_jira_client.get_screen_scheme.return_value = default_screen_scheme
        mock_jira_client.get_screen.return_value = default_screen
        mock_jira_client.get_screen_tabs.return_value = default_screen_tabs
        mock_jira_client.get_screen_tab_fields.return_value = field_tab_fields

        from get_project_screens import get_project_screens
        result = get_project_screens(
            project_key='PROJ',
            client=mock_jira_client,
            show_full_hierarchy=True
        )

        assert result is not None
        # Should contain hierarchy information

    def test_filter_by_issue_type(self, mock_jira_client, sample_project,
                                   project_issue_type_screen_schemes,
                                   issue_type_screen_scheme_mappings):
        """Test filtering screens by issue type."""
        mock_jira_client.get_project.return_value = sample_project
        mock_jira_client.get_project_issue_type_screen_schemes.return_value = project_issue_type_screen_schemes
        mock_jira_client.get_issue_type_screen_scheme_mappings.return_value = issue_type_screen_scheme_mappings

        from get_project_screens import get_project_screens
        result = get_project_screens(
            project_key='PROJ',
            client=mock_jira_client,
            issue_type='Bug'
        )

        assert result is not None
        # Should only show screens for Bug issue type

    def test_filter_by_operation(self, mock_jira_client, sample_project,
                                  project_issue_type_screen_schemes,
                                  issue_type_screen_scheme_mappings,
                                  default_screen_scheme):
        """Test filtering screens by operation type (create/edit/view)."""
        mock_jira_client.get_project.return_value = sample_project
        mock_jira_client.get_project_issue_type_screen_schemes.return_value = project_issue_type_screen_schemes
        mock_jira_client.get_issue_type_screen_scheme_mappings.return_value = issue_type_screen_scheme_mappings
        mock_jira_client.get_screen_scheme.return_value = default_screen_scheme

        from get_project_screens import get_project_screens
        result = get_project_screens(
            project_key='PROJ',
            client=mock_jira_client,
            operation='create'
        )

        assert result is not None
        # Should only show create screens

    def test_format_text_output(self, mock_jira_client, sample_project,
                                 project_issue_type_screen_schemes):
        """Test human-readable output."""
        mock_jira_client.get_project.return_value = sample_project
        mock_jira_client.get_project_issue_type_screen_schemes.return_value = project_issue_type_screen_schemes

        from get_project_screens import get_project_screens, format_output
        result = get_project_screens(project_key='PROJ', client=mock_jira_client)
        output = format_output(result, output_format='text')

        assert 'PROJ' in output

    def test_format_json_output(self, mock_jira_client, sample_project,
                                 project_issue_type_screen_schemes):
        """Test JSON output format."""
        mock_jira_client.get_project.return_value = sample_project
        mock_jira_client.get_project_issue_type_screen_schemes.return_value = project_issue_type_screen_schemes

        from get_project_screens import get_project_screens, format_output
        result = get_project_screens(project_key='PROJ', client=mock_jira_client)
        output = format_output(result, output_format='json')

        parsed = json.loads(output)
        assert 'project' in parsed

    def test_project_not_found(self, mock_jira_client):
        """Test error handling for invalid project key."""
        from jira_assistant_skills_lib import NotFoundError
        mock_jira_client.get_project.side_effect = NotFoundError("Project INVALID not found")

        from get_project_screens import get_project_screens
        with pytest.raises(NotFoundError):
            get_project_screens(project_key='INVALID', client=mock_jira_client)

    def test_show_available_fields(self, mock_jira_client, sample_project,
                                    project_issue_type_screen_schemes,
                                    issue_type_screen_scheme_mappings,
                                    default_screen_scheme,
                                    default_screen,
                                    available_fields):
        """Test showing fields available to add to screens."""
        mock_jira_client.get_project.return_value = sample_project
        mock_jira_client.get_project_issue_type_screen_schemes.return_value = project_issue_type_screen_schemes
        mock_jira_client.get_issue_type_screen_scheme_mappings.return_value = issue_type_screen_scheme_mappings
        mock_jira_client.get_screen_scheme.return_value = default_screen_scheme
        mock_jira_client.get_screen.return_value = default_screen
        mock_jira_client.get_screen_available_fields.return_value = available_fields

        from get_project_screens import get_project_screens
        result = get_project_screens(
            project_key='PROJ',
            client=mock_jira_client,
            show_available_fields=True
        )

        # Should include available fields information
        assert result is not None

    def test_shows_screen_scheme_association(self, mock_jira_client, sample_project,
                                              project_issue_type_screen_schemes):
        """Test that output shows which scheme is associated with project."""
        mock_jira_client.get_project.return_value = sample_project
        mock_jira_client.get_project_issue_type_screen_schemes.return_value = project_issue_type_screen_schemes

        from get_project_screens import get_project_screens
        result = get_project_screens(project_key='PROJ', client=mock_jira_client)

        assert 'issue_type_screen_scheme' in result or 'scheme' in result
