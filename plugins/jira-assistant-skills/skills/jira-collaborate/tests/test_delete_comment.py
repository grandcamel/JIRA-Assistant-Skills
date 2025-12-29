"""
Tests for delete_comment.py - Delete comment from an issue.
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.collaborate
@pytest.mark.unit
class TestDeleteComment:
    """Tests for deleting comments."""

    @patch('delete_comment.get_jira_client')
    def test_delete_comment(self, mock_get_client, mock_jira_client):
        """Test deleting a comment."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete_comment.return_value = None

        from delete_comment import delete_comment

        # Should succeed without error
        delete_comment('PROJ-123', '10001', profile=None)

        mock_jira_client.delete_comment.assert_called_once_with('PROJ-123', '10001')

    @patch('delete_comment.get_jira_client')
    def test_delete_comment_not_author(self, mock_get_client, mock_jira_client):
        """Test error when not comment author."""
        from error_handler import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete_comment.side_effect = PermissionError(
            "You do not have permission to delete this comment"
        )

        from delete_comment import delete_comment

        with pytest.raises(PermissionError):
            delete_comment('PROJ-123', '10001', profile=None)

    @patch('delete_comment.get_jira_client')
    def test_delete_comment_not_found(self, mock_get_client, mock_jira_client):
        """Test error when comment doesn't exist."""
        from error_handler import NotFoundError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete_comment.side_effect = NotFoundError(
            "Comment 99999 not found"
        )

        from delete_comment import delete_comment

        with pytest.raises(NotFoundError):
            delete_comment('PROJ-123', '99999', profile=None)

    @patch('delete_comment.get_jira_client')
    @patch('builtins.input', return_value='yes')
    def test_delete_with_confirmation(self, mock_input, mock_get_client, mock_jira_client, sample_comment):
        """Test confirmation prompt."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comment.return_value = sample_comment
        mock_jira_client.delete_comment.return_value = None

        from delete_comment import delete_comment_with_confirm

        result = delete_comment_with_confirm('PROJ-123', '10001', profile=None)

        assert result is True
        mock_input.assert_called_once()
        mock_jira_client.delete_comment.assert_called_once_with('PROJ-123', '10001')

    @patch('delete_comment.get_jira_client')
    def test_delete_dry_run(self, mock_get_client, mock_jira_client, sample_comment):
        """Test dry-run mode."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comment.return_value = sample_comment

        from delete_comment import delete_comment_dry_run

        result = delete_comment_dry_run('PROJ-123', '10001', profile=None)

        # Should return comment info but not delete
        assert result['id'] == '10001'
        mock_jira_client.get_comment.assert_called_once_with('PROJ-123', '10001')
        mock_jira_client.delete_comment.assert_not_called()


@pytest.mark.collaborate
@pytest.mark.unit
class TestDeleteCommentErrorHandling:
    """Test API error handling scenarios for delete_comment."""

    @patch('delete_comment.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete_comment.side_effect = AuthenticationError("Invalid API token")

        from delete_comment import delete_comment

        with pytest.raises(AuthenticationError):
            delete_comment('PROJ-123', '10001', profile=None)

    @patch('delete_comment.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete_comment.side_effect = JiraError("Rate limit exceeded", status_code=429)

        from delete_comment import delete_comment

        with pytest.raises(JiraError) as exc_info:
            delete_comment('PROJ-123', '10001', profile=None)
        assert exc_info.value.status_code == 429

    @patch('delete_comment.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.delete_comment.side_effect = JiraError("Internal server error", status_code=500)

        from delete_comment import delete_comment

        with pytest.raises(JiraError) as exc_info:
            delete_comment('PROJ-123', '10001', profile=None)
        assert exc_info.value.status_code == 500
