"""
Tests for create_filter.py - Create saved filters.
"""

import copy
import pytest
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.search
@pytest.mark.unit
class TestCreateFilter:
    """Tests for creating saved filters."""

    def test_create_filter_minimal(self, mock_jira_client, sample_filter):
        """Test creating filter with name and JQL only."""
        mock_jira_client.create_filter.return_value = sample_filter

        from create_filter import create_filter

        result = create_filter(
            mock_jira_client,
            name='My Bugs',
            jql='project = PROJ AND type = Bug'
        )

        assert result['id'] == '10042'
        assert result['name'] == 'My Bugs'
        mock_jira_client.create_filter.assert_called_once()

    def test_create_filter_with_description(self, mock_jira_client, sample_filter):
        """Test creating filter with description."""
        expected = copy.deepcopy(sample_filter)
        expected['description'] = 'All bugs in the project'
        mock_jira_client.create_filter.return_value = expected

        from create_filter import create_filter

        result = create_filter(
            mock_jira_client,
            name='My Bugs',
            jql='project = PROJ AND type = Bug',
            description='All bugs in the project'
        )

        assert result['description'] == 'All bugs in the project'

    def test_create_filter_as_favourite(self, mock_jira_client, sample_filter):
        """Test creating filter and marking as favourite."""
        expected = copy.deepcopy(sample_filter)
        expected['favourite'] = True
        mock_jira_client.create_filter.return_value = expected

        from create_filter import create_filter

        result = create_filter(
            mock_jira_client,
            name='My Bugs',
            jql='project = PROJ AND type = Bug',
            favourite=True
        )

        assert result['favourite'] is True

    def test_create_filter_shared_project(self, mock_jira_client, sample_filter):
        """Test creating filter shared with project."""
        expected = copy.deepcopy(sample_filter)
        expected['sharePermissions'] = [
            {'type': 'project', 'project': {'id': '10000', 'key': 'PROJ'}}
        ]
        mock_jira_client.create_filter.return_value = expected

        from create_filter import create_filter, build_project_permission

        permission = build_project_permission('10000')
        result = create_filter(
            mock_jira_client,
            name='Project Bugs',
            jql='project = PROJ AND type = Bug',
            share_permissions=[permission]
        )

        assert len(result['sharePermissions']) == 1
        assert result['sharePermissions'][0]['type'] == 'project'

    def test_create_filter_shared_group(self, mock_jira_client, sample_filter):
        """Test creating filter shared with group."""
        expected = copy.deepcopy(sample_filter)
        expected['sharePermissions'] = [
            {'type': 'group', 'group': {'name': 'developers'}}
        ]
        mock_jira_client.create_filter.return_value = expected

        from create_filter import create_filter, build_group_permission

        permission = build_group_permission('developers')
        result = create_filter(
            mock_jira_client,
            name='Team Bugs',
            jql='project = PROJ AND type = Bug',
            share_permissions=[permission]
        )

        assert len(result['sharePermissions']) == 1
        assert result['sharePermissions'][0]['type'] == 'group'

    def test_create_filter_invalid_jql(self, mock_jira_client):
        """Test error handling for invalid JQL."""
        from jira_assistant_skills_lib import ValidationError
        mock_jira_client.create_filter.side_effect = ValidationError(
            "JQL parse error: Field 'projct' does not exist"
        )

        from create_filter import create_filter

        with pytest.raises(ValidationError):
            create_filter(
                mock_jira_client,
                name='Bad Filter',
                jql='projct = PROJ'
            )

    def test_create_filter_duplicate_name(self, mock_jira_client, sample_filter):
        """Test handling duplicate filter names."""
        # JIRA allows duplicate names, so this should succeed
        mock_jira_client.create_filter.return_value = sample_filter

        from create_filter import create_filter

        result = create_filter(
            mock_jira_client,
            name='My Bugs',
            jql='project = PROJ AND type = Bug'
        )

        # Should succeed (JIRA allows duplicate names)
        assert result['name'] == 'My Bugs'


@pytest.mark.search
@pytest.mark.unit
class TestCreateFilterErrorHandling:
    """Test API error handling scenarios for create_filter."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError
        mock_jira_client.create_filter.side_effect = AuthenticationError(
            "Invalid API token"
        )

        from create_filter import create_filter

        with pytest.raises(AuthenticationError):
            create_filter(mock_jira_client, name='Test', jql='project = PROJ')

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError
        mock_jira_client.create_filter.side_effect = PermissionError(
            "You don't have permission to create filters"
        )

        from create_filter import create_filter

        with pytest.raises(PermissionError):
            create_filter(mock_jira_client, name='Test', jql='project = PROJ')

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError
        mock_jira_client.create_filter.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from create_filter import create_filter

        with pytest.raises(JiraError) as exc_info:
            create_filter(mock_jira_client, name='Test', jql='project = PROJ')
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 internal server error."""
        from jira_assistant_skills_lib import JiraError
        mock_jira_client.create_filter.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from create_filter import create_filter

        with pytest.raises(JiraError) as exc_info:
            create_filter(mock_jira_client, name='Test', jql='project = PROJ')
        assert exc_info.value.status_code == 500
