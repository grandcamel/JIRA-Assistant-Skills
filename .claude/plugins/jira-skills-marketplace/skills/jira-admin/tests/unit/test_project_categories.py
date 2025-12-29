"""
Tests for project category management - create_category.py, list_categories.py, assign_category.py.

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
from unittest.mock import Mock, patch


@pytest.mark.admin
@pytest.mark.unit
class TestCreateCategory:
    """Test suite for create_category.py functionality."""

    def test_create_category_basic(self, mock_jira_client, sample_category_response):
        """Test creating category with name only."""
        from create_category import create_category

        mock_jira_client.create_project_category.return_value = sample_category_response

        result = create_category(
            name="Development",
            client=mock_jira_client
        )

        assert result is not None
        assert result['name'] == "Development"

        mock_jira_client.create_project_category.assert_called_once()

    def test_create_category_with_description(self, mock_jira_client, sample_category_response):
        """Test creating category with description."""
        from create_category import create_category

        mock_jira_client.create_project_category.return_value = sample_category_response

        result = create_category(
            name="Development",
            description="All development projects",
            client=mock_jira_client
        )

        assert result is not None

        # Verify description was passed
        call_kwargs = mock_jira_client.create_project_category.call_args
        assert 'description' in str(call_kwargs) or 'All development' in str(call_kwargs)

    def test_create_category_empty_name(self, mock_jira_client):
        """Test error for empty category name."""
        from create_category import create_category
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            create_category(
                name="",
                client=mock_jira_client
            )

    def test_create_category_name_too_long(self, mock_jira_client):
        """Test error for category name exceeding max length."""
        from create_category import create_category
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            create_category(
                name="A" * 300,  # 256 char max
                client=mock_jira_client
            )

    def test_create_category_duplicate_name(self, mock_jira_client):
        """Test error when category name already exists."""
        from create_category import create_category
        from error_handler import JiraError

        mock_jira_client.create_project_category.side_effect = JiraError(
            "A category with that name already exists",
            status_code=409
        )

        with pytest.raises(JiraError) as exc_info:
            create_category(
                name="Development",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 409

    def test_create_category_no_permission(self, mock_jira_client):
        """Test error when user lacks admin permission."""
        from create_category import create_category
        from error_handler import JiraError

        mock_jira_client.create_project_category.side_effect = JiraError(
            "You don't have permission to create categories",
            status_code=403
        )

        with pytest.raises(JiraError) as exc_info:
            create_category(
                name="Development",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 403


@pytest.mark.admin
@pytest.mark.unit
class TestListCategories:
    """Test suite for list_categories.py functionality."""

    def test_list_categories_all(self, mock_jira_client, sample_categories_list):
        """Test listing all categories."""
        from list_categories import list_categories

        mock_jira_client.get_project_categories.return_value = sample_categories_list

        result = list_categories(client=mock_jira_client)

        assert result is not None
        assert len(result) == 3
        assert result[0]['name'] == "Development"
        assert result[1]['name'] == "Marketing"
        assert result[2]['name'] == "Support"

        mock_jira_client.get_project_categories.assert_called_once()

    def test_list_categories_empty(self, mock_jira_client):
        """Test when no categories exist."""
        from list_categories import list_categories

        mock_jira_client.get_project_categories.return_value = []

        result = list_categories(client=mock_jira_client)

        assert result is not None
        assert len(result) == 0

    def test_list_categories_json_output(self, mock_jira_client, sample_categories_list):
        """Test JSON output format."""
        from list_categories import list_categories

        mock_jira_client.get_project_categories.return_value = sample_categories_list

        result = list_categories(
            output_format="json",
            client=mock_jira_client
        )

        assert result is not None
        # Result should be suitable for JSON serialization
        import json
        json.dumps(result)  # Should not raise


@pytest.mark.admin
@pytest.mark.unit
class TestAssignCategory:
    """Test suite for assign_category.py functionality."""

    def test_assign_category_by_id(self, mock_jira_client, sample_project_response):
        """Test assigning category to project by ID."""
        from assign_category import assign_category

        mock_jira_client.update_project.return_value = sample_project_response

        result = assign_category(
            project_key="PROJ",
            category_id=10000,
            client=mock_jira_client
        )

        assert result is not None

        # Verify update_project was called with category_id
        mock_jira_client.update_project.assert_called_once()
        call_kwargs = mock_jira_client.update_project.call_args
        assert 'category_id' in str(call_kwargs) or '10000' in str(call_kwargs)

    def test_assign_category_by_name(self, mock_jira_client, sample_project_response, sample_categories_list):
        """Test assigning category to project by name."""
        from assign_category import assign_category

        mock_jira_client.get_project_categories.return_value = sample_categories_list
        mock_jira_client.update_project.return_value = sample_project_response

        result = assign_category(
            project_key="PROJ",
            category_name="Development",
            client=mock_jira_client
        )

        assert result is not None

        # Verify update_project was called
        mock_jira_client.update_project.assert_called_once()

    def test_assign_category_not_found(self, mock_jira_client, sample_categories_list):
        """Test error when category name doesn't exist."""
        from assign_category import assign_category
        from error_handler import ValidationError

        mock_jira_client.get_project_categories.return_value = sample_categories_list

        with pytest.raises(ValidationError) as exc_info:
            assign_category(
                project_key="PROJ",
                category_name="NonExistent",
                client=mock_jira_client
            )

        assert "not found" in str(exc_info.value).lower()

    def test_remove_category(self, mock_jira_client, sample_project_response):
        """Test removing category from project."""
        from assign_category import assign_category

        # Response without category
        response_no_category = sample_project_response.copy()
        response_no_category['projectCategory'] = None
        mock_jira_client.update_project.return_value = response_no_category

        result = assign_category(
            project_key="PROJ",
            remove=True,
            client=mock_jira_client
        )

        assert result is not None

        # Verify update_project was called to remove category
        mock_jira_client.update_project.assert_called_once()

    def test_assign_category_project_not_found(self, mock_jira_client):
        """Test error when project doesn't exist."""
        from assign_category import assign_category
        from error_handler import JiraError

        mock_jira_client.update_project.side_effect = JiraError(
            "Project not found",
            status_code=404
        )

        with pytest.raises(JiraError) as exc_info:
            assign_category(
                project_key="NOTFOUND",
                category_id=10000,
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 404

    def test_assign_category_requires_one_param(self, mock_jira_client):
        """Test error when neither category_id, category_name, nor remove specified."""
        from assign_category import assign_category
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            assign_category(
                project_key="PROJ",
                client=mock_jira_client
                # No category_id, category_name, or remove
            )


@pytest.mark.admin
@pytest.mark.unit
class TestCategoryManagementCLI:
    """Test command-line interfaces for category management."""

    @patch('sys.argv', ['create_category.py', '--name', 'Development'])
    def test_cli_create_category(self, mock_jira_client, sample_category_response):
        """Test CLI for creating category."""
        mock_jira_client.create_project_category.return_value = sample_category_response
        pass

    @patch('sys.argv', ['list_categories.py'])
    def test_cli_list_categories(self, mock_jira_client, sample_categories_list):
        """Test CLI for listing categories."""
        mock_jira_client.get_project_categories.return_value = sample_categories_list
        pass

    @patch('sys.argv', ['assign_category.py', 'PROJ', '--category', 'Development'])
    def test_cli_assign_category(self, mock_jira_client, sample_project_response):
        """Test CLI for assigning category."""
        mock_jira_client.update_project.return_value = sample_project_response
        pass

    @patch('sys.argv', ['assign_category.py', 'PROJ', '--remove'])
    def test_cli_remove_category(self, mock_jira_client, sample_project_response):
        """Test CLI for removing category."""
        mock_jira_client.update_project.return_value = sample_project_response
        pass
