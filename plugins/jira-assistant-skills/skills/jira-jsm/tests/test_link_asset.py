"""
Tests for link_asset.py script.

Tests asset linking to service requests.
"""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path
import sys

scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import link_asset


@pytest.mark.jsm
@pytest.mark.unit
class TestLinkAsset:
    """Test asset linking functionality."""

    def test_link_asset_to_request(self, mock_jira_client):
        """Test linking asset to request."""
        mock_jira_client.has_assets_license.return_value = True
        mock_jira_client.link_asset_to_request.return_value = None

        with patch('link_asset.get_jira_client', return_value=mock_jira_client):
            link_asset.link_asset(10001, "REQ-123")

        mock_jira_client.link_asset_to_request.assert_called_once_with(10001, "REQ-123")

    def test_link_asset_with_comment(self, mock_jira_client):
        """Test linking asset with additional comment."""
        mock_jira_client.has_assets_license.return_value = True
        mock_jira_client.link_asset_to_request.return_value = None
        mock_jira_client.add_request_comment.return_value = None

        with patch('link_asset.get_jira_client', return_value=mock_jira_client):
            link_asset.link_asset(10001, "REQ-123", comment="Primary server")

        mock_jira_client.link_asset_to_request.assert_called_once()
        mock_jira_client.add_request_comment.assert_called_once_with("REQ-123", "Primary server", public=False)

    def test_link_asset_no_license(self, mock_jira_client):
        """Test error when Assets license not available."""
        mock_jira_client.has_assets_license.return_value = False

        with patch('link_asset.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(SystemExit):
                link_asset.link_asset(10001, "REQ-123")

    def test_link_asset_invalid_request(self, mock_jira_client):
        """Test error when request doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError
        mock_jira_client.has_assets_license.return_value = True
        mock_jira_client.link_asset_to_request.side_effect = NotFoundError("Request not found")

        with patch('link_asset.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(NotFoundError, match="Request not found"):
                link_asset.link_asset(10001, "REQ-999")

    def test_link_asset_invalid_asset(self, mock_jira_client):
        """Test error when asset doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError
        mock_jira_client.has_assets_license.return_value = True
        mock_jira_client.link_asset_to_request.side_effect = NotFoundError("Asset not found")

        with patch('link_asset.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(NotFoundError, match="Asset not found"):
                link_asset.link_asset(999999, "REQ-123")

    def test_link_asset_error(self, mock_jira_client):
        """Test error handling during link operation."""
        from jira_assistant_skills_lib import JiraError
        mock_jira_client.has_assets_license.return_value = True
        mock_jira_client.link_asset_to_request.side_effect = JiraError("Link failed")

        with patch('link_asset.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(JiraError, match="Link failed"):
                link_asset.link_asset(10001, "REQ-123")
