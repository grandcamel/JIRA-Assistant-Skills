"""
Tests for get_asset.py script.

Tests asset retrieval and formatting.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import get_asset


@pytest.mark.jsm
@pytest.mark.unit
class TestGetAsset:
    """Test asset retrieval functionality."""

    def test_get_asset_by_id(self, mock_jira_client, sample_asset):
        """Test fetching asset by object ID."""
        mock_jira_client.has_assets_license.return_value = True
        mock_jira_client.get_asset.return_value = sample_asset

        with patch("get_asset.get_jira_client", return_value=mock_jira_client):
            result = get_asset.get_asset(10001)

        assert result["id"] == "10001"
        assert result["objectKey"] == "ASSET-123"
        mock_jira_client.get_asset.assert_called_once_with(10001)

    def test_get_asset_no_license(self, mock_jira_client):
        """Test error when Assets license not available."""
        mock_jira_client.has_assets_license.return_value = False

        with patch("get_asset.get_jira_client", return_value=mock_jira_client):
            with pytest.raises(SystemExit):
                get_asset.get_asset(10001)

    def test_format_text(self, sample_asset):
        """Test human-readable output."""
        output = get_asset.format_text(sample_asset)

        assert "ASSET-123" in output
        assert "web-server-01" in output
        assert "Server" in output
        assert "192.168.1.100" in output

    def test_format_json(self, sample_asset):
        """Test JSON output format."""
        output = get_asset.format_json(sample_asset)

        data = json.loads(output)
        assert data["id"] == "10001"
        assert data["objectKey"] == "ASSET-123"

    def test_get_asset_with_attributes(self, sample_asset):
        """Test asset includes all attributes."""
        output = get_asset.format_text(sample_asset)

        assert "IP Address" in output
        assert "Status" in output
        assert "Location" in output

    def test_get_asset_error(self, mock_jira_client):
        """Test error when asset doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.has_assets_license.return_value = True
        mock_jira_client.get_asset.side_effect = NotFoundError("Asset not found")

        with patch("get_asset.get_jira_client", return_value=mock_jira_client):
            with pytest.raises(NotFoundError, match="Asset not found"):
                get_asset.get_asset(999999)
