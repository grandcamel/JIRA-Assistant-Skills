"""
Tests for Issue Type Scheme assignment and project management.

Following TDD: Tests are written FIRST and should pass after implementation.
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


@pytest.mark.admin
@pytest.mark.unit
class TestGetProjectScheme:
    """Test suite for get_project_issue_type_scheme.py functionality."""

    def test_get_project_scheme_success(
        self, mock_jira_client, scheme_for_projects_response
    ):
        """Should retrieve scheme for a project."""
        mock_jira_client.get_issue_type_scheme_for_projects.return_value = scheme_for_projects_response

        from get_project_issue_type_scheme import get_project_issue_type_scheme

        result = get_project_issue_type_scheme(
            project_id='10000',
            client=mock_jira_client
        )

        assert result is not None
        assert result['issueTypeScheme']['id'] == '10000'
        mock_jira_client.get_issue_type_scheme_for_projects.assert_called_once()

    def test_get_project_scheme_not_found(self, mock_jira_client):
        """Should handle project with no scheme assignment."""
        mock_jira_client.get_issue_type_scheme_for_projects.return_value = {
            'values': [],
            'total': 0
        }

        from get_project_issue_type_scheme import get_project_issue_type_scheme
        from jira_assistant_skills_lib import NotFoundError

        with pytest.raises(NotFoundError):
            get_project_issue_type_scheme(
                project_id='99999',
                client=mock_jira_client
            )


@pytest.mark.admin
@pytest.mark.unit
class TestAssignScheme:
    """Test suite for assign_issue_type_scheme.py functionality."""

    def test_assign_scheme_success(self, mock_jira_client):
        """Should assign scheme to project."""
        mock_jira_client.assign_issue_type_scheme.return_value = None

        from assign_issue_type_scheme import assign_issue_type_scheme

        result = assign_issue_type_scheme(
            scheme_id='10001',
            project_id='10000',
            client=mock_jira_client
        )

        assert result is True
        mock_jira_client.assign_issue_type_scheme.assert_called_once_with(
            scheme_id='10001',
            project_id='10000'
        )

    def test_assign_scheme_dry_run(self, mock_jira_client):
        """Should support dry run."""
        from assign_issue_type_scheme import assign_issue_type_scheme

        result = assign_issue_type_scheme(
            scheme_id='10001',
            project_id='10000',
            client=mock_jira_client,
            dry_run=True
        )

        assert result is True
        mock_jira_client.assign_issue_type_scheme.assert_not_called()

    def test_assign_scheme_team_managed_fails(self, mock_jira_client):
        """Should fail for team-managed projects."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.assign_issue_type_scheme.side_effect = JiraError(
            "Issue type scheme can only be associated with company-managed projects",
            status_code=400
        )

        from assign_issue_type_scheme import assign_issue_type_scheme

        with pytest.raises(JiraError):
            assign_issue_type_scheme(
                scheme_id='10001',
                project_id='10000',
                client=mock_jira_client
            )


@pytest.mark.admin
@pytest.mark.unit
class TestGetSchemeMappings:
    """Test suite for get_issue_type_scheme_mappings.py functionality."""

    def test_get_scheme_mappings_success(
        self, mock_jira_client, scheme_mappings_response
    ):
        """Should retrieve all mappings."""
        mock_jira_client.get_issue_type_scheme_items.return_value = scheme_mappings_response

        from get_issue_type_scheme_mappings import get_issue_type_scheme_mappings

        result = get_issue_type_scheme_mappings(client=mock_jira_client)

        assert result is not None
        assert len(result['values']) == 4
        mock_jira_client.get_issue_type_scheme_items.assert_called_once()

    def test_get_scheme_mappings_filter_by_scheme(
        self, mock_jira_client, scheme_mappings_response
    ):
        """Should filter mappings by scheme ID."""
        mock_jira_client.get_issue_type_scheme_items.return_value = scheme_mappings_response

        from get_issue_type_scheme_mappings import get_issue_type_scheme_mappings

        result = get_issue_type_scheme_mappings(
            scheme_ids=['10000'],
            client=mock_jira_client
        )

        call_args = mock_jira_client.get_issue_type_scheme_items.call_args
        assert call_args[1]['scheme_ids'] == ['10000']


@pytest.mark.admin
@pytest.mark.unit
class TestAddIssueTypesToScheme:
    """Test suite for add_issue_types_to_scheme.py functionality."""

    def test_add_issue_types_success(self, mock_jira_client):
        """Should add issue types to scheme."""
        mock_jira_client.add_issue_types_to_scheme.return_value = None

        from add_issue_types_to_scheme import add_issue_types_to_scheme

        result = add_issue_types_to_scheme(
            scheme_id='10001',
            issue_type_ids=['10003', '10004'],
            client=mock_jira_client
        )

        assert result is True
        mock_jira_client.add_issue_types_to_scheme.assert_called_once_with(
            scheme_id='10001',
            issue_type_ids=['10003', '10004']
        )

    def test_add_issue_types_empty_list(self, mock_jira_client):
        """Should raise ValidationError for empty list."""
        from add_issue_types_to_scheme import add_issue_types_to_scheme
        from jira_assistant_skills_lib import ValidationError

        with pytest.raises(ValidationError):
            add_issue_types_to_scheme(
                scheme_id='10001',
                issue_type_ids=[],
                client=mock_jira_client
            )


@pytest.mark.admin
@pytest.mark.unit
class TestRemoveIssueTypeFromScheme:
    """Test suite for remove_issue_type_from_scheme.py functionality."""

    def test_remove_issue_type_success(self, mock_jira_client):
        """Should remove issue type from scheme."""
        mock_jira_client.remove_issue_type_from_scheme.return_value = None

        from remove_issue_type_from_scheme import remove_issue_type_from_scheme

        result = remove_issue_type_from_scheme(
            scheme_id='10001',
            issue_type_id='10003',
            client=mock_jira_client
        )

        assert result is True
        mock_jira_client.remove_issue_type_from_scheme.assert_called_once_with(
            scheme_id='10001',
            issue_type_id='10003'
        )

    def test_remove_default_issue_type_fails(self, mock_jira_client):
        """Should fail when removing default issue type."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.remove_issue_type_from_scheme.side_effect = JiraError(
            "Cannot remove the default issue type from the scheme",
            status_code=400
        )

        from remove_issue_type_from_scheme import remove_issue_type_from_scheme

        with pytest.raises(JiraError):
            remove_issue_type_from_scheme(
                scheme_id='10001',
                issue_type_id='10001',
                client=mock_jira_client
            )

    def test_remove_last_issue_type_fails(self, mock_jira_client):
        """Should fail when removing last issue type."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.remove_issue_type_from_scheme.side_effect = JiraError(
            "Cannot remove the last issue type from the scheme",
            status_code=400
        )

        from remove_issue_type_from_scheme import remove_issue_type_from_scheme

        with pytest.raises(JiraError):
            remove_issue_type_from_scheme(
                scheme_id='10001',
                issue_type_id='10001',
                client=mock_jira_client
            )


@pytest.mark.admin
@pytest.mark.unit
class TestReorderIssueTypesInScheme:
    """Test suite for reorder_issue_types_in_scheme.py functionality."""

    def test_reorder_move_to_first(self, mock_jira_client):
        """Should move issue type to first position."""
        mock_jira_client.reorder_issue_types_in_scheme.return_value = None

        from reorder_issue_types_in_scheme import reorder_issue_types_in_scheme

        result = reorder_issue_types_in_scheme(
            scheme_id='10001',
            issue_type_id='10003',
            client=mock_jira_client
        )

        assert result is True
        call_args = mock_jira_client.reorder_issue_types_in_scheme.call_args
        assert call_args[1]['issue_type_id'] == '10003'
        assert call_args[1]['after'] is None

    def test_reorder_move_after(self, mock_jira_client):
        """Should move issue type after another."""
        mock_jira_client.reorder_issue_types_in_scheme.return_value = None

        from reorder_issue_types_in_scheme import reorder_issue_types_in_scheme

        result = reorder_issue_types_in_scheme(
            scheme_id='10001',
            issue_type_id='10003',
            after='10001',
            client=mock_jira_client
        )

        assert result is True
        call_args = mock_jira_client.reorder_issue_types_in_scheme.call_args
        assert call_args[1]['after'] == '10001'
