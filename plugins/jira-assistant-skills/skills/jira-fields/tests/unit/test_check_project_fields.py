"""
Unit Tests: check_project_fields.py

Tests for checking project field availability.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Path setup
_this_dir = Path(__file__).parent
_tests_dir = _this_dir.parent
_jira_fields_dir = _tests_dir.parent
_scripts_dir = _jira_fields_dir / "scripts"
_shared_lib_dir = _jira_fields_dir.parent / "shared" / "scripts" / "lib"

for path in [str(_shared_lib_dir), str(_scripts_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)

from check_project_fields import AGILE_FIELDS, check_project_fields

from jira_assistant_skills_lib import AuthenticationError, JiraError


@pytest.mark.fields
@pytest.mark.unit
class TestCheckProjectFieldsBasic:
    """Test basic check_project_fields functionality."""

    def test_check_project_fields_basic(
        self, mock_jira_client, sample_project_response, sample_create_meta_response
    ):
        """Test basic project field check."""
        mock_jira_client.get.side_effect = [
            sample_project_response,
            sample_create_meta_response,
        ]

        result = check_project_fields(project_key="TEST", client=mock_jira_client)

        assert result is not None
        assert "project" in result
        assert result["project"]["key"] == "TEST"
        assert result["project"]["name"] == "Test Project"
        assert "fields" in result
        assert "issue_types" in result

    def test_check_project_detects_classic_style(
        self, mock_jira_client, sample_project_response, sample_create_meta_response
    ):
        """Test detection of company-managed (classic) project style."""
        mock_jira_client.get.side_effect = [
            sample_project_response,
            sample_create_meta_response,
        ]

        result = check_project_fields(project_key="TEST", client=mock_jira_client)

        assert result["is_team_managed"] is False
        assert result["project"]["style"] == "classic"

    def test_check_project_detects_team_managed_style(
        self, mock_jira_client, sample_project_team_managed, sample_create_meta_response
    ):
        """Test detection of team-managed (next-gen) project style."""
        mock_jira_client.get.side_effect = [
            sample_project_team_managed,
            sample_create_meta_response,
        ]

        result = check_project_fields(project_key="TEAM", client=mock_jira_client)

        assert result["is_team_managed"] is True
        assert result["project"]["style"] == "next-gen"


@pytest.mark.fields
@pytest.mark.unit
class TestCheckProjectFieldsIssueTypes:
    """Test issue type filtering."""

    def test_check_specific_issue_type(
        self, mock_jira_client, sample_project_response, sample_create_meta_response
    ):
        """Test checking fields for specific issue type."""
        mock_jira_client.get.side_effect = [
            sample_project_response,
            sample_create_meta_response,
        ]

        result = check_project_fields(
            project_key="TEST", issue_type="Task", client=mock_jira_client
        )

        assert result is not None
        # Verify API was called with issuetypeNames param
        calls = mock_jira_client.get.call_args_list
        assert len(calls) == 2
        second_call = calls[1]
        params = second_call[1].get(
            "params", second_call[0][1] if len(second_call[0]) > 1 else {}
        )
        assert params.get("issuetypeNames") == "Task"

    def test_issue_types_in_result(
        self, mock_jira_client, sample_project_response, sample_create_meta_response
    ):
        """Test that issue types are properly populated."""
        mock_jira_client.get.side_effect = [
            sample_project_response,
            sample_create_meta_response,
        ]

        result = check_project_fields(project_key="TEST", client=mock_jira_client)

        assert len(result["issue_types"]) == 2
        type_names = [t["name"] for t in result["issue_types"]]
        assert "Task" in type_names
        assert "Story" in type_names


@pytest.mark.fields
@pytest.mark.unit
class TestCheckProjectFieldsAgile:
    """Test Agile field checking."""

    def test_check_agile_fields(
        self, mock_jira_client, sample_project_response, sample_create_meta_response
    ):
        """Test checking Agile field availability."""
        mock_jira_client.get.side_effect = [
            sample_project_response,
            sample_create_meta_response,
        ]

        result = check_project_fields(
            project_key="TEST", check_agile=True, client=mock_jira_client
        )

        assert "agile_fields" in result
        agile = result["agile_fields"]
        # Sprint and Story Points should be found
        assert agile.get("sprint") is not None
        assert agile.get("story_points") is not None

    def test_agile_fields_not_found(self, mock_jira_client, sample_project_response):
        """Test when no Agile fields are available."""
        # Create meta with no agile fields
        meta = {
            "projects": [
                {
                    "id": "10001",
                    "key": "TEST",
                    "issuetypes": [
                        {
                            "id": "10001",
                            "name": "Task",
                            "fields": {
                                "summary": {"name": "Summary", "required": True}
                            },
                        }
                    ],
                }
            ]
        }
        mock_jira_client.get.side_effect = [sample_project_response, meta]

        result = check_project_fields(
            project_key="TEST", check_agile=True, client=mock_jira_client
        )

        assert "agile_fields" in result
        # All agile fields should be None
        for field_type in AGILE_FIELDS:
            assert result["agile_fields"].get(field_type) is None


@pytest.mark.fields
@pytest.mark.unit
class TestCheckProjectFieldsErrorHandling:
    """Test error handling in check_project_fields."""

    def test_project_not_found(self, mock_jira_client):
        """Test handling of non-existent project."""
        mock_jira_client.get.side_effect = JiraError(
            "Project not found", status_code=404
        )

        with pytest.raises(JiraError) as exc_info:
            check_project_fields(project_key="NOTEXIST", client=mock_jira_client)
        assert exc_info.value.status_code == 404

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 authentication error."""
        mock_jira_client.get.side_effect = AuthenticationError("Invalid token")

        with pytest.raises(AuthenticationError):
            check_project_fields(project_key="TEST", client=mock_jira_client)

    def test_permission_denied_error(self, mock_jira_client):
        """Test handling of 403 permission denied."""
        mock_jira_client.get.side_effect = JiraError(
            "Permission denied", status_code=403
        )

        with pytest.raises(JiraError) as exc_info:
            check_project_fields(project_key="TEST", client=mock_jira_client)
        assert exc_info.value.status_code == 403

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        mock_jira_client.get.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        with pytest.raises(JiraError) as exc_info:
            check_project_fields(project_key="TEST", client=mock_jira_client)
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        mock_jira_client.get.side_effect = JiraError("Server error", status_code=500)

        with pytest.raises(JiraError) as exc_info:
            check_project_fields(project_key="TEST", client=mock_jira_client)
        assert exc_info.value.status_code == 500


@pytest.mark.fields
@pytest.mark.unit
class TestCheckProjectFieldsClientManagement:
    """Test client lifecycle management."""

    def test_closes_client_on_success(
        self, sample_project_response, sample_create_meta_response
    ):
        """Test that client is closed after successful operation."""
        mock_client = MagicMock()
        mock_client.get.side_effect = [
            sample_project_response,
            sample_create_meta_response,
        ]

        with patch("check_project_fields.get_jira_client", return_value=mock_client):
            check_project_fields(project_key="TEST")

        mock_client.close.assert_called_once()

    def test_closes_client_on_error(self):
        """Test that client is closed even when operation fails."""
        mock_client = MagicMock()
        mock_client.get.side_effect = JiraError("Test error")

        with patch("check_project_fields.get_jira_client", return_value=mock_client):
            with pytest.raises(JiraError):
                check_project_fields(project_key="TEST")

        mock_client.close.assert_called_once()

    def test_does_not_close_provided_client(
        self, mock_jira_client, sample_project_response, sample_create_meta_response
    ):
        """Test that provided client is not closed."""
        mock_jira_client.get.side_effect = [
            sample_project_response,
            sample_create_meta_response,
        ]

        check_project_fields(project_key="TEST", client=mock_jira_client)

        mock_jira_client.close.assert_not_called()
