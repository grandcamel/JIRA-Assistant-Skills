"""
Tests for create_component.py - Create a project component.
"""

import copy
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.mark.lifecycle
@pytest.mark.unit
class TestCreateComponent:
    """Tests for creating project components."""

    @patch("create_component.get_jira_client")
    def test_create_basic_component(
        self, mock_get_client, mock_jira_client, sample_component
    ):
        """Test creating a basic component with name only."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_component.return_value = sample_component

        from create_component import create_component

        result = create_component(project="PROJ", name="Backend API")

        assert result["name"] == "Backend API"
        assert result["project"] == "PROJ"
        mock_jira_client.create_component.assert_called_once()

    @patch("create_component.get_jira_client")
    def test_create_component_with_description(self, mock_get_client, mock_jira_client):
        """Test creating component with description."""
        mock_get_client.return_value = mock_jira_client
        component_with_desc = {
            "id": "10001",
            "name": "Frontend UI",
            "description": "User interface components",
            "project": "PROJ",
            "projectId": 10000,
        }
        mock_jira_client.create_component.return_value = component_with_desc

        from create_component import create_component

        result = create_component(
            project="PROJ",
            name="Frontend UI",
            description="User interface components",
        )

        assert result["description"] == "User interface components"

    @patch("create_component.get_jira_client")
    def test_create_component_with_lead(self, mock_get_client, mock_jira_client):
        """Test creating component with component lead."""
        mock_get_client.return_value = mock_jira_client
        component_with_lead = {
            "id": "10002",
            "name": "Database",
            "project": "PROJ",
            "lead": {
                "accountId": "5b10a2844c20165700ede21g",
                "displayName": "Alice Smith",
            },
        }
        mock_jira_client.create_component.return_value = component_with_lead

        from create_component import create_component

        result = create_component(
            project="PROJ",
            name="Database",
            lead_account_id="5b10a2844c20165700ede21g",
        )

        assert result["lead"]["accountId"] == "5b10a2844c20165700ede21g"

    @patch("create_component.get_jira_client")
    def test_create_component_with_assignee_type(
        self, mock_get_client, mock_jira_client
    ):
        """Test creating component with default assignee type."""
        mock_get_client.return_value = mock_jira_client
        component_with_assignee = {
            "id": "10003",
            "name": "Infrastructure",
            "project": "PROJ",
            "assigneeType": "COMPONENT_LEAD",
        }
        mock_jira_client.create_component.return_value = component_with_assignee

        from create_component import create_component

        result = create_component(
            project="PROJ",
            name="Infrastructure",
            assignee_type="COMPONENT_LEAD",
        )

        assert result["assigneeType"] == "COMPONENT_LEAD"

    @patch("create_component.get_jira_client")
    def test_create_component_full(self, mock_get_client, mock_jira_client):
        """Test creating component with all fields."""
        mock_get_client.return_value = mock_jira_client
        full_component = {
            "id": "10004",
            "name": "Security",
            "description": "Security and authentication",
            "project": "PROJ",
            "lead": {
                "accountId": "5b10a2844c20165700ede22h",
                "displayName": "Bob Jones",
            },
            "assigneeType": "PROJECT_LEAD",
        }
        mock_jira_client.create_component.return_value = full_component

        from create_component import create_component

        result = create_component(
            project="PROJ",
            name="Security",
            description="Security and authentication",
            lead_account_id="5b10a2844c20165700ede22h",
            assignee_type="PROJECT_LEAD",
        )

        assert result["name"] == "Security"
        assert result["description"] == "Security and authentication"
        assert result["assigneeType"] == "PROJECT_LEAD"

    @patch("create_component.get_jira_client")
    def test_create_component_dry_run(self, mock_get_client, mock_jira_client):
        """Test dry-run mode shows what would be created."""
        mock_get_client.return_value = mock_jira_client

        from create_component import create_component_dry_run

        result = create_component_dry_run(
            project="PROJ",
            name="Testing",
            description="QA and testing",
            lead_account_id="5b10a2844c20165700ede21g",
            assignee_type="COMPONENT_LEAD",
        )

        # Dry run should return data without calling API
        assert result["project"] == "PROJ"
        assert result["name"] == "Testing"
        assert result["description"] == "QA and testing"
        mock_jira_client.create_component.assert_not_called()


@pytest.mark.lifecycle
@pytest.mark.unit
class TestCreateComponentErrorHandling:
    """Test API error handling for create_component."""

    @patch("create_component.get_jira_client")
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_component.side_effect = AuthenticationError(
            "Invalid token"
        )

        from create_component import create_component

        with pytest.raises(AuthenticationError):
            create_component(project="PROJ", name="Test")

    @patch("create_component.get_jira_client")
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_component.side_effect = PermissionError(
            "Cannot create component"
        )

        from create_component import create_component

        with pytest.raises(PermissionError):
            create_component(project="PROJ", name="Test")

    @patch("create_component.get_jira_client")
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when project doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_component.side_effect = NotFoundError(
            "Project", "INVALID"
        )

        from create_component import create_component

        with pytest.raises(NotFoundError):
            create_component(project="INVALID", name="Test")

    @patch("create_component.get_jira_client")
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_component.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from create_component import create_component

        with pytest.raises(JiraError) as exc_info:
            create_component(project="PROJ", name="Test")
        assert exc_info.value.status_code == 429

    @patch("create_component.get_jira_client")
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_component.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from create_component import create_component

        with pytest.raises(JiraError) as exc_info:
            create_component(project="PROJ", name="Test")
        assert exc_info.value.status_code == 500


@pytest.mark.lifecycle
@pytest.mark.unit
class TestCreateComponentMain:
    """Tests for main() function."""

    @patch("create_component.get_jira_client")
    def test_main_basic(
        self, mock_get_client, mock_jira_client, sample_component, capsys
    ):
        """Test main with basic args."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_component.return_value = copy.deepcopy(sample_component)

        from create_component import main

        main(["PROJ", "--name", "Backend API"])

        captured = capsys.readouterr()
        assert "Created component" in captured.out

    @patch("create_component.get_jira_client")
    def test_main_with_description(
        self, mock_get_client, mock_jira_client, sample_component, capsys
    ):
        """Test main with --description."""
        mock_get_client.return_value = mock_jira_client
        component = copy.deepcopy(sample_component)
        component["description"] = "API backend"
        mock_jira_client.create_component.return_value = component

        from create_component import main

        main(["PROJ", "--name", "Backend", "--description", "API backend"])

        captured = capsys.readouterr()
        assert "API backend" in captured.out

    @patch("create_component.get_jira_client")
    def test_main_with_lead(
        self, mock_get_client, mock_jira_client, sample_component, capsys
    ):
        """Test main with --lead."""
        mock_get_client.return_value = mock_jira_client
        component = copy.deepcopy(sample_component)
        component["lead"] = {
            "displayName": "Alice",
            "accountId": "5b10a2844c20165700ede21g",
        }
        mock_jira_client.create_component.return_value = component

        from create_component import main

        main(["PROJ", "--name", "Backend", "--lead", "5b10a2844c20165700ede21g"])

        captured = capsys.readouterr()
        assert "Lead: Alice" in captured.out

    @patch("create_component.get_jira_client")
    def test_main_with_assignee_type(
        self, mock_get_client, mock_jira_client, sample_component, capsys
    ):
        """Test main with --assignee-type."""
        mock_get_client.return_value = mock_jira_client
        component = copy.deepcopy(sample_component)
        component["assigneeType"] = "COMPONENT_LEAD"
        mock_jira_client.create_component.return_value = component

        from create_component import main

        main(["PROJ", "--name", "Backend", "--assignee-type", "COMPONENT_LEAD"])

        captured = capsys.readouterr()
        assert "Assignee Type: COMPONENT_LEAD" in captured.out

    @patch("create_component.get_jira_client")
    def test_main_dry_run(self, mock_get_client, mock_jira_client, capsys):
        """Test main with --dry-run."""
        mock_get_client.return_value = mock_jira_client

        from create_component import main

        main(["PROJ", "--name", "Testing", "--dry-run"])

        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
        assert "Testing" in captured.out
        mock_jira_client.create_component.assert_not_called()

    @patch("create_component.get_jira_client")
    def test_main_dry_run_with_all_options(
        self, mock_get_client, mock_jira_client, capsys
    ):
        """Test main dry-run with all options."""
        mock_get_client.return_value = mock_jira_client

        from create_component import main

        main(
            [
                "PROJ",
                "--name",
                "Test",
                "--description",
                "Desc",
                "--lead",
                "abc123",
                "--assignee-type",
                "PROJECT_LEAD",
                "--dry-run",
            ]
        )

        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
        assert "Desc" in captured.out
        assert "abc123" in captured.out
        assert "PROJECT_LEAD" in captured.out

    @patch("create_component.get_jira_client")
    def test_main_jira_error(self, mock_get_client, mock_jira_client, capsys):
        """Test main with JIRA API error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_component.side_effect = JiraError(
            "API Error", status_code=500
        )

        from create_component import main

        with pytest.raises(SystemExit) as exc_info:
            main(["PROJ", "--name", "Test"])

        assert exc_info.value.code == 1
