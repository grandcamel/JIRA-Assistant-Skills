"""
Tests for find_affected_assets.py script.

Tests asset discovery for impact analysis.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import find_affected_assets


@pytest.mark.jsm
@pytest.mark.unit
class TestFindAffectedAssets:
    """Test affected asset discovery functionality."""

    def test_find_assets_by_location(self, mock_jira_client, sample_assets_list):
        """Test finding assets in same location."""
        mock_jira_client.has_assets_license.return_value = True
        dc1_assets = [
            a
            for a in sample_assets_list
            if any(
                attr.get("objectTypeAttribute", {}).get("name") == "Location"
                and attr.get("objectAttributeValues", [{}])[0].get("value") == "DC-1"
                for attr in a.get("attributes", [])
            )
        ]
        mock_jira_client.find_assets_by_criteria.return_value = dc1_assets

        with patch(
            "find_affected_assets.get_jira_client", return_value=mock_jira_client
        ):
            find_affected_assets.find_affected_assets('Location="DC-1"')

        mock_jira_client.find_assets_by_criteria.assert_called_once_with(
            'Location="DC-1"'
        )

    def test_find_assets_by_type_and_status(self, mock_jira_client, sample_assets_list):
        """Test finding assets by multiple criteria."""
        mock_jira_client.has_assets_license.return_value = True
        filtered = [
            a for a in sample_assets_list if a["objectType"]["name"] == "Server"
        ]
        mock_jira_client.find_assets_by_criteria.return_value = filtered

        with patch(
            "find_affected_assets.get_jira_client", return_value=mock_jira_client
        ):
            results = find_affected_assets.find_affected_assets(
                'objectType="Server" AND Status="Active"'
            )

        assert len(results) == 2

    def test_find_assets_no_matches(self, mock_jira_client):
        """Test when no affected assets found."""
        mock_jira_client.has_assets_license.return_value = True
        mock_jira_client.find_assets_by_criteria.return_value = []

        with patch(
            "find_affected_assets.get_jira_client", return_value=mock_jira_client
        ):
            results = find_affected_assets.find_affected_assets(
                'Location="NonExistent"'
            )

        assert len(results) == 0

    def test_find_assets_no_license(self, mock_jira_client):
        """Test error when Assets license not available."""
        mock_jira_client.has_assets_license.return_value = False

        with (
            patch(
                "find_affected_assets.get_jira_client", return_value=mock_jira_client
            ),
            pytest.raises(SystemExit),
        ):
            find_affected_assets.find_affected_assets('Location="DC-1"')

    def test_format_text(self, sample_assets_list):
        """Test human-readable output format."""
        output = find_affected_assets.format_text(sample_assets_list, 'Location="DC-1"')

        assert "Affected Assets (3 found)" in output
        assert 'Location="DC-1"' in output

    def test_format_json(self, sample_assets_list):
        """Test JSON output format."""
        output = find_affected_assets.format_json(sample_assets_list)

        data = json.loads(output)
        assert len(data) == 3
