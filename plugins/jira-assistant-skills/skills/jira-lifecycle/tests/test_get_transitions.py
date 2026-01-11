"""
Tests for get_transitions.py - Get available transitions for an issue.
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
class TestGetTransitions:
    """Tests for getting issue transitions."""

    @patch("get_transitions.get_jira_client")
    def test_get_transitions_success(
        self, mock_get_client, mock_jira_client, sample_transitions
    ):
        """Test getting transitions for an issue."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = copy.deepcopy(
            sample_transitions
        )

        from get_transitions import get_transitions

        result = get_transitions("PROJ-123")

        assert len(result) == 3
        assert any(t["name"] == "In Progress" for t in result)
        mock_jira_client.get_transitions.assert_called_once_with("PROJ-123")

    @patch("get_transitions.get_jira_client")
    def test_get_transitions_empty(self, mock_get_client, mock_jira_client):
        """Test handling when no transitions available."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = []

        from get_transitions import get_transitions

        result = get_transitions("PROJ-123")

        assert result == []

    def test_get_transitions_invalid_issue_key(self):
        """Test error on invalid issue key."""
        from assistant_skills_lib.error_handler import ValidationError
        from get_transitions import get_transitions

        with pytest.raises(ValidationError):
            get_transitions("invalid")


@pytest.mark.lifecycle
@pytest.mark.unit
class TestGetTransitionsErrorHandling:
    """Test API error handling for get_transitions."""

    @patch("get_transitions.get_jira_client")
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = AuthenticationError(
            "Invalid token"
        )

        from get_transitions import get_transitions

        with pytest.raises(AuthenticationError):
            get_transitions("PROJ-123")

    @patch("get_transitions.get_jira_client")
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = PermissionError("Access denied")

        from get_transitions import get_transitions

        with pytest.raises(PermissionError):
            get_transitions("PROJ-123")

    @patch("get_transitions.get_jira_client")
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when issue doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = NotFoundError(
            "Issue", "PROJ-999"
        )

        from get_transitions import get_transitions

        with pytest.raises(NotFoundError):
            get_transitions("PROJ-999")

    @patch("get_transitions.get_jira_client")
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from get_transitions import get_transitions

        with pytest.raises(JiraError) as exc_info:
            get_transitions("PROJ-123")
        assert exc_info.value.status_code == 429

    @patch("get_transitions.get_jira_client")
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from get_transitions import get_transitions

        with pytest.raises(JiraError) as exc_info:
            get_transitions("PROJ-123")
        assert exc_info.value.status_code == 500


@pytest.mark.lifecycle
@pytest.mark.unit
class TestGetTransitionsMain:
    """Tests for main() function."""

    @patch("get_transitions.get_jira_client")
    def test_main_text_output(
        self, mock_get_client, mock_jira_client, sample_transitions, capsys
    ):
        """Test main with text output."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = copy.deepcopy(
            sample_transitions
        )

        from get_transitions import main

        main(["PROJ-123"])

        captured = capsys.readouterr()
        assert "Available transitions for PROJ-123" in captured.out

    @patch("get_transitions.get_jira_client")
    def test_main_json_output(
        self, mock_get_client, mock_jira_client, sample_transitions, capsys
    ):
        """Test main with --output json."""
        import json

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = copy.deepcopy(
            sample_transitions
        )

        from get_transitions import main

        main(["PROJ-123", "--output", "json"])

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert isinstance(output, list)
        assert len(output) == 3

    @patch("get_transitions.get_jira_client")
    def test_main_no_transitions(self, mock_get_client, mock_jira_client, capsys):
        """Test main when no transitions available."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = []

        from get_transitions import main

        main(["PROJ-123"])

        captured = capsys.readouterr()
        assert "No transitions available" in captured.out

    @patch("get_transitions.get_jira_client")
    def test_main_jira_error(self, mock_get_client, mock_jira_client, capsys):
        """Test main with JIRA API error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = JiraError(
            "API Error", status_code=500
        )

        from get_transitions import main

        with pytest.raises(SystemExit) as exc_info:
            main(["PROJ-123"])

        assert exc_info.value.code == 1
