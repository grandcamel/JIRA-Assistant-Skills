"""
Tests for create_version.py - Create a project version.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestCreateVersion:
    """Tests for creating project versions."""

    @patch('create_version.get_jira_client')
    def test_create_basic_version(self, mock_get_client, mock_jira_client, sample_version):
        """Test creating a basic version with name only."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.create_version.return_value = sample_version

        from create_version import create_version

        result = create_version(
            project='PROJ',
            name='v1.0.0',
            profile=None
        )

        assert result['name'] == 'v1.0.0'
        assert result['project'] == 'PROJ'
        mock_jira_client.create_version.assert_called_once()

    @patch('create_version.get_jira_client')
    def test_create_version_with_description(self, mock_get_client, mock_jira_client):
        """Test creating version with description."""
        mock_get_client.return_value = mock_jira_client
        version_with_desc = {
            'id': '10001',
            'name': 'v1.1.0',
            'description': 'Bug fix release',
            'project': 'PROJ',
            'released': False,
            'archived': False
        }
        mock_jira_client.create_version.return_value = version_with_desc

        from create_version import create_version

        result = create_version(
            project='PROJ',
            name='v1.1.0',
            description='Bug fix release',
            profile=None
        )

        assert result['description'] == 'Bug fix release'

    @patch('create_version.get_jira_client')
    def test_create_version_with_dates(self, mock_get_client, mock_jira_client):
        """Test creating version with start and release dates."""
        mock_get_client.return_value = mock_jira_client
        version_with_dates = {
            'id': '10002',
            'name': 'v2.0.0',
            'project': 'PROJ',
            'startDate': '2025-02-01',
            'releaseDate': '2025-03-01',
            'released': False,
            'archived': False
        }
        mock_jira_client.create_version.return_value = version_with_dates

        from create_version import create_version

        result = create_version(
            project='PROJ',
            name='v2.0.0',
            start_date='2025-02-01',
            release_date='2025-03-01',
            profile=None
        )

        assert result['startDate'] == '2025-02-01'
        assert result['releaseDate'] == '2025-03-01'

    @patch('create_version.get_jira_client')
    def test_create_released_version(self, mock_get_client, mock_jira_client):
        """Test creating version that is already released."""
        mock_get_client.return_value = mock_jira_client
        released_version = {
            'id': '10003',
            'name': 'v0.9.0',
            'project': 'PROJ',
            'released': True,
            'releaseDate': '2025-01-15',
            'archived': False
        }
        mock_jira_client.create_version.return_value = released_version

        from create_version import create_version

        result = create_version(
            project='PROJ',
            name='v0.9.0',
            released=True,
            release_date='2025-01-15',
            profile=None
        )

        assert result['released'] is True

    @patch('create_version.get_jira_client')
    def test_create_archived_version(self, mock_get_client, mock_jira_client):
        """Test creating archived version."""
        mock_get_client.return_value = mock_jira_client
        archived_version = {
            'id': '10004',
            'name': 'v0.8.0',
            'project': 'PROJ',
            'released': True,
            'archived': True
        }
        mock_jira_client.create_version.return_value = archived_version

        from create_version import create_version

        result = create_version(
            project='PROJ',
            name='v0.8.0',
            archived=True,
            profile=None
        )

        assert result['archived'] is True

    @patch('create_version.get_jira_client')
    def test_create_version_dry_run(self, mock_get_client, mock_jira_client):
        """Test dry-run mode shows what would be created."""
        mock_get_client.return_value = mock_jira_client

        from create_version import create_version_dry_run

        result = create_version_dry_run(
            project='PROJ',
            name='v3.0.0',
            description='Major release',
            start_date='2025-04-01',
            release_date='2025-06-01',
            released=False,
            archived=False
        )

        # Dry run should return data without calling API
        assert result['project'] == 'PROJ'
        assert result['name'] == 'v3.0.0'
        assert result['description'] == 'Major release'
        mock_jira_client.create_version.assert_not_called()
