"""
Tests for list_workflow_schemes.py and get_workflow_scheme.py - TDD approach.

Tests for workflow scheme listing and retrieval.
"""

import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


# ========== list_workflow_schemes.py Tests ==========


class TestListWorkflowSchemesBasic:
    """Test listing all workflow schemes."""

    def test_list_workflow_schemes_returns_all(
        self, mock_jira_client, workflow_schemes_list_response
    ):
        """Test listing all workflow schemes."""
        from list_workflow_schemes import list_workflow_schemes

        mock_jira_client.get_workflow_schemes.return_value = (
            workflow_schemes_list_response
        )

        result = list_workflow_schemes(client=mock_jira_client)

        assert result["total"] == 3
        assert len(result["schemes"]) == 3
        mock_jira_client.get_workflow_schemes.assert_called_once()

    def test_list_workflow_schemes_empty(
        self, mock_jira_client, empty_workflow_schemes_response
    ):
        """Test handling empty schemes list."""
        from list_workflow_schemes import list_workflow_schemes

        mock_jira_client.get_workflow_schemes.return_value = (
            empty_workflow_schemes_response
        )

        result = list_workflow_schemes(client=mock_jira_client)

        assert result["total"] == 0
        assert len(result["schemes"]) == 0


class TestListWorkflowSchemesWithMappings:
    """Test listing schemes with issue type mappings."""

    def test_list_workflow_schemes_show_mappings(
        self, mock_jira_client, workflow_schemes_list_response
    ):
        """Test showing issue type mappings for each scheme."""
        from list_workflow_schemes import list_workflow_schemes

        mock_jira_client.get_workflow_schemes.return_value = (
            workflow_schemes_list_response
        )

        result = list_workflow_schemes(client=mock_jira_client, show_mappings=True)

        # Software Development Scheme should have mappings
        software_scheme = next(
            s for s in result["schemes"] if s["name"] == "Software Development Scheme"
        )
        assert "mappings" in software_scheme
        assert len(software_scheme["mappings"]) > 0


class TestListWorkflowSchemesWithProjects:
    """Test listing schemes with associated projects."""

    def test_list_workflow_schemes_show_projects(
        self, mock_jira_client, workflow_schemes_list_response, project_workflow_scheme
    ):
        """Test showing which projects use each scheme."""
        from list_workflow_schemes import list_workflow_schemes

        mock_jira_client.get_workflow_schemes.return_value = (
            workflow_schemes_list_response
        )
        mock_jira_client.get_workflow_scheme_for_project.return_value = (
            project_workflow_scheme
        )

        result = list_workflow_schemes(client=mock_jira_client, show_projects=True)

        # At least one scheme should have project info queried
        assert len(result["schemes"]) == 3


class TestListWorkflowSchemesPagination:
    """Test pagination handling."""

    def test_list_workflow_schemes_pagination(
        self, mock_jira_client, workflow_schemes_list_response
    ):
        """Test paginated results."""
        from list_workflow_schemes import list_workflow_schemes

        # Simulate first page
        page1 = {
            **workflow_schemes_list_response,
            "values": workflow_schemes_list_response["values"][:2],
            "total": 3,
            "isLast": False,
        }
        mock_jira_client.get_workflow_schemes.return_value = page1

        result = list_workflow_schemes(client=mock_jira_client, max_results=2)

        assert len(result["schemes"]) == 2
        assert result["has_more"]


class TestListWorkflowSchemesOutputFormats:
    """Test output formatting."""

    def test_list_workflow_schemes_format_table(
        self, mock_jira_client, workflow_schemes_list_response
    ):
        """Test table output format."""
        from list_workflow_schemes import format_schemes_table, list_workflow_schemes

        mock_jira_client.get_workflow_schemes.return_value = (
            workflow_schemes_list_response
        )

        result = list_workflow_schemes(client=mock_jira_client)
        output = format_schemes_table(result["schemes"])

        assert "Software Development Scheme" in output
        assert "Default Workflow Scheme" in output

    def test_list_workflow_schemes_format_json(
        self, mock_jira_client, workflow_schemes_list_response
    ):
        """Test JSON output format."""
        import json

        from list_workflow_schemes import format_schemes_json, list_workflow_schemes

        mock_jira_client.get_workflow_schemes.return_value = (
            workflow_schemes_list_response
        )

        result = list_workflow_schemes(client=mock_jira_client)
        output = format_schemes_json(result["schemes"])

        parsed = json.loads(output)
        assert len(parsed) == 3


# ========== get_workflow_scheme.py Tests ==========


class TestGetWorkflowSchemeById:
    """Test getting workflow scheme by ID."""

    def test_get_workflow_scheme_by_id(self, mock_jira_client, software_scheme_detail):
        """Test getting workflow scheme by ID."""
        from get_workflow_scheme import get_workflow_scheme

        mock_jira_client.get_workflow_scheme.return_value = software_scheme_detail

        result = get_workflow_scheme(client=mock_jira_client, scheme_id=10100)

        assert result["id"] == 10100
        assert result["name"] == "Software Development Scheme"
        mock_jira_client.get_workflow_scheme.assert_called_once_with(
            10100, return_draft_if_exists=False
        )

    def test_get_workflow_scheme_not_found(self, mock_jira_client):
        """Test error when scheme not found."""
        from get_workflow_scheme import get_workflow_scheme

        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_workflow_scheme.side_effect = NotFoundError(
            "Scheme not found"
        )

        with pytest.raises(NotFoundError):
            get_workflow_scheme(client=mock_jira_client, scheme_id=99999)


class TestGetWorkflowSchemeByName:
    """Test getting workflow scheme by name."""

    def test_get_workflow_scheme_by_name(
        self, mock_jira_client, workflow_schemes_list_response, software_scheme_detail
    ):
        """Test getting workflow scheme by name."""
        from get_workflow_scheme import get_workflow_scheme

        mock_jira_client.get_workflow_schemes.return_value = (
            workflow_schemes_list_response
        )
        mock_jira_client.get_workflow_scheme.return_value = software_scheme_detail

        result = get_workflow_scheme(
            client=mock_jira_client, name="Software Development Scheme"
        )

        assert result["name"] == "Software Development Scheme"

    def test_get_workflow_scheme_name_not_found(
        self, mock_jira_client, workflow_schemes_list_response
    ):
        """Test error when scheme name not found."""
        from get_workflow_scheme import get_workflow_scheme

        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_workflow_schemes.return_value = (
            workflow_schemes_list_response
        )

        with pytest.raises(NotFoundError):
            get_workflow_scheme(client=mock_jira_client, name="Nonexistent Scheme")


class TestGetWorkflowSchemeWithMappings:
    """Test getting scheme with detailed mappings."""

    def test_get_workflow_scheme_show_mappings(
        self, mock_jira_client, software_scheme_detail
    ):
        """Test showing issue type to workflow mappings."""
        from get_workflow_scheme import get_workflow_scheme

        mock_jira_client.get_workflow_scheme.return_value = software_scheme_detail

        result = get_workflow_scheme(
            client=mock_jira_client, scheme_id=10100, show_mappings=True
        )

        assert "mappings" in result
        # Check that mappings include issue type names and workflow names
        for mapping in result["mappings"]:
            assert "issue_type" in mapping or "issue_type_id" in mapping
            assert "workflow" in mapping or "workflow_name" in mapping


class TestGetWorkflowSchemeWithProjects:
    """Test getting scheme with project information."""

    def test_get_workflow_scheme_show_projects(
        self, mock_jira_client, software_scheme_detail
    ):
        """Test showing which projects use this scheme."""
        from get_workflow_scheme import get_workflow_scheme

        mock_jira_client.get_workflow_scheme.return_value = software_scheme_detail

        result = get_workflow_scheme(
            client=mock_jira_client, scheme_id=10100, show_projects=True
        )

        # Result should include projects info
        assert "projects" in result


class TestGetWorkflowSchemeWithDraft:
    """Test getting draft version of scheme."""

    def test_get_workflow_scheme_with_draft(
        self, mock_jira_client, software_scheme_detail
    ):
        """Test getting draft version if exists."""
        from get_workflow_scheme import get_workflow_scheme

        draft_scheme = {**software_scheme_detail, "draft": True}
        mock_jira_client.get_workflow_scheme.return_value = draft_scheme

        get_workflow_scheme(client=mock_jira_client, scheme_id=10100, return_draft=True)

        mock_jira_client.get_workflow_scheme.assert_called_once_with(
            10100, return_draft_if_exists=True
        )


class TestGetWorkflowSchemeOutputFormats:
    """Test output formatting."""

    def test_get_workflow_scheme_format_json(
        self, mock_jira_client, software_scheme_detail
    ):
        """Test JSON output format."""
        import json

        from get_workflow_scheme import format_scheme_json, get_workflow_scheme

        mock_jira_client.get_workflow_scheme.return_value = software_scheme_detail

        result = get_workflow_scheme(client=mock_jira_client, scheme_id=10100)
        output = format_scheme_json(result)

        parsed = json.loads(output)
        assert parsed["name"] == "Software Development Scheme"

    def test_get_workflow_scheme_format_text(
        self, mock_jira_client, software_scheme_detail
    ):
        """Test text output format."""
        from get_workflow_scheme import format_scheme_details, get_workflow_scheme

        mock_jira_client.get_workflow_scheme.return_value = software_scheme_detail

        result = get_workflow_scheme(
            client=mock_jira_client, scheme_id=10100, show_mappings=True
        )
        output = format_scheme_details(result)

        assert "Software Development Scheme" in output


class TestGetWorkflowSchemeErrorHandling:
    """Test error handling scenarios."""

    def test_get_workflow_scheme_missing_params(self, mock_jira_client):
        """Test error when neither id nor name provided."""
        from assistant_skills_lib.error_handler import ValidationError
        from get_workflow_scheme import get_workflow_scheme

        with pytest.raises(ValidationError):
            get_workflow_scheme(client=mock_jira_client)

    def test_get_workflow_scheme_no_permission(self, mock_jira_client):
        """Test error when user lacks admin permission."""
        from get_workflow_scheme import get_workflow_scheme

        from jira_assistant_skills_lib import PermissionError as JiraPermissionError

        mock_jira_client.get_workflow_scheme.side_effect = JiraPermissionError(
            "Requires admin permission"
        )

        with pytest.raises(JiraPermissionError):
            get_workflow_scheme(client=mock_jira_client, scheme_id=10100)
