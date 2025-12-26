"""
Tests for upload_attachment.py - Upload attachments to issues.
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.fixture
def sample_attachment():
    """Sample attachment response."""
    return [
        {
            'id': '10001',
            'filename': 'test.txt',
            'size': 100,
            'mimeType': 'text/plain',
            'author': {
                'accountId': '5b10a2844c20165700ede21g',
                'displayName': 'Alice Smith'
            },
            'created': '2025-01-14T09:00:00.000+0000'
        }
    ]


@pytest.mark.collaborate
@pytest.mark.unit
class TestUploadAttachment:
    """Tests for uploading attachments."""

    @patch('upload_attachment.get_jira_client')
    def test_upload_attachment_success(self, mock_get_client, mock_jira_client, sample_attachment, tmp_path):
        """Test successful attachment upload."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.upload_file.return_value = sample_attachment

        # Create temp file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        from upload_attachment import upload_attachment

        result = upload_attachment('PROJ-123', str(test_file), profile=None)

        assert result[0]['filename'] == 'test.txt'
        mock_jira_client.upload_file.assert_called_once()

    @patch('upload_attachment.get_jira_client')
    def test_upload_attachment_custom_name(self, mock_get_client, mock_jira_client, tmp_path):
        """Test upload with custom filename."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.upload_file.return_value = [
            {'id': '10001', 'filename': 'custom_name.txt', 'size': 100}
        ]

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        from upload_attachment import upload_attachment

        result = upload_attachment('PROJ-123', str(test_file), file_name='custom_name.txt', profile=None)

        call_args = mock_jira_client.upload_file.call_args
        assert call_args[1]['file_name'] == 'custom_name.txt'

    def test_upload_attachment_file_not_found(self):
        """Test error when file doesn't exist."""
        from error_handler import ValidationError

        from upload_attachment import upload_attachment

        with pytest.raises(ValidationError):
            upload_attachment('PROJ-123', '/nonexistent/file.txt', profile=None)

    def test_upload_attachment_invalid_issue_key(self, tmp_path):
        """Test error for invalid issue key."""
        from error_handler import ValidationError

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        from upload_attachment import upload_attachment

        with pytest.raises(ValidationError):
            upload_attachment('invalid', str(test_file), profile=None)


@pytest.mark.collaborate
@pytest.mark.unit
class TestUploadAttachmentErrorHandling:
    """Test API error handling scenarios for upload_attachment."""

    @patch('upload_attachment.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client, tmp_path):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.upload_file.side_effect = AuthenticationError("Invalid API token")

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        from upload_attachment import upload_attachment

        with pytest.raises(AuthenticationError):
            upload_attachment('PROJ-123', str(test_file), profile=None)

    @patch('upload_attachment.get_jira_client')
    def test_permission_error(self, mock_get_client, mock_jira_client, tmp_path):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.upload_file.side_effect = PermissionError("No permission to add attachments")

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        from upload_attachment import upload_attachment

        with pytest.raises(PermissionError):
            upload_attachment('PROJ-123', str(test_file), profile=None)

    @patch('upload_attachment.get_jira_client')
    def test_not_found_error(self, mock_get_client, mock_jira_client, tmp_path):
        """Test handling of 404 not found."""
        from error_handler import NotFoundError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.upload_file.side_effect = NotFoundError("Issue PROJ-999 not found")

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        from upload_attachment import upload_attachment

        with pytest.raises(NotFoundError):
            upload_attachment('PROJ-999', str(test_file), profile=None)

    @patch('upload_attachment.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client, tmp_path):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.upload_file.side_effect = JiraError("Rate limit exceeded", status_code=429)

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        from upload_attachment import upload_attachment

        with pytest.raises(JiraError) as exc_info:
            upload_attachment('PROJ-123', str(test_file), profile=None)
        assert exc_info.value.status_code == 429

    @patch('upload_attachment.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client, tmp_path):
        """Test handling of 500 server error."""
        from error_handler import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.upload_file.side_effect = JiraError("Internal server error", status_code=500)

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        from upload_attachment import upload_attachment

        with pytest.raises(JiraError) as exc_info:
            upload_attachment('PROJ-123', str(test_file), profile=None)
        assert exc_info.value.status_code == 500
