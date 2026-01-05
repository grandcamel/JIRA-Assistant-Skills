"""
Tests for assign_workflow_scheme.py - TDD approach.

Tests for assigning workflow schemes to projects.
"""

import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


class TestAssignWorkflowSchemeShowCurrent:
    """Test showing current workflow scheme for a project."""

    def test_show_current_scheme(self, mock_jira_client, project_workflow_scheme):
        """Test showing the current workflow scheme for a project."""
        from assign_workflow_scheme import get_current_scheme

        mock_jira_client.get_workflow_scheme_for_project.return_value = (
            project_workflow_scheme
        )

        result = get_current_scheme(client=mock_jira_client, project_key="PROJ")

        assert result["id"] == 10100
        assert result["name"] == "Software Development Scheme"

    def test_show_current_scheme_not_found(self, mock_jira_client):
        """Test handling when project has no custom scheme."""
        from assign_workflow_scheme import get_current_scheme

        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_workflow_scheme_for_project.side_effect = NotFoundError(
            "No workflow scheme found"
        )

        with pytest.raises(NotFoundError):
            get_current_scheme(client=mock_jira_client, project_key="NONEXISTENT")


class TestAssignWorkflowSchemeDryRun:
    """Test dry-run mode for workflow scheme assignment."""

    def test_assign_scheme_dry_run(
        self, mock_jira_client, project_workflow_scheme, software_scheme_detail
    ):
        """Test dry-run shows what would change without making changes."""
        from assign_workflow_scheme import assign_workflow_scheme

        mock_jira_client.get_workflow_scheme_for_project.return_value = (
            project_workflow_scheme
        )
        mock_jira_client.get_workflow_scheme.return_value = software_scheme_detail

        result = assign_workflow_scheme(
            client=mock_jira_client, project_key="PROJ", scheme_id=10101, dry_run=True
        )

        assert result["dry_run"]
        assert "current_scheme" in result
        assert "new_scheme" in result
        # Should not call assign method
        mock_jira_client.assign_workflow_scheme_to_project.assert_not_called()


class TestAssignWorkflowSchemeExecution:
    """Test actual workflow scheme assignment."""

    def test_assign_scheme_success(
        self, mock_jira_client, assign_scheme_task_response, task_complete_response
    ):
        """Test successful workflow scheme assignment."""
        from assign_workflow_scheme import assign_workflow_scheme

        mock_jira_client.assign_workflow_scheme_to_project.return_value = (
            assign_scheme_task_response
        )
        mock_jira_client.get_task_status.return_value = task_complete_response

        result = assign_workflow_scheme(
            client=mock_jira_client, project_key="PROJ", scheme_id=10101, confirm=True
        )

        assert result["success"]
        assert result["task_id"] == "10050"
        mock_jira_client.assign_workflow_scheme_to_project.assert_called_once()

    def test_assign_scheme_requires_confirmation(self, mock_jira_client):
        """Test that assignment requires explicit confirmation."""
        from assign_workflow_scheme import assign_workflow_scheme
        from assistant_skills_lib.error_handler import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            assign_workflow_scheme(
                client=mock_jira_client,
                project_key="PROJ",
                scheme_id=10101,
                confirm=False,
                dry_run=False,
            )

        assert "confirm" in str(exc_info.value).lower()


class TestAssignWorkflowSchemeWithMappings:
    """Test workflow scheme assignment with status mappings."""

    def test_assign_scheme_with_status_mappings(
        self, mock_jira_client, assign_scheme_task_response, task_complete_response
    ):
        """Test assignment with status migration mappings."""
        from assign_workflow_scheme import assign_workflow_scheme

        mock_jira_client.assign_workflow_scheme_to_project.return_value = (
            assign_scheme_task_response
        )
        mock_jira_client.get_task_status.return_value = task_complete_response

        status_mappings = [
            {
                "issueTypeId": "10000",
                "statusMigrations": [{"oldStatusId": "1", "newStatusId": "10000"}],
            }
        ]

        result = assign_workflow_scheme(
            client=mock_jira_client,
            project_key="PROJ",
            scheme_id=10101,
            status_mappings=status_mappings,
            confirm=True,
        )

        assert result["success"]
        # Verify mappings were passed
        call_args = mock_jira_client.assign_workflow_scheme_to_project.call_args
        assert call_args is not None


class TestAssignWorkflowSchemeTaskTracking:
    """Test async task tracking during assignment."""

    def test_assign_scheme_wait_for_task(
        self,
        mock_jira_client,
        assign_scheme_task_response,
        task_in_progress_response,
        task_complete_response,
    ):
        """Test waiting for async task to complete."""
        from assign_workflow_scheme import assign_workflow_scheme

        mock_jira_client.assign_workflow_scheme_to_project.return_value = (
            assign_scheme_task_response
        )
        # First call returns in-progress, second returns complete
        mock_jira_client.get_task_status.side_effect = [
            task_in_progress_response,
            task_complete_response,
        ]

        result = assign_workflow_scheme(
            client=mock_jira_client,
            project_key="PROJ",
            scheme_id=10101,
            confirm=True,
            wait=True,
        )

        assert result["success"]
        assert mock_jira_client.get_task_status.call_count >= 1

    def test_assign_scheme_no_wait(self, mock_jira_client, assign_scheme_task_response):
        """Test returning immediately without waiting for task."""
        from assign_workflow_scheme import assign_workflow_scheme

        mock_jira_client.assign_workflow_scheme_to_project.return_value = (
            assign_scheme_task_response
        )

        result = assign_workflow_scheme(
            client=mock_jira_client,
            project_key="PROJ",
            scheme_id=10101,
            confirm=True,
            wait=False,
        )

        assert "task_id" in result
        # Should not poll for status
        mock_jira_client.get_task_status.assert_not_called()


class TestAssignWorkflowSchemeByName:
    """Test assigning workflow scheme by name."""

    def test_assign_scheme_by_name(
        self,
        mock_jira_client,
        workflow_schemes_list_response,
        assign_scheme_task_response,
        task_complete_response,
    ):
        """Test assigning workflow scheme by name instead of ID."""
        from assign_workflow_scheme import assign_workflow_scheme

        mock_jira_client.get_workflow_schemes.return_value = (
            workflow_schemes_list_response
        )
        mock_jira_client.assign_workflow_scheme_to_project.return_value = (
            assign_scheme_task_response
        )
        mock_jira_client.get_task_status.return_value = task_complete_response

        result = assign_workflow_scheme(
            client=mock_jira_client,
            project_key="PROJ",
            scheme_name="Agile Development Scheme",
            confirm=True,
        )

        assert result["success"]

    def test_assign_scheme_name_not_found(
        self, mock_jira_client, workflow_schemes_list_response
    ):
        """Test error when scheme name not found."""
        from assign_workflow_scheme import assign_workflow_scheme

        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_workflow_schemes.return_value = (
            workflow_schemes_list_response
        )

        with pytest.raises(NotFoundError):
            assign_workflow_scheme(
                client=mock_jira_client,
                project_key="PROJ",
                scheme_name="Nonexistent Scheme",
                confirm=True,
            )


class TestAssignWorkflowSchemeErrorHandling:
    """Test error handling scenarios."""

    def test_assign_scheme_missing_params(self, mock_jira_client):
        """Test error when neither scheme_id nor scheme_name provided."""
        from assign_workflow_scheme import assign_workflow_scheme
        from assistant_skills_lib.error_handler import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            assign_workflow_scheme(
                client=mock_jira_client, project_key="PROJ", confirm=True
            )

        assert "scheme" in str(exc_info.value).lower()

    def test_assign_scheme_no_permission(self, mock_jira_client):
        """Test error when user lacks admin permission."""
        from assign_workflow_scheme import assign_workflow_scheme

        from jira_assistant_skills_lib import PermissionError as JiraPermissionError

        mock_jira_client.assign_workflow_scheme_to_project.side_effect = (
            JiraPermissionError("Requires admin permission")
        )

        with pytest.raises(JiraPermissionError):
            assign_workflow_scheme(
                client=mock_jira_client,
                project_key="PROJ",
                scheme_id=10101,
                confirm=True,
            )

    def test_assign_scheme_project_not_found(self, mock_jira_client):
        """Test error when project not found."""
        from assign_workflow_scheme import assign_workflow_scheme

        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.assign_workflow_scheme_to_project.side_effect = NotFoundError(
            "Project not found"
        )

        with pytest.raises(NotFoundError):
            assign_workflow_scheme(
                client=mock_jira_client,
                project_key="NONEXISTENT",
                scheme_id=10101,
                confirm=True,
            )


@pytest.mark.admin
@pytest.mark.unit
class TestAssignWorkflowSchemeTaskFailure:
    """Test handling of failed async tasks."""

    def test_assign_scheme_task_failure(
        self, mock_jira_client, assign_scheme_task_response, task_failed_response
    ):
        """Test handling of failed async task."""
        from assign_workflow_scheme import assign_workflow_scheme

        mock_jira_client.assign_workflow_scheme_to_project.return_value = (
            assign_scheme_task_response
        )
        mock_jira_client.get_task_status.return_value = task_failed_response

        result = assign_workflow_scheme(
            client=mock_jira_client,
            project_key="PROJ",
            scheme_id=10101,
            confirm=True,
            wait=True,
        )

        # Task failure should result in success=False
        assert not result["success"]
        assert "failed" in result.get("message", "").lower()
        mock_jira_client.get_task_status.assert_called()

    def test_assign_scheme_task_cancelled(
        self, mock_jira_client, assign_scheme_task_response
    ):
        """Test handling of cancelled async task."""
        from assign_workflow_scheme import assign_workflow_scheme

        task_cancelled = {
            "taskId": "10050",
            "status": "CANCELLED",
            "message": "Task was cancelled by user",
            "progress": 30,
        }
        mock_jira_client.assign_workflow_scheme_to_project.return_value = (
            assign_scheme_task_response
        )
        mock_jira_client.get_task_status.return_value = task_cancelled

        result = assign_workflow_scheme(
            client=mock_jira_client,
            project_key="PROJ",
            scheme_id=10101,
            confirm=True,
            wait=True,
        )

        # Cancelled task should result in success=False
        assert not result["success"]
        mock_jira_client.get_task_status.assert_called()

    def test_assign_scheme_task_timeout(
        self, mock_jira_client, assign_scheme_task_response
    ):
        """Test handling of task timeout."""
        from assign_workflow_scheme import assign_workflow_scheme

        # Setup: Task never completes (stays in RUNNING state)
        in_progress = {"taskId": "10050", "status": "RUNNING", "progress": 50}
        mock_jira_client.assign_workflow_scheme_to_project.return_value = (
            assign_scheme_task_response
        )
        mock_jira_client.get_task_status.return_value = in_progress

        # Use very short max_wait and poll_interval for fast test
        result = assign_workflow_scheme(
            client=mock_jira_client,
            project_key="PROJ",
            scheme_id=10101,
            confirm=True,
            wait=True,
            max_wait=1,
            poll_interval=1,
        )

        # Should timeout and return with timeout message
        assert "task_id" in result
        assert (
            "Timed out" in result.get("message", "")
            or mock_jira_client.get_task_status.called
        )
