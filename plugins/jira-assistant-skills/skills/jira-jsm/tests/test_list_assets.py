"""
Tests for list_assets.py script.

Tests asset listing with IQL filtering.
"""

import pytest
from unittest.mock import patch, Mock
import json
from pathlib import Path
import sys

scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import list_assets


@pytest.mark.jsm
@pytest.mark.unit
class TestListAssets:
    """Test asset listing functionality."""

    def test_list_assets_all(self, mock_jira_client, sample_assets_list):
        """Test listing all assets."""
        mock_jira_client.has_assets_license.return_value = True
        mock_jira_client.list_assets.return_value = sample_assets_list

        with patch('list_assets.get_jira_client', return_value=mock_jira_client):
            results = list_assets.list_assets()

        assert len(results) == 3
        mock_jira_client.list_assets.assert_called_once_with(None, None, 100)

    def test_list_assets_by_type(self, mock_jira_client, sample_assets_list):
        """Test filtering by object type."""
        mock_jira_client.has_assets_license.return_value = True
        filtered = [a for a in sample_assets_list if a['objectType']['name'] == 'Server']
        mock_jira_client.list_assets.return_value = filtered

        with patch('list_assets.get_jira_client', return_value=mock_jira_client):
            results = list_assets.list_assets(object_type="Server")

        assert len(results) == 2
        assert all(a['objectType']['name'] == 'Server' for a in results)

    def test_list_assets_with_iql(self, mock_jira_client, sample_assets_list):
        """Test filtering with IQL query."""
        mock_jira_client.has_assets_license.return_value = True
        mock_jira_client.list_assets.return_value = sample_assets_list

        with patch('list_assets.get_jira_client', return_value=mock_jira_client):
            results = list_assets.list_assets(iql='Status="Active"')

        mock_jira_client.list_assets.assert_called_once_with(None, 'Status="Active"', 100)

    def test_list_assets_no_license(self, mock_jira_client):
        """Test error when Assets license not available."""
        mock_jira_client.has_assets_license.return_value = False

        with patch('list_assets.get_jira_client', return_value=mock_jira_client):
            with pytest.raises(SystemExit):
                list_assets.list_assets()

    def test_format_text(self, sample_assets_list):
        """Test table output format."""
        output = list_assets.format_text(sample_assets_list)

        assert "Assets (3 total)" in output
        assert "ASSET-123" in output
        assert "web-server-01" in output

    def test_format_text_no_results(self):
        """Test text format with no results."""
        output = list_assets.format_text([])

        assert "No assets found" in output

    def test_format_json(self, sample_assets_list):
        """Test JSON output format."""
        output = list_assets.format_json(sample_assets_list)

        data = json.loads(output)
        assert len(data) == 3
        assert data[0]['objectKey'] == "ASSET-123"
