"""
Tests for update_asset.py script.

Tests asset update functionality.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import update_asset


@pytest.mark.jsm
@pytest.mark.unit
class TestUpdateAsset:
    """Test asset update functionality."""

    def test_update_asset_single_attribute(self, mock_jira_client, sample_asset):
        """Test updating one attribute."""
        mock_jira_client.has_assets_license.return_value = True
        mock_jira_client.update_asset.return_value = sample_asset

        attributes = {"Status": "Inactive"}

        with patch("update_asset.get_jira_client", return_value=mock_jira_client):
            result = update_asset.update_asset(10001, attributes)

        assert result["id"] == "10001"
        mock_jira_client.update_asset.assert_called_once_with(10001, attributes)

    def test_update_asset_multiple_attributes(self, mock_jira_client, sample_asset):
        """Test updating multiple attributes."""
        mock_jira_client.has_assets_license.return_value = True
        mock_jira_client.update_asset.return_value = sample_asset

        attributes = {"Status": "Inactive", "Location": "DC-2"}

        with patch("update_asset.get_jira_client", return_value=mock_jira_client):
            update_asset.update_asset(10001, attributes)

        mock_jira_client.update_asset.assert_called_once_with(10001, attributes)

    def test_update_asset_dry_run(self, mock_jira_client):
        """Test dry-run mode doesn't update asset."""
        mock_jira_client.has_assets_license.return_value = True

        attributes = {"Status": "Inactive"}

        with patch("update_asset.get_jira_client", return_value=mock_jira_client):
            result = update_asset.update_asset(10001, attributes, dry_run=True)

        assert result is None
        mock_jira_client.update_asset.assert_not_called()

    def test_update_asset_no_license(self, mock_jira_client):
        """Test error when Assets license not available."""
        mock_jira_client.has_assets_license.return_value = False

        with patch("update_asset.get_jira_client", return_value=mock_jira_client):
            with pytest.raises(SystemExit):
                update_asset.update_asset(10001, {"Status": "Inactive"})

    def test_parse_attributes(self):
        """Test parsing attribute list."""
        attr_list = ["Status=Inactive", "Location=DC-2"]
        result = update_asset.parse_attributes(attr_list)

        assert result == {"Status": "Inactive", "Location": "DC-2"}

    def test_update_asset_error(self, mock_jira_client):
        """Test error when update fails."""
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.has_assets_license.return_value = True
        mock_jira_client.update_asset.side_effect = JiraError("Update failed")

        with patch("update_asset.get_jira_client", return_value=mock_jira_client):
            with pytest.raises(JiraError, match="Update failed"):
                update_asset.update_asset(10001, {"Status": "Inactive"})
