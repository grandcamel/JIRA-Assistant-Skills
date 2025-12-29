"""
Tests for create_asset.py script.

Tests asset creation functionality.
"""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path
import sys

scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import create_asset


@pytest.mark.jsm
@pytest.mark.unit
class TestCreateAsset:
    """Test asset creation functionality."""

    def test_create_asset_minimal(self, mock_jira_client, sample_asset):
        """Test creating asset with required fields."""
        mock_jira_client.has_assets_license.return_value = True
        mock_jira_client.create_asset.return_value = sample_asset

        attributes = {"IP Address": "192.168.1.105", "Status": "Active"}

        with patch('create_asset.get_jira_client', return_value=mock_jira_client):
            result = create_asset.create_asset(5, attributes)

        assert result['id'] == "10001"
        mock_jira_client.create_asset.assert_called_once_with(5, attributes)

    def test_create_asset_dry_run(self, mock_jira_client):
        """Test dry-run mode doesn't create asset."""
        mock_jira_client.has_assets_license.return_value = True

        attributes = {"IP Address": "192.168.1.105"}

        with patch('create_asset.get_jira_client', return_value=mock_jira_client):
            result = create_asset.create_asset(5, attributes, dry_run=True)

        assert result is None
        mock_jira_client.create_asset.assert_not_called()

    def test_create_asset_no_license(self, mock_jira_client):
        """Test error when Assets license not available."""
        mock_jira_client.has_assets_license.return_value = False

        with patch('create_asset.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(SystemExit):
                create_asset.create_asset(5, {"IP Address": "192.168.1.105"})

    def test_parse_attributes(self):
        """Test parsing attribute list."""
        attr_list = ["IP Address=192.168.1.105", "Status=Active", "Location=DC-1"]
        result = create_asset.parse_attributes(attr_list)

        assert result == {
            "IP Address": "192.168.1.105",
            "Status": "Active",
            "Location": "DC-1"
        }

    def test_parse_attributes_invalid(self):
        """Test error with invalid attribute format."""
        with pytest.raises(ValueError, match="Invalid attribute format"):
            create_asset.parse_attributes(["InvalidFormat"])

    def test_create_asset_error(self, mock_jira_client):
        """Test error when creation fails."""
        from jira_assistant_skills_lib import JiraError
        mock_jira_client.has_assets_license.return_value = True
        mock_jira_client.create_asset.side_effect = JiraError("Creation failed")

        with patch('create_asset.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(JiraError, match="Creation failed"):
                create_asset.create_asset(5, {"IP Address": "192.168.1.105"})
