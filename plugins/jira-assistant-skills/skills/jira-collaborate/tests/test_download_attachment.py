"""
Tests for download_attachment.py - Download attachments from JIRA issues.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.fixture
def sample_attachments():
    """Sample attachments list."""
    return [
        {
            "id": "10001",
            "filename": "screenshot.png",
            "size": 102400,
            "mimeType": "image/png",
            "created": "2024-01-15T10:00:00.000+0000",
            "author": {"displayName": "John Smith"},
            "content": "https://test.atlassian.net/secure/attachment/10001/screenshot.png",
        },
        {
            "id": "10002",
            "filename": "report.pdf",
            "size": 5242880,
            "mimeType": "application/pdf",
            "created": "2024-01-14T09:00:00.000+0000",
            "author": {"displayName": "Jane Doe"},
            "content": "https://test.atlassian.net/secure/attachment/10002/report.pdf",
        },
        {
            "id": "10003",
            "filename": "data.csv",
            "size": 512,
            "mimeType": "text/csv",
            "created": "2024-01-13T08:00:00.000+0000",
            "author": {"displayName": "Bob Jones"},
            "content": "https://test.atlassian.net/secure/attachment/10003/data.csv",
        },
    ]


@pytest.mark.collaborate
@pytest.mark.unit
class TestListAttachments:
    """Tests for list_attachments function."""

    def test_list_attachments_success(self, mock_jira_client, sample_attachments):
        """Test listing attachments for an issue."""
        mock_jira_client.get_attachments.return_value = sample_attachments

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import list_attachments

            result = list_attachments("PROJ-123")

            assert len(result) == 3
            assert result[0]["filename"] == "screenshot.png"
            mock_jira_client.get_attachments.assert_called_once_with("PROJ-123")

    def test_list_attachments_empty(self, mock_jira_client):
        """Test listing when no attachments exist."""
        mock_jira_client.get_attachments.return_value = []

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import list_attachments

            result = list_attachments("PROJ-123")

            assert result == []

@pytest.mark.collaborate
@pytest.mark.unit
class TestDownloadAttachment:
    """Tests for download_attachment function."""

    def test_download_by_id(self, mock_jira_client, sample_attachments, tmp_path):
        """Test downloading attachment by ID."""
        mock_jira_client.get_attachments.return_value = sample_attachments

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import download_attachment

            result = download_attachment(
                "PROJ-123", attachment_id="10001", output_dir=str(tmp_path)
            )

            assert "screenshot.png" in result
            mock_jira_client.download_file.assert_called_once()

    def test_download_by_name(self, mock_jira_client, sample_attachments, tmp_path):
        """Test downloading attachment by name."""
        mock_jira_client.get_attachments.return_value = sample_attachments

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import download_attachment

            result = download_attachment(
                "PROJ-123", attachment_name="report.pdf", output_dir=str(tmp_path)
            )

            assert "report.pdf" in result

    def test_download_id_not_found(self, mock_jira_client, sample_attachments):
        """Test error when attachment ID not found."""
        mock_jira_client.get_attachments.return_value = sample_attachments

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import download_attachment

            from jira_assistant_skills_lib import ValidationError

            with pytest.raises(ValidationError) as exc_info:
                download_attachment("PROJ-123", attachment_id="99999")
            assert "not found" in str(exc_info.value)

    def test_download_name_not_found(self, mock_jira_client, sample_attachments):
        """Test error when attachment name not found."""
        mock_jira_client.get_attachments.return_value = sample_attachments

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import download_attachment

            from jira_assistant_skills_lib import ValidationError

            with pytest.raises(ValidationError) as exc_info:
                download_attachment("PROJ-123", attachment_name="nonexistent.txt")
            assert "not found" in str(exc_info.value)

    def test_download_no_identifier(self, mock_jira_client, sample_attachments):
        """Test error when neither ID nor name specified."""
        mock_jira_client.get_attachments.return_value = sample_attachments

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import download_attachment

            from jira_assistant_skills_lib import ValidationError

            with pytest.raises(ValidationError) as exc_info:
                download_attachment("PROJ-123")
            assert "--id" in str(exc_info.value) or "--name" in str(exc_info.value)

    def test_download_no_content_url(self, mock_jira_client):
        """Test error when attachment has no content URL."""
        mock_jira_client.get_attachments.return_value = [
            {"id": "10001", "filename": "test.txt", "content": None}
        ]

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import download_attachment

            from jira_assistant_skills_lib import ValidationError

            with pytest.raises(ValidationError) as exc_info:
                download_attachment("PROJ-123", attachment_id="10001")
            assert "No content URL" in str(exc_info.value)


@pytest.mark.collaborate
@pytest.mark.unit
class TestDownloadAllAttachments:
    """Tests for download_all_attachments function."""

    def test_download_all(self, mock_jira_client, sample_attachments, tmp_path):
        """Test downloading all attachments."""
        mock_jira_client.get_attachments.return_value = sample_attachments

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import download_all_attachments

            result = download_all_attachments("PROJ-123", output_dir=str(tmp_path))

            assert len(result) == 3
            assert mock_jira_client.download_file.call_count == 3

    def test_download_all_empty(self, mock_jira_client, tmp_path):
        """Test downloading when no attachments exist."""
        mock_jira_client.get_attachments.return_value = []

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import download_all_attachments

            result = download_all_attachments("PROJ-123", output_dir=str(tmp_path))

            assert result == []
            mock_jira_client.download_file.assert_not_called()

    def test_download_all_skips_no_content(self, mock_jira_client, tmp_path):
        """Test that attachments without content URL are skipped."""
        mock_jira_client.get_attachments.return_value = [
            {
                "id": "10001",
                "filename": "test.txt",
                "content": "https://example.com/test.txt",
            },
            {"id": "10002", "filename": "no-content.txt", "content": None},
        ]

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import download_all_attachments

            result = download_all_attachments("PROJ-123", output_dir=str(tmp_path))

            assert len(result) == 1
            assert mock_jira_client.download_file.call_count == 1

    def test_download_all_handles_duplicates(self, mock_jira_client, tmp_path):
        """Test handling of duplicate filenames."""
        mock_jira_client.get_attachments.return_value = [
            {"id": "10001", "filename": "test.txt", "content": "https://example.com/1"},
            {"id": "10002", "filename": "test.txt", "content": "https://example.com/2"},
        ]

        # Create the first file so the duplicate handling kicks in
        first_file = tmp_path / "test.txt"
        first_file.write_text("first file")

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import download_all_attachments

            result = download_all_attachments("PROJ-123", output_dir=str(tmp_path))

            assert len(result) == 2
            # Second file should have _1 suffix
            assert any("test_1.txt" in path for path in result)


@pytest.mark.collaborate
@pytest.mark.unit
class TestFormatAttachmentList:
    """Tests for format_attachment_list function."""

    def test_format_attachments(self, sample_attachments):
        """Test formatting attachments as a table."""
        from download_attachment import format_attachment_list

        result = format_attachment_list(sample_attachments)

        assert "screenshot.png" in result
        assert "report.pdf" in result
        assert "100.0 KB" in result  # 102400 bytes
        assert "5.0 MB" in result  # 5242880 bytes
        assert "512 B" in result  # 512 bytes

    def test_format_empty_list(self):
        """Test formatting empty attachment list."""
        from download_attachment import format_attachment_list

        result = format_attachment_list([])

        assert "No attachments" in result


@pytest.mark.collaborate
@pytest.mark.unit
class TestDownloadAttachmentMain:
    """Tests for main() function."""

    def test_main_list(self, mock_jira_client, sample_attachments, capsys):
        """Test main with --list."""
        mock_jira_client.get_attachments.return_value = sample_attachments

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import main

            main(["PROJ-123", "--list"])

            captured = capsys.readouterr()
            assert "screenshot.png" in captured.out

    def test_main_list_json(self, mock_jira_client, sample_attachments, capsys):
        """Test main with --list --output json."""
        mock_jira_client.get_attachments.return_value = sample_attachments

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import main

            main(["PROJ-123", "--list", "--output", "json"])

            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert len(data) == 3

    def test_main_download_by_name(
        self, mock_jira_client, sample_attachments, tmp_path, capsys
    ):
        """Test main with --name."""
        mock_jira_client.get_attachments.return_value = sample_attachments

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import main

            main(
                ["PROJ-123", "--name", "screenshot.png", "--output-dir", str(tmp_path)]
            )

            captured = capsys.readouterr()
            assert "Downloaded" in captured.out

    def test_main_download_by_id(
        self, mock_jira_client, sample_attachments, tmp_path, capsys
    ):
        """Test main with --id."""
        mock_jira_client.get_attachments.return_value = sample_attachments

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import main

            main(["PROJ-123", "--id", "10001", "--output-dir", str(tmp_path)])

            captured = capsys.readouterr()
            assert "Downloaded" in captured.out

    def test_main_download_all(
        self, mock_jira_client, sample_attachments, tmp_path, capsys
    ):
        """Test main with --all."""
        mock_jira_client.get_attachments.return_value = sample_attachments

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import main

            main(["PROJ-123", "--all", "--output-dir", str(tmp_path)])

            captured = capsys.readouterr()
            assert "Downloaded 3 attachment" in captured.out

    def test_main_download_all_empty(self, mock_jira_client, tmp_path, capsys):
        """Test main with --all when no attachments."""
        mock_jira_client.get_attachments.return_value = []

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import main

            main(["PROJ-123", "--all", "--output-dir", str(tmp_path)])

            captured = capsys.readouterr()
            assert "No attachments" in captured.out


@pytest.mark.collaborate
@pytest.mark.unit
class TestDownloadAttachmentErrors:
    """Tests for error handling."""

    def test_jira_error_handling(self, mock_jira_client):
        """Test handling of JIRA API errors."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_attachments.side_effect = JiraError(
            "API Error", status_code=500
        )

        with patch(
            "download_attachment.get_jira_client", return_value=mock_jira_client
        ):
            from download_attachment import main

            with pytest.raises(SystemExit) as exc_info:
                main(["PROJ-123", "--list"])
            assert exc_info.value.code == 1

    def test_invalid_issue_key(self, mock_jira_client):
        """Test handling of invalid issue key."""
        from jira_assistant_skills_lib import ValidationError

        with (
            patch("download_attachment.get_jira_client", return_value=mock_jira_client),
            patch(
                "download_attachment.validate_issue_key",
                side_effect=ValidationError("Invalid issue key"),
            ),
        ):
            from download_attachment import main

            with pytest.raises(SystemExit) as exc_info:
                main(["invalid-key", "--list"])
            assert exc_info.value.code == 1
