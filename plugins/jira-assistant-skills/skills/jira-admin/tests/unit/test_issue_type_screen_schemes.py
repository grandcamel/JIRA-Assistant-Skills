"""
Unit tests for Issue Type Screen Schemes scripts (Phase 3).

Tests:
- list_issue_type_screen_schemes.py
- get_issue_type_screen_scheme.py
"""

import sys
from pathlib import Path

# Add paths BEFORE any other imports
test_dir = Path(__file__).parent  # unit
tests_dir = test_dir.parent  # tests
jira_admin_dir = tests_dir.parent  # jira-admin
skills_dir = jira_admin_dir.parent  # skills
shared_lib_path = skills_dir / 'shared' / 'scripts' / 'lib'
scripts_path = jira_admin_dir / 'scripts'

sys.path.insert(0, str(shared_lib_path))
sys.path.insert(0, str(scripts_path))

import pytest
from unittest.mock import Mock, patch
import json


# ========== Test list_issue_type_screen_schemes.py ==========

@pytest.mark.admin
@pytest.mark.unit
class TestListIssueTypeScreenSchemes:
    """Tests for list_issue_type_screen_schemes.py script."""

    def test_list_all_issue_type_screen_schemes(self, mock_jira_client, issue_type_screen_schemes_response):
        """Test listing all issue type screen schemes."""
        mock_jira_client.get_issue_type_screen_schemes.return_value = issue_type_screen_schemes_response

        from list_issue_type_screen_schemes import list_issue_type_screen_schemes
        result = list_issue_type_screen_schemes(client=mock_jira_client)

        assert result is not None
        assert len(result) == 3
        mock_jira_client.get_issue_type_screen_schemes.assert_called_once()

    def test_list_schemes_with_projects(self, mock_jira_client,
                                         issue_type_screen_schemes_response,
                                         project_issue_type_screen_schemes):
        """Test including project associations."""
        mock_jira_client.get_issue_type_screen_schemes.return_value = issue_type_screen_schemes_response
        mock_jira_client.get_project_issue_type_screen_schemes.return_value = project_issue_type_screen_schemes

        from list_issue_type_screen_schemes import list_issue_type_screen_schemes
        result = list_issue_type_screen_schemes(client=mock_jira_client, show_projects=True)

        assert result is not None
        # Should include project information

    def test_filter_schemes_by_name(self, mock_jira_client, issue_type_screen_schemes_response):
        """Test filtering schemes by name pattern."""
        mock_jira_client.get_issue_type_screen_schemes.return_value = issue_type_screen_schemes_response

        from list_issue_type_screen_schemes import list_issue_type_screen_schemes
        result = list_issue_type_screen_schemes(client=mock_jira_client, filter_pattern="Default")

        assert all("Default" in scheme['name'] for scheme in result)

    def test_format_text_output(self, mock_jira_client, issue_type_screen_schemes_response):
        """Test human-readable table output."""
        mock_jira_client.get_issue_type_screen_schemes.return_value = issue_type_screen_schemes_response

        from list_issue_type_screen_schemes import list_issue_type_screen_schemes, format_schemes_output
        schemes = list_issue_type_screen_schemes(client=mock_jira_client)
        output = format_schemes_output(schemes, output_format='text')

        assert 'Default Issue Type Screen Scheme' in output

    def test_format_json_output(self, mock_jira_client, issue_type_screen_schemes_response):
        """Test JSON output format."""
        mock_jira_client.get_issue_type_screen_schemes.return_value = issue_type_screen_schemes_response

        from list_issue_type_screen_schemes import list_issue_type_screen_schemes, format_schemes_output
        schemes = list_issue_type_screen_schemes(client=mock_jira_client)
        output = format_schemes_output(schemes, output_format='json')

        parsed = json.loads(output)
        assert isinstance(parsed, list)
        assert len(parsed) == 3

    def test_empty_schemes(self, mock_jira_client, empty_issue_type_screen_schemes_response):
        """Test output when no schemes exist."""
        mock_jira_client.get_issue_type_screen_schemes.return_value = empty_issue_type_screen_schemes_response

        from list_issue_type_screen_schemes import list_issue_type_screen_schemes
        result = list_issue_type_screen_schemes(client=mock_jira_client)

        assert result == []


# ========== Test get_issue_type_screen_scheme.py ==========

@pytest.mark.admin
@pytest.mark.unit
class TestGetIssueTypeScreenScheme:
    """Tests for get_issue_type_screen_scheme.py script."""

    def test_get_issue_type_screen_scheme_basic(self, mock_jira_client, default_issue_type_screen_scheme):
        """Test getting basic scheme details."""
        mock_jira_client.get_issue_type_screen_scheme.return_value = default_issue_type_screen_scheme

        from get_issue_type_screen_scheme import get_issue_type_screen_scheme
        result = get_issue_type_screen_scheme(scheme_id=10000, client=mock_jira_client)

        assert result is not None
        assert result['id'] == '10000'
        assert result['name'] == 'Default Issue Type Screen Scheme'

    def test_get_scheme_with_mappings(self, mock_jira_client,
                                       default_issue_type_screen_scheme,
                                       issue_type_screen_scheme_mappings):
        """Test including issue type to screen scheme mappings."""
        mock_jira_client.get_issue_type_screen_scheme.return_value = default_issue_type_screen_scheme
        mock_jira_client.get_issue_type_screen_scheme_mappings.return_value = issue_type_screen_scheme_mappings

        from get_issue_type_screen_scheme import get_issue_type_screen_scheme
        result = get_issue_type_screen_scheme(
            scheme_id=10000,
            client=mock_jira_client,
            show_mappings=True
        )

        assert 'mappings' in result

    def test_get_scheme_with_projects(self, mock_jira_client,
                                       default_issue_type_screen_scheme,
                                       project_issue_type_screen_schemes):
        """Test including associated projects."""
        mock_jira_client.get_issue_type_screen_scheme.return_value = default_issue_type_screen_scheme
        mock_jira_client.get_project_issue_type_screen_schemes.return_value = project_issue_type_screen_schemes

        from get_issue_type_screen_scheme import get_issue_type_screen_scheme
        result = get_issue_type_screen_scheme(
            scheme_id=10000,
            client=mock_jira_client,
            show_projects=True
        )

        assert 'projects' in result or 'project_ids' in result

    def test_get_scheme_not_found(self, mock_jira_client):
        """Test error handling for invalid scheme ID."""
        from jira_assistant_skills_lib import NotFoundError
        mock_jira_client.get_issue_type_screen_scheme.side_effect = NotFoundError(
            "Issue type screen scheme 99999 not found"
        )

        from get_issue_type_screen_scheme import get_issue_type_screen_scheme
        with pytest.raises(NotFoundError):
            get_issue_type_screen_scheme(scheme_id=99999, client=mock_jira_client)

    def test_format_detailed_output(self, mock_jira_client,
                                     default_issue_type_screen_scheme,
                                     issue_type_screen_scheme_mappings):
        """Test detailed human-readable output."""
        mock_jira_client.get_issue_type_screen_scheme.return_value = default_issue_type_screen_scheme
        mock_jira_client.get_issue_type_screen_scheme_mappings.return_value = issue_type_screen_scheme_mappings

        from get_issue_type_screen_scheme import get_issue_type_screen_scheme, format_scheme_output
        result = get_issue_type_screen_scheme(
            scheme_id=10000,
            client=mock_jira_client,
            show_mappings=True
        )
        output = format_scheme_output(result, output_format='text')

        assert 'Default Issue Type Screen Scheme' in output
