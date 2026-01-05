"""
Tests for create_version.py - Create a project version.
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
class TestCreateVersion:
    """Tests for creating project versions."""

    @patch("create_version.get_jira_client")
    def test_create_basic_version(
        self, mock_get_client, mock_jira_client, sample_version
    ):
        """Test creating a basic version with name only."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_version.return_value = copy.deepcopy(sample_version)

        from create_version import create_version

        result = create_version(project="PROJ", name="v1.0.0", profile=None)

        assert result["name"] == "v1.0.0"
        assert result["project"] == "PROJ"
        mock_jira_client.create_version.assert_called_once()

    @patch("create_version.get_jira_client")
    def test_create_version_with_description(self, mock_get_client, mock_jira_client):
        """Test creating version with description."""
        mock_get_client.return_value = mock_jira_client
        version_with_desc = {
            "id": "10001",
            "name": "v1.1.0",
            "description": "Bug fix release",
            "project": "PROJ",
            "released": False,
            "archived": False,
        }
        mock_jira_client.create_version.return_value = version_with_desc

        from create_version import create_version

        result = create_version(
            project="PROJ", name="v1.1.0", description="Bug fix release", profile=None
        )

        assert result["description"] == "Bug fix release"

    @patch("create_version.get_jira_client")
    def test_create_version_with_dates(self, mock_get_client, mock_jira_client):
        """Test creating version with start and release dates."""
        mock_get_client.return_value = mock_jira_client
        version_with_dates = {
            "id": "10002",
            "name": "v2.0.0",
            "project": "PROJ",
            "startDate": "2025-02-01",
            "releaseDate": "2025-03-01",
            "released": False,
            "archived": False,
        }
        mock_jira_client.create_version.return_value = version_with_dates

        from create_version import create_version

        result = create_version(
            project="PROJ",
            name="v2.0.0",
            start_date="2025-02-01",
            release_date="2025-03-01",
            profile=None,
        )

        assert result["startDate"] == "2025-02-01"
        assert result["releaseDate"] == "2025-03-01"

    @patch("create_version.get_jira_client")
    def test_create_released_version(self, mock_get_client, mock_jira_client):
        """Test creating version that is already released."""
        mock_get_client.return_value = mock_jira_client
        released_version = {
            "id": "10003",
            "name": "v0.9.0",
            "project": "PROJ",
            "released": True,
            "releaseDate": "2025-01-15",
            "archived": False,
        }
        mock_jira_client.create_version.return_value = released_version

        from create_version import create_version

        result = create_version(
            project="PROJ",
            name="v0.9.0",
            released=True,
            release_date="2025-01-15",
            profile=None,
        )

        assert result["released"] is True

    @patch("create_version.get_jira_client")
    def test_create_archived_version(self, mock_get_client, mock_jira_client):
        """Test creating archived version."""
        mock_get_client.return_value = mock_jira_client
        archived_version = {
            "id": "10004",
            "name": "v0.8.0",
            "project": "PROJ",
            "released": True,
            "archived": True,
        }
        mock_jira_client.create_version.return_value = archived_version

        from create_version import create_version

        result = create_version(
            project="PROJ", name="v0.8.0", archived=True, profile=None
        )

        assert result["archived"] is True

    @patch("create_version.get_jira_client")
    def test_create_version_dry_run(self, mock_get_client, mock_jira_client):
        """Test dry-run mode shows what would be created."""
        mock_get_client.return_value = mock_jira_client

        from create_version import create_version_dry_run

        result = create_version_dry_run(
            project="PROJ",
            name="v3.0.0",
            description="Major release",
            start_date="2025-04-01",
            release_date="2025-06-01",
            released=False,
            archived=False,
        )

        # Dry run should return data without calling API
        assert result["project"] == "PROJ"
        assert result["name"] == "v3.0.0"
        assert result["description"] == "Major release"
        mock_jira_client.create_version.assert_not_called()


@pytest.mark.lifecycle
@pytest.mark.unit
class TestCreateVersionErrorHandling:
    """Test API error handling for create_version."""

    @patch("create_version.get_jira_client")
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_version.side_effect = AuthenticationError(
            "Invalid token"
        )

        from create_version import create_version

        with pytest.raises(AuthenticationError):
            create_version(project="PROJ", name="v1.0.0", profile=None)

    @patch("create_version.get_jira_client")
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_version.side_effect = PermissionError(
            "Cannot create version"
        )

        from create_version import create_version

        with pytest.raises(PermissionError):
            create_version(project="PROJ", name="v1.0.0", profile=None)

    @patch("create_version.get_jira_client")
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when project doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_version.side_effect = NotFoundError(
            "Project", "INVALID"
        )

        from create_version import create_version

        with pytest.raises(NotFoundError):
            create_version(project="INVALID", name="v1.0.0", profile=None)

    @patch("create_version.get_jira_client")
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_version.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from create_version import create_version

        with pytest.raises(JiraError) as exc_info:
            create_version(project="PROJ", name="v1.0.0", profile=None)
        assert exc_info.value.status_code == 429

    @patch("create_version.get_jira_client")
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_version.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from create_version import create_version

        with pytest.raises(JiraError) as exc_info:
            create_version(project="PROJ", name="v1.0.0", profile=None)
        assert exc_info.value.status_code == 500


@pytest.mark.lifecycle
@pytest.mark.unit
class TestCreateVersionMain:
    """Tests for main() function."""

    @patch("create_version.get_jira_client")
    def test_main_basic(
        self, mock_get_client, mock_jira_client, sample_version, capsys
    ):
        """Test main with basic args."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_version.return_value = copy.deepcopy(sample_version)

        from create_version import main

        main(["PROJ", "--name", "v1.0.0"])

        captured = capsys.readouterr()
        assert "Created version" in captured.out

    @patch("create_version.get_jira_client")
    def test_main_with_description(
        self, mock_get_client, mock_jira_client, sample_version, capsys
    ):
        """Test main with --description."""
        mock_get_client.return_value = mock_jira_client
        version = copy.deepcopy(sample_version)
        version["description"] = "Major release"
        mock_jira_client.create_version.return_value = version

        from create_version import main

        main(["PROJ", "--name", "v1.0.0", "--description", "Major release"])

        captured = capsys.readouterr()
        assert "Major release" in captured.out

    @patch("create_version.get_jira_client")
    def test_main_with_dates(
        self, mock_get_client, mock_jira_client, sample_version, capsys
    ):
        """Test main with --start-date and --release-date."""
        mock_get_client.return_value = mock_jira_client
        version = copy.deepcopy(sample_version)
        version["startDate"] = "2025-02-01"
        version["releaseDate"] = "2025-03-01"
        mock_jira_client.create_version.return_value = version

        from create_version import main

        main(
            [
                "PROJ",
                "--name",
                "v1.0.0",
                "--start-date",
                "2025-02-01",
                "--release-date",
                "2025-03-01",
            ]
        )

        captured = capsys.readouterr()
        assert "2025-02-01" in captured.out
        assert "2025-03-01" in captured.out

    @patch("create_version.get_jira_client")
    def test_main_released(
        self, mock_get_client, mock_jira_client, sample_version, capsys
    ):
        """Test main with --released."""
        mock_get_client.return_value = mock_jira_client
        version = copy.deepcopy(sample_version)
        version["released"] = True
        mock_jira_client.create_version.return_value = version

        from create_version import main

        main(["PROJ", "--name", "v1.0.0", "--released"])

        captured = capsys.readouterr()
        assert "Released" in captured.out

    @patch("create_version.get_jira_client")
    def test_main_archived(
        self, mock_get_client, mock_jira_client, sample_version, capsys
    ):
        """Test main with --archived."""
        mock_get_client.return_value = mock_jira_client
        version = copy.deepcopy(sample_version)
        version["archived"] = True
        mock_jira_client.create_version.return_value = version

        from create_version import main

        main(["PROJ", "--name", "v1.0.0", "--archived"])

        captured = capsys.readouterr()
        assert "Archived" in captured.out

    @patch("create_version.get_jira_client")
    def test_main_dry_run(self, mock_get_client, mock_jira_client, capsys):
        """Test main with --dry-run."""
        mock_get_client.return_value = mock_jira_client

        from create_version import main

        main(["PROJ", "--name", "v2.0.0", "--dry-run"])

        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
        assert "v2.0.0" in captured.out
        mock_jira_client.create_version.assert_not_called()

    @patch("create_version.get_jira_client")
    def test_main_dry_run_with_all_options(
        self, mock_get_client, mock_jira_client, capsys
    ):
        """Test main dry-run with all options."""
        mock_get_client.return_value = mock_jira_client

        from create_version import main

        main(
            [
                "PROJ",
                "--name",
                "v2.0.0",
                "--description",
                "Test",
                "--start-date",
                "2025-02-01",
                "--release-date",
                "2025-03-01",
                "--released",
                "--dry-run",
            ]
        )

        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
        assert "Test" in captured.out
        assert "2025-02-01" in captured.out

    @patch("create_version.get_jira_client")
    def test_main_with_profile(
        self, mock_get_client, mock_jira_client, sample_version, capsys
    ):
        """Test main with --profile."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_version.return_value = copy.deepcopy(sample_version)

        from create_version import main

        main(["PROJ", "--name", "v1.0.0", "--profile", "dev"])

        mock_get_client.assert_called_with("dev")

    @patch("create_version.get_jira_client")
    def test_main_jira_error(self, mock_get_client, mock_jira_client, capsys):
        """Test main with JIRA API error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_version.side_effect = JiraError(
            "API Error", status_code=500
        )

        from create_version import main

        with pytest.raises(SystemExit) as exc_info:
            main(["PROJ", "--name", "v1.0.0"])

        assert exc_info.value.code == 1
