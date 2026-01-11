"""
Tests for get_versions.py - Get project versions.
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
class TestGetVersions:
    """Tests for getting project versions."""

    @patch("get_versions.get_jira_client")
    def test_get_all_versions(
        self, mock_get_client, mock_jira_client, sample_versions_list
    ):
        """Test getting all versions for a project."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = copy.deepcopy(sample_versions_list)

        from get_versions import get_versions

        result = get_versions("PROJ")

        assert len(result) == 4
        mock_jira_client.get_versions.assert_called_once_with("PROJ")

    @patch("get_versions.get_jira_client")
    def test_get_version_by_id(self, mock_get_client, mock_jira_client, sample_version):
        """Test getting a specific version by ID."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_version.return_value = copy.deepcopy(sample_version)

        from get_versions import get_version_by_id

        result = get_version_by_id("10000")

        assert result["id"] == "10000"
        assert result["name"] == "v1.0.0"
        mock_jira_client.get_version.assert_called_once_with("10000")

    @patch("get_versions.get_jira_client")
    def test_filter_released_versions(
        self, mock_get_client, mock_jira_client, sample_versions_list
    ):
        """Test filtering for released versions."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = copy.deepcopy(sample_versions_list)

        from get_versions import filter_versions, get_versions

        versions = get_versions("PROJ")
        released = filter_versions(versions, released=True)

        # 2 released versions in sample_versions_list (v0.9.0, v0.5.0)
        assert len(released) == 2
        assert all(v["released"] is True for v in released)

    @patch("get_versions.get_jira_client")
    def test_filter_unreleased_versions(
        self, mock_get_client, mock_jira_client, sample_versions_list
    ):
        """Test filtering for unreleased versions."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = copy.deepcopy(sample_versions_list)

        from get_versions import filter_versions, get_versions

        versions = get_versions("PROJ")
        unreleased = filter_versions(versions, released=False)

        # 2 unreleased versions in sample_versions_list (v1.2.0, v1.0.0)
        assert len(unreleased) == 2
        assert all(not v["released"] for v in unreleased)

    @patch("get_versions.get_jira_client")
    def test_filter_archived_versions(
        self, mock_get_client, mock_jira_client, sample_versions_list
    ):
        """Test filtering for archived versions."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = copy.deepcopy(sample_versions_list)

        from get_versions import filter_versions, get_versions

        versions = get_versions("PROJ")
        archived = filter_versions(versions, archived=True)

        # 1 archived version in sample_versions_list
        assert len(archived) == 1
        assert archived[0]["archived"] is True

    @patch("get_versions.get_jira_client")
    def test_get_version_issue_counts(
        self, mock_get_client, mock_jira_client, sample_version_issue_counts
    ):
        """Test getting issue counts for a version."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_version_issue_counts.return_value = copy.deepcopy(
            sample_version_issue_counts
        )

        from get_versions import get_version_issue_counts

        result = get_version_issue_counts("10000")

        assert result["issuesFixedCount"] == 45
        assert result["issuesAffectedCount"] == 12

    @patch("get_versions.get_jira_client")
    def test_get_version_unresolved_count(
        self, mock_get_client, mock_jira_client, sample_version_unresolved_count
    ):
        """Test getting unresolved issue count for a version."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_version_unresolved_count.return_value = copy.deepcopy(
            sample_version_unresolved_count
        )

        from get_versions import get_version_unresolved_count

        result = get_version_unresolved_count("10000")

        assert result["issuesUnresolvedCount"] == 3
        assert result["issuesCount"] == 48

    @patch("get_versions.get_jira_client")
    def test_versions_table_output(
        self, mock_get_client, mock_jira_client, sample_versions_list, capsys
    ):
        """Test table output format for versions."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = copy.deepcopy(sample_versions_list)

        from get_versions import display_versions_table

        display_versions_table(sample_versions_list)

        captured = capsys.readouterr()
        assert "v1.2.0" in captured.out
        assert "v1.0.0" in captured.out
        assert "v0.9.0" in captured.out


@pytest.mark.lifecycle
@pytest.mark.unit
class TestGetVersionsErrorHandling:
    """Test API error handling for get_versions."""

    @patch("get_versions.get_jira_client")
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.side_effect = AuthenticationError("Invalid token")

        from get_versions import get_versions

        with pytest.raises(AuthenticationError):
            get_versions("PROJ")

    @patch("get_versions.get_jira_client")
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.side_effect = PermissionError(
            "Cannot view versions"
        )

        from get_versions import get_versions

        with pytest.raises(PermissionError):
            get_versions("PROJ")

    @patch("get_versions.get_jira_client")
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when project doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.side_effect = NotFoundError("Project", "INVALID")

        from get_versions import get_versions

        with pytest.raises(NotFoundError):
            get_versions("INVALID")

    @patch("get_versions.get_jira_client")
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from get_versions import get_versions

        with pytest.raises(JiraError) as exc_info:
            get_versions("PROJ")
        assert exc_info.value.status_code == 429

    @patch("get_versions.get_jira_client")
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from get_versions import get_versions

        with pytest.raises(JiraError) as exc_info:
            get_versions("PROJ")
        assert exc_info.value.status_code == 500


@pytest.mark.lifecycle
@pytest.mark.unit
class TestGetVersionsMain:
    """Tests for main() function."""

    @patch("get_versions.get_jira_client")
    def test_main_project_table(
        self, mock_get_client, mock_jira_client, sample_versions_list, capsys
    ):
        """Test main with project argument."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = copy.deepcopy(sample_versions_list)

        from get_versions import main

        main(["PROJ"])

        captured = capsys.readouterr()
        assert "Versions for project PROJ" in captured.out
        assert "v1.0.0" in captured.out

    @patch("get_versions.get_jira_client")
    def test_main_project_json(
        self, mock_get_client, mock_jira_client, sample_versions_list, capsys
    ):
        """Test main with --output json."""
        import json

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = copy.deepcopy(sample_versions_list)

        from get_versions import main

        main(["PROJ", "--output", "json"])

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert isinstance(output, list)
        assert len(output) == 4

    @patch("get_versions.get_jira_client")
    def test_main_released_filter(
        self, mock_get_client, mock_jira_client, sample_versions_list, capsys
    ):
        """Test main with --released filter."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = copy.deepcopy(sample_versions_list)

        from get_versions import main

        main(["PROJ", "--released"])

        captured = capsys.readouterr()
        assert "Versions for project PROJ" in captured.out

    @patch("get_versions.get_jira_client")
    def test_main_unreleased_filter(
        self, mock_get_client, mock_jira_client, sample_versions_list, capsys
    ):
        """Test main with --unreleased filter."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = copy.deepcopy(sample_versions_list)

        from get_versions import main

        main(["PROJ", "--unreleased"])

        captured = capsys.readouterr()
        assert "Versions for project PROJ" in captured.out

    @patch("get_versions.get_jira_client")
    def test_main_version_by_id(
        self, mock_get_client, mock_jira_client, sample_version, capsys
    ):
        """Test main with --id."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_version.return_value = copy.deepcopy(sample_version)

        from get_versions import main

        main(["--id", "10000"])

        captured = capsys.readouterr()
        assert "v1.0.0" in captured.out
        assert "ID: 10000" in captured.out

    @patch("get_versions.get_jira_client")
    def test_main_version_by_id_json(
        self, mock_get_client, mock_jira_client, sample_version, capsys
    ):
        """Test main with --id and --output json."""
        import json

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_version.return_value = copy.deepcopy(sample_version)

        from get_versions import main

        main(["--id", "10000", "--output", "json"])

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["id"] == "10000"

    @patch("get_versions.get_jira_client")
    def test_main_version_counts(
        self,
        mock_get_client,
        mock_jira_client,
        sample_version,
        sample_version_issue_counts,
        sample_version_unresolved_count,
        capsys,
    ):
        """Test main with --id and --counts."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_version.return_value = copy.deepcopy(sample_version)
        mock_jira_client.get_version_issue_counts.return_value = copy.deepcopy(
            sample_version_issue_counts
        )
        mock_jira_client.get_version_unresolved_count.return_value = copy.deepcopy(
            sample_version_unresolved_count
        )

        from get_versions import main

        main(["--id", "10000", "--counts"])

        captured = capsys.readouterr()
        assert "Issue Counts" in captured.out
        assert "Fixed:" in captured.out

    @patch("get_versions.get_jira_client")
    def test_main_jira_error(self, mock_get_client, mock_jira_client, capsys):
        """Test main with JIRA API error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.side_effect = JiraError(
            "API Error", status_code=500
        )

        from get_versions import main

        with pytest.raises(SystemExit) as exc_info:
            main(["PROJ"])

        assert exc_info.value.code == 1
