"""
Shared pytest fixtures for jira-lifecycle skill tests.

Provides mock JIRA API responses and client fixtures for testing
workflow and lifecycle operations without hitting real JIRA instance.
"""

import pytest
from unittest.mock import Mock
import sys
from pathlib import Path

# Add shared lib to path so imports work in tests
shared_lib_path = str(Path(__file__).parent.parent.parent.parent / 'shared' / 'scripts' / 'lib')
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)

# Add scripts to path for importing
scripts_path = str(Path(__file__).parent.parent / 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


@pytest.fixture
def mock_jira_client():
    """Mock JiraClient for testing without API calls."""
    client = Mock()
    client.base_url = "https://test.atlassian.net"
    client.email = "test@example.com"
    client.close = Mock()
    return client


@pytest.fixture
def sample_transitions():
    """Sample transitions available for an issue."""
    return [
        {
            "id": "11",
            "name": "To Do",
            "to": {"name": "To Do", "id": "1"}
        },
        {
            "id": "21",
            "name": "In Progress",
            "to": {"name": "In Progress", "id": "2"}
        },
        {
            "id": "31",
            "name": "Done",
            "to": {"name": "Done", "id": "3"}
        }
    ]


@pytest.fixture
def sample_issue_response():
    """Sample JIRA API response for an issue."""
    return {
        "id": "10101",
        "key": "PROJ-123",
        "self": "https://test.atlassian.net/rest/api/3/issue/10101",
        "fields": {
            "summary": "Test Issue",
            "status": {
                "name": "To Do",
                "id": "1"
            },
            "issuetype": {
                "name": "Story"
            },
            "project": {
                "key": "PROJ"
            }
        }
    }


@pytest.fixture
def mock_config_manager(mock_jira_client):
    """Mock config_manager.get_jira_client() to return mock client."""
    def _get_jira_client(profile=None):
        return mock_jira_client
    return _get_jira_client
