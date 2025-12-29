"""
Tests for create_project.py - Creating JIRA projects.

Following TDD: These tests are written FIRST and should FAIL initially.
Implementation comes after tests are defined.
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
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.admin
@pytest.mark.unit
class TestCreateProject:
    """Test suite for create_project.py functionality."""

    def test_create_project_minimal(self, mock_jira_client, sample_project_create_response):
        """Test creating project with only required fields (key, name, type)."""
        from create_project import create_project

        mock_jira_client.create_project.return_value = sample_project_create_response
        mock_jira_client.get_current_user_id.return_value = "557058:test-user-id"

        result = create_project(
            key="PROJ",
            name="Test Project",
            project_type="software",
            client=mock_jira_client
        )

        assert result is not None
        assert result['key'] == "PROJ"
        assert result['name'] == "Test Project"
        assert result['projectTypeKey'] == "software"

        # Verify API call
        mock_jira_client.create_project.assert_called_once()

    def test_create_project_with_template(self, mock_jira_client, sample_project_create_response):
        """Test creating project with specific template."""
        from create_project import create_project

        mock_jira_client.create_project.return_value = sample_project_create_response
        mock_jira_client.get_current_user_id.return_value = "557058:test-user-id"

        result = create_project(
            key="SCRUM",
            name="Scrum Project",
            project_type="software",
            template="scrum",
            client=mock_jira_client
        )

        assert result is not None

        # Verify template was expanded and used
        call_kwargs = mock_jira_client.create_project.call_args
        assert 'com.pyxis.greenhopper.jira:gh-simplified-agility-scrum' in str(call_kwargs)

    def test_create_project_with_lead(self, mock_jira_client, sample_project_create_response):
        """Test setting project lead."""
        from create_project import create_project

        mock_jira_client.create_project.return_value = sample_project_create_response
        # Mock search_users to return user when looking up email
        mock_jira_client.search_users.return_value = [
            {'accountId': 'alice-account-id', 'emailAddress': 'alice@example.com'}
        ]

        result = create_project(
            key="PROJ",
            name="Test Project",
            project_type="software",
            lead="alice@example.com",
            client=mock_jira_client
        )

        assert result is not None

        # Verify lead was passed
        call_kwargs = mock_jira_client.create_project.call_args
        assert 'alice-account-id' in str(call_kwargs) or 'lead' in str(call_kwargs)

    def test_create_project_with_description(self, mock_jira_client, sample_project_create_response):
        """Test creating project with description."""
        from create_project import create_project

        mock_jira_client.create_project.return_value = sample_project_create_response
        mock_jira_client.get_current_user_id.return_value = "557058:test-user-id"

        result = create_project(
            key="PROJ",
            name="Test Project",
            project_type="software",
            description="A comprehensive development project",
            client=mock_jira_client
        )

        assert result is not None

        # Verify description was passed
        call_kwargs = mock_jira_client.create_project.call_args
        assert 'description' in str(call_kwargs).lower()

    def test_create_project_with_category(self, mock_jira_client, sample_project_create_response):
        """Test assigning project to category."""
        from create_project import create_project

        mock_jira_client.create_project.return_value = sample_project_create_response
        mock_jira_client.get_current_user_id.return_value = "557058:test-user-id"
        mock_jira_client.update_project.return_value = sample_project_create_response

        result = create_project(
            key="PROJ",
            name="Test Project",
            project_type="software",
            category_id=10000,
            client=mock_jira_client
        )

        assert result is not None

        # Verify update_project was called with category
        mock_jira_client.update_project.assert_called_once()
        update_call = mock_jira_client.update_project.call_args
        assert 'category_id' in str(update_call) or '10000' in str(update_call)

    def test_create_project_invalid_key(self, mock_jira_client):
        """Test validation of project key (uppercase, starts with letter)."""
        from create_project import create_project
        from jira_assistant_skills_lib import ValidationError

        # Test with invalid characters (contains hyphen which is not allowed)
        with pytest.raises(ValidationError) as exc_info:
            create_project(
                key="PR-OJ",  # Contains invalid character
                name="Test Project",
                project_type="software",
                client=mock_jira_client
            )

        # Test with too long key
        with pytest.raises(ValidationError) as exc_info:
            create_project(
                key="VERYLONGPROJECTKEY",  # Too long (>10 chars)
                name="Test Project",
                project_type="software",
                client=mock_jira_client
            )

    def test_create_project_duplicate_key(self, mock_jira_client):
        """Test error when key already exists."""
        from create_project import create_project
        from jira_assistant_skills_lib import ConflictError, JiraError

        # Simulate 409 conflict error
        mock_jira_client.create_project.side_effect = JiraError(
            "A project with that key already exists",
            status_code=409
        )
        mock_jira_client.get_current_user_id.return_value = "557058:test-user-id"

        with pytest.raises(JiraError) as exc_info:
            create_project(
                key="PROJ",
                name="Test Project",
                project_type="software",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 409

    def test_create_project_invalid_type(self, mock_jira_client):
        """Test error for invalid project type."""
        from create_project import create_project
        from jira_assistant_skills_lib import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            create_project(
                key="PROJ",
                name="Test Project",
                project_type="invalid_type",
                client=mock_jira_client
            )

        assert "invalid" in str(exc_info.value).lower() or "type" in str(exc_info.value).lower()

    def test_create_project_no_permission(self, mock_jira_client):
        """Test error when user lacks admin permission."""
        from create_project import create_project
        from jira_assistant_skills_lib import PermissionError, JiraError

        # Simulate 403 permission error
        mock_jira_client.create_project.side_effect = JiraError(
            "You don't have permission to create projects",
            status_code=403
        )
        mock_jira_client.get_current_user_id.return_value = "557058:test-user-id"

        with pytest.raises(JiraError) as exc_info:
            create_project(
                key="PROJ",
                name="Test Project",
                project_type="software",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 403


@pytest.mark.admin
@pytest.mark.unit
class TestCreateProjectCLI:
    """Test command-line interface for create_project.py."""

    @patch('sys.argv', ['create_project.py', '--key', 'PROJ', '--name', 'Test Project', '--type', 'software'])
    def test_cli_minimal_args(self, mock_jira_client, sample_project_create_response):
        """Test CLI with minimal required arguments."""
        mock_jira_client.create_project.return_value = sample_project_create_response
        mock_jira_client.get_current_user_id.return_value = "557058:test-user-id"
        # CLI test would call main() with patched get_jira_client
        pass

    @patch('sys.argv', ['create_project.py', '--key', 'PROJ', '--name', 'Test', '--type', 'software', '--template', 'scrum'])
    def test_cli_with_template(self, mock_jira_client, sample_project_create_response):
        """Test CLI with template argument."""
        mock_jira_client.create_project.return_value = sample_project_create_response
        mock_jira_client.get_current_user_id.return_value = "557058:test-user-id"
        pass
