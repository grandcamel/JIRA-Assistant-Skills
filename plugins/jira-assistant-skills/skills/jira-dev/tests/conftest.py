"""
Pytest configuration and shared fixtures for jira-dev tests.

Note: Common markers (unit, integration, dev) are defined in the root pytest.ini.
"""

import copy
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add lib path for imports
lib_path = Path(__file__).parent.parent.parent / "shared" / "scripts" / "lib"
sys.path.insert(0, str(lib_path))

# Add scripts path for imports
scripts_path = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))


@pytest.fixture
def mock_jira_client():
    """Create a mock JIRA client."""
    client = Mock()
    client.close = Mock()
    return client


@pytest.fixture
def sample_issue():
    """Sample JIRA issue data."""
    _sample_issue = {
        "key": "PROJ-123",
        "id": "10001",
        "self": "https://company.atlassian.net/rest/api/3/issue/10001",
        "fields": {
            "summary": "Fix login button not responding",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "The login button does not respond on mobile.",
                            }
                        ],
                    }
                ],
            },
            "issuetype": {"id": "10001", "name": "Bug", "subtask": False},
            "status": {"id": "10000", "name": "To Do"},
            "priority": {"id": "3", "name": "Medium"},
            "assignee": {
                "accountId": "123456",
                "displayName": "John Doe",
                "emailAddress": "john@example.com",
            },
            "reporter": {
                "accountId": "789012",
                "displayName": "Jane Smith",
                "emailAddress": "jane@example.com",
            },
            "created": "2025-01-15T10:30:00.000+0000",
            "updated": "2025-01-15T14:45:00.000+0000",
            "labels": ["mobile", "ui"],
            "components": [{"id": "10000", "name": "Frontend"}],
        },
    }
    return copy.deepcopy(_sample_issue)


@pytest.fixture
def sample_story_issue():
    """Sample JIRA story issue data."""
    return {
        "key": "PROJ-456",
        "id": "10002",
        "fields": {
            "summary": "Implement user preferences page",
            "issuetype": {"id": "10002", "name": "Story", "subtask": False},
            "status": {"id": "10000", "name": "To Do"},
        },
    }


@pytest.fixture
def sample_task_issue():
    """Sample JIRA task issue data."""
    return {
        "key": "PROJ-789",
        "id": "10003",
        "fields": {
            "summary": "Update documentation",
            "issuetype": {"id": "10003", "name": "Task", "subtask": False},
            "status": {"id": "10000", "name": "To Do"},
        },
    }


@pytest.fixture
def sample_dev_info():
    """Sample development information from JIRA."""
    _sample_dev_info = {
        "detail": [
            {
                "repositories": [
                    {
                        "name": "org/repo",
                        "url": "https://github.com/org/repo",
                        "commits": [
                            {
                                "id": "abc123def456",
                                "displayId": "abc123d",
                                "message": "PROJ-123: Fix login button",
                                "author": {
                                    "name": "John Doe",
                                    "email": "john@example.com",
                                },
                                "authorTimestamp": "2025-01-15T15:30:00.000Z",
                                "url": "https://github.com/org/repo/commit/abc123def456",
                            },
                            {
                                "id": "def456ghi789",
                                "displayId": "def456g",
                                "message": "PROJ-123: Add unit tests",
                                "author": {
                                    "name": "John Doe",
                                    "email": "john@example.com",
                                },
                                "authorTimestamp": "2025-01-15T16:00:00.000Z",
                                "url": "https://github.com/org/repo/commit/def456ghi789",
                            },
                        ],
                    }
                ]
            }
        ]
    }
    return copy.deepcopy(_sample_dev_info)


@pytest.fixture
def mock_config_manager():
    """Mock ConfigManager for tests."""
    with patch("config_manager.ConfigManager") as mock_cm:
        mock_instance = MagicMock()
        mock_cm.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_jira_client(mock_jira_client):
    """Mock get_jira_client function."""
    with patch("config_manager.get_jira_client") as mock_get:
        mock_get.return_value = mock_jira_client
        yield mock_get
