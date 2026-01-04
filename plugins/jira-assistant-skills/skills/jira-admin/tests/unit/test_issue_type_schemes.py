"""
Tests for Issue Type Scheme management scripts.

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
class TestListIssueTypeSchemes:
    """Test suite for list_issue_type_schemes.py functionality."""

    def test_list_issue_type_schemes_success(
        self, mock_jira_client, issue_type_schemes_response
    ):
        """Should return paginated list of schemes."""
        mock_jira_client.get_issue_type_schemes.return_value = issue_type_schemes_response

        from list_issue_type_schemes import list_issue_type_schemes

        result = list_issue_type_schemes(client=mock_jira_client)

        assert result is not None
        assert len(result['values']) == 2
        assert result['values'][0]['name'] == 'Default Issue Type Scheme'
        mock_jira_client.get_issue_type_schemes.assert_called_once()

    def test_list_issue_type_schemes_with_pagination(
        self, mock_jira_client, issue_type_schemes_response
    ):
        """Should support pagination parameters."""
        mock_jira_client.get_issue_type_schemes.return_value = issue_type_schemes_response

        from list_issue_type_schemes import list_issue_type_schemes

        result = list_issue_type_schemes(
            client=mock_jira_client,
            start_at=10,
            max_results=25
        )

        call_args = mock_jira_client.get_issue_type_schemes.call_args
        assert call_args[1]['start_at'] == 10
        assert call_args[1]['max_results'] == 25

    def test_list_issue_type_schemes_filter_by_id(
        self, mock_jira_client, issue_type_schemes_response
    ):
        """Should support filtering by scheme IDs."""
        mock_jira_client.get_issue_type_schemes.return_value = issue_type_schemes_response

        from list_issue_type_schemes import list_issue_type_schemes

        result = list_issue_type_schemes(
            client=mock_jira_client,
            scheme_ids=['10000', '10001']
        )

        call_args = mock_jira_client.get_issue_type_schemes.call_args
        assert call_args[1]['scheme_ids'] == ['10000', '10001']

    def test_list_issue_type_schemes_empty(self, mock_jira_client):
        """Should handle empty result."""
        mock_jira_client.get_issue_type_schemes.return_value = {
            'values': [],
            'total': 0,
            'startAt': 0,
            'maxResults': 50,
            'isLast': True
        }

        from list_issue_type_schemes import list_issue_type_schemes

        result = list_issue_type_schemes(client=mock_jira_client)

        assert result['values'] == []
        assert result['total'] == 0


@pytest.mark.admin
@pytest.mark.unit
class TestGetIssueTypeScheme:
    """Test suite for get_issue_type_scheme.py functionality."""

    def test_get_issue_type_scheme_by_id(
        self, mock_jira_client, default_scheme_response
    ):
        """Should retrieve scheme by ID."""
        mock_jira_client.get_issue_type_schemes.return_value = {
            'values': [default_scheme_response],
            'total': 1
        }

        from get_issue_type_scheme import get_issue_type_scheme

        result = get_issue_type_scheme(
            scheme_id='10000',
            client=mock_jira_client
        )

        assert result is not None
        assert result['id'] == '10000'
        assert result['name'] == 'Default Issue Type Scheme'

    def test_get_issue_type_scheme_with_items(
        self, mock_jira_client, default_scheme_response, scheme_mappings_response
    ):
        """Should include scheme items when requested."""
        mock_jira_client.get_issue_type_schemes.return_value = {
            'values': [default_scheme_response],
            'total': 1
        }
        mock_jira_client.get_issue_type_scheme_items.return_value = scheme_mappings_response

        from get_issue_type_scheme import get_issue_type_scheme

        result = get_issue_type_scheme(
            scheme_id='10000',
            client=mock_jira_client,
            include_items=True
        )

        assert 'items' in result
        mock_jira_client.get_issue_type_scheme_items.assert_called_once()

    def test_get_issue_type_scheme_not_found(self, mock_jira_client):
        """Should raise NotFoundError for invalid ID."""
        mock_jira_client.get_issue_type_schemes.return_value = {
            'values': [],
            'total': 0
        }

        from get_issue_type_scheme import get_issue_type_scheme
        from jira_assistant_skills_lib import NotFoundError

        with pytest.raises(NotFoundError):
            get_issue_type_scheme(
                scheme_id='99999',
                client=mock_jira_client
            )


@pytest.mark.admin
@pytest.mark.unit
class TestCreateIssueTypeScheme:
    """Test suite for create_issue_type_scheme.py functionality."""

    def test_create_issue_type_scheme_success(
        self, mock_jira_client, created_scheme_response
    ):
        """Should create a new scheme."""
        mock_jira_client.create_issue_type_scheme.return_value = created_scheme_response

        from create_issue_type_scheme import create_issue_type_scheme

        result = create_issue_type_scheme(
            name='Test Scheme',
            issue_type_ids=['10001', '10002'],
            client=mock_jira_client
        )

        assert result is not None
        assert 'issueTypeSchemeId' in result
        mock_jira_client.create_issue_type_scheme.assert_called_once()

    def test_create_issue_type_scheme_with_default(
        self, mock_jira_client, created_scheme_response
    ):
        """Should create scheme with default issue type."""
        mock_jira_client.create_issue_type_scheme.return_value = created_scheme_response

        from create_issue_type_scheme import create_issue_type_scheme

        result = create_issue_type_scheme(
            name='Test Scheme',
            issue_type_ids=['10001', '10002'],
            default_issue_type_id='10001',
            client=mock_jira_client
        )

        call_args = mock_jira_client.create_issue_type_scheme.call_args
        assert call_args[1]['default_issue_type_id'] == '10001'

    def test_create_issue_type_scheme_empty_types(self, mock_jira_client):
        """Should raise ValidationError for empty issue type list."""
        from create_issue_type_scheme import create_issue_type_scheme
        from assistant_skills_lib.error_handler import ValidationError

        with pytest.raises(ValidationError):
            create_issue_type_scheme(
                name='Test Scheme',
                issue_type_ids=[],
                client=mock_jira_client
            )

    def test_create_issue_type_scheme_empty_name(self, mock_jira_client):
        """Should raise ValidationError for empty name."""
        from create_issue_type_scheme import create_issue_type_scheme
        from assistant_skills_lib.error_handler import ValidationError

        with pytest.raises(ValidationError):
            create_issue_type_scheme(
                name='',
                issue_type_ids=['10001'],
                client=mock_jira_client
            )


@pytest.mark.admin
@pytest.mark.unit
class TestUpdateIssueTypeScheme:
    """Test suite for update_issue_type_scheme.py functionality."""

    def test_update_issue_type_scheme_name(self, mock_jira_client):
        """Should update scheme name."""
        mock_jira_client.update_issue_type_scheme.return_value = {}

        from update_issue_type_scheme import update_issue_type_scheme

        update_issue_type_scheme(
            scheme_id='10001',
            name='Updated Scheme',
            client=mock_jira_client
        )

        call_args = mock_jira_client.update_issue_type_scheme.call_args
        assert call_args[1]['name'] == 'Updated Scheme'

    def test_update_issue_type_scheme_description(self, mock_jira_client):
        """Should update scheme description."""
        mock_jira_client.update_issue_type_scheme.return_value = {}

        from update_issue_type_scheme import update_issue_type_scheme

        update_issue_type_scheme(
            scheme_id='10001',
            description='New description',
            client=mock_jira_client
        )

        call_args = mock_jira_client.update_issue_type_scheme.call_args
        assert call_args[1]['description'] == 'New description'

    def test_update_issue_type_scheme_default_type(self, mock_jira_client):
        """Should update default issue type."""
        mock_jira_client.update_issue_type_scheme.return_value = {}

        from update_issue_type_scheme import update_issue_type_scheme

        update_issue_type_scheme(
            scheme_id='10001',
            default_issue_type_id='10002',
            client=mock_jira_client
        )

        call_args = mock_jira_client.update_issue_type_scheme.call_args
        assert call_args[1]['default_issue_type_id'] == '10002'

    def test_update_issue_type_scheme_no_changes(self, mock_jira_client):
        """Should raise ValidationError with no update parameters."""
        from update_issue_type_scheme import update_issue_type_scheme
        from assistant_skills_lib.error_handler import ValidationError

        with pytest.raises(ValidationError):
            update_issue_type_scheme(
                scheme_id='10001',
                client=mock_jira_client
            )


@pytest.mark.admin
@pytest.mark.unit
class TestDeleteIssueTypeScheme:
    """Test suite for delete_issue_type_scheme.py functionality."""

    def test_delete_issue_type_scheme_success(self, mock_jira_client):
        """Should delete scheme successfully."""
        mock_jira_client.delete_issue_type_scheme.return_value = None

        from delete_issue_type_scheme import delete_issue_type_scheme

        result = delete_issue_type_scheme(
            scheme_id='10002',
            client=mock_jira_client
        )

        assert result is True
        mock_jira_client.delete_issue_type_scheme.assert_called_once_with('10002')

    def test_delete_issue_type_scheme_dry_run(self, mock_jira_client):
        """Should support dry run."""
        from delete_issue_type_scheme import delete_issue_type_scheme

        result = delete_issue_type_scheme(
            scheme_id='10002',
            client=mock_jira_client,
            dry_run=True
        )

        assert result is True
        mock_jira_client.delete_issue_type_scheme.assert_not_called()

    def test_delete_issue_type_scheme_in_use(self, mock_jira_client):
        """Should raise error if scheme is in use."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.delete_issue_type_scheme.side_effect = JiraError(
            "Cannot delete issue type scheme that is in use",
            status_code=400
        )

        from delete_issue_type_scheme import delete_issue_type_scheme

        with pytest.raises(JiraError):
            delete_issue_type_scheme(
                scheme_id='10000',
                client=mock_jira_client
            )

    def test_delete_default_scheme_fails(self, mock_jira_client):
        """Should fail to delete default scheme."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.delete_issue_type_scheme.side_effect = JiraError(
            "Cannot delete the default issue type scheme",
            status_code=400
        )

        from delete_issue_type_scheme import delete_issue_type_scheme

        with pytest.raises(JiraError):
            delete_issue_type_scheme(
                scheme_id='10000',
                client=mock_jira_client
            )
