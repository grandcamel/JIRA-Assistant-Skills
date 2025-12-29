"""
Tests for comment visibility (internal vs external comments).
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.collaborate
@pytest.mark.unit
class TestCommentVisibility:
    """Tests for adding comments with visibility restrictions."""

    @patch('add_comment.get_jira_client')
    def test_add_internal_comment_role(self, mock_get_client, mock_jira_client, sample_comment_with_visibility):
        """Test adding comment visible only to a role."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.add_comment_with_visibility.return_value = sample_comment_with_visibility

        from add_comment import add_comment_with_visibility

        result = add_comment_with_visibility(
            'PROJ-123',
            'Internal admin note',
            format_type='text',
            visibility_type='role',
            visibility_value='Administrators',
            profile=None
        )

        assert result['id'] == '10002'
        assert result['visibility']['type'] == 'role'
        assert result['visibility']['value'] == 'Administrators'
        mock_jira_client.add_comment_with_visibility.assert_called_once()
        call_args = mock_jira_client.add_comment_with_visibility.call_args
        assert call_args[1]['visibility_type'] == 'role'
        assert call_args[1]['visibility_value'] == 'Administrators'

    @patch('add_comment.get_jira_client')
    def test_add_internal_comment_group(self, mock_get_client, mock_jira_client):
        """Test adding comment visible only to a group."""
        mock_get_client.return_value = mock_jira_client
        group_comment = {
            'id': '10003',
            'author': {'displayName': 'Test User'},
            'body': {'type': 'doc', 'version': 1, 'content': []},
            'visibility': {
                'type': 'group',
                'value': 'jira-developers',
                'identifier': 'jira-developers'
            }
        }
        mock_jira_client.add_comment_with_visibility.return_value = group_comment

        from add_comment import add_comment_with_visibility

        result = add_comment_with_visibility(
            'PROJ-123',
            'Dev team note',
            format_type='text',
            visibility_type='group',
            visibility_value='jira-developers',
            profile=None
        )

        assert result['visibility']['type'] == 'group'
        assert result['visibility']['value'] == 'jira-developers'

    @patch('add_comment.get_jira_client')
    def test_add_public_comment(self, mock_get_client, mock_jira_client, sample_comment):
        """Test adding comment visible to all (default)."""
        mock_get_client.return_value = mock_jira_client
        # Use regular add_comment for public comments
        mock_jira_client.add_comment.return_value = sample_comment

        from add_comment import add_comment

        result = add_comment(
            'PROJ-123',
            'Public note',
            format_type='text',
            profile=None
        )

        # Should not have visibility restrictions
        assert result.get('visibility') is None
        mock_jira_client.add_comment.assert_called_once()

    @patch('update_comment.get_jira_client')
    def test_update_comment_preserve_visibility(self, mock_get_client, mock_jira_client, sample_comment_with_visibility):
        """Test that updating preserves visibility."""
        mock_get_client.return_value = mock_jira_client
        # When updating, the API returns the comment with preserved visibility
        mock_jira_client.update_comment.return_value = sample_comment_with_visibility

        from update_comment import update_comment

        result = update_comment('PROJ-123', '10002', 'Updated internal note', profile=None)

        # Visibility should be preserved
        assert result['visibility']['type'] == 'role'
        assert result['visibility']['value'] == 'Administrators'

    @patch('get_comments.get_jira_client')
    def test_get_comment_shows_visibility(self, mock_get_client, mock_jira_client, sample_comment_with_visibility):
        """Test that visibility is shown in output."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_comment.return_value = sample_comment_with_visibility

        from get_comments import get_comment_by_id

        result = get_comment_by_id('PROJ-123', '10002', profile=None)

        # Should include visibility info
        assert 'visibility' in result
        assert result['visibility']['type'] == 'role'

    @patch('add_comment.get_jira_client')
    def test_invalid_visibility_role(self, mock_get_client, mock_jira_client):
        """Test error for invalid role name."""
        from error_handler import ValidationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.add_comment_with_visibility.side_effect = ValidationError(
            "Invalid role: InvalidRole"
        )

        from add_comment import add_comment_with_visibility

        with pytest.raises(ValidationError):
            add_comment_with_visibility(
                'PROJ-123',
                'Test comment',
                visibility_type='role',
                visibility_value='InvalidRole',
                profile=None
            )


@pytest.mark.collaborate
@pytest.mark.unit
class TestCommentVisibilityErrorHandling:
    """Test API error handling scenarios for comment visibility."""

    @patch('add_comment.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.add_comment_with_visibility.side_effect = AuthenticationError("Invalid API token")

        from add_comment import add_comment_with_visibility

        with pytest.raises(AuthenticationError):
            add_comment_with_visibility(
                'PROJ-123',
                'Test comment',
                visibility_type='role',
                visibility_value='Administrators',
                profile=None
            )

    @patch('add_comment.get_jira_client')
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.add_comment_with_visibility.side_effect = PermissionError("No permission to add comments")

        from add_comment import add_comment_with_visibility

        with pytest.raises(PermissionError):
            add_comment_with_visibility(
                'PROJ-123',
                'Test comment',
                visibility_type='role',
                visibility_value='Administrators',
                profile=None
            )

    @patch('add_comment.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.add_comment_with_visibility.side_effect = JiraError("Rate limit exceeded", status_code=429)

        from add_comment import add_comment_with_visibility

        with pytest.raises(JiraError) as exc_info:
            add_comment_with_visibility(
                'PROJ-123',
                'Test comment',
                visibility_type='role',
                visibility_value='Administrators',
                profile=None
            )
        assert exc_info.value.status_code == 429

    @patch('add_comment.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.add_comment_with_visibility.side_effect = JiraError("Internal server error", status_code=500)

        from add_comment import add_comment_with_visibility

        with pytest.raises(JiraError) as exc_info:
            add_comment_with_visibility(
                'PROJ-123',
                'Test comment',
                visibility_type='role',
                visibility_value='Administrators',
                profile=None
            )
        assert exc_info.value.status_code == 500
