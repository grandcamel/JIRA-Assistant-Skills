"""
Shared pytest fixtures for jira-agile skill tests.

Provides mock JIRA API responses and client fixtures for testing
Agile/Scrum functionality without hitting real JIRA instance.
"""

import pytest
from unittest.mock import Mock, MagicMock
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
def sample_epic_response():
    """Sample JIRA API response for an epic issue."""
    return {
        "id": "10100",
        "key": "PROJ-100",
        "self": "https://test.atlassian.net/rest/api/3/issue/10100",
        "fields": {
            "summary": "Mobile App MVP",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": "Epic description"}
                        ]
                    }
                ]
            },
            "issuetype": {
                "id": "10000",
                "name": "Epic",
                "subtask": False
            },
            "project": {
                "key": "PROJ",
                "name": "Test Project"
            },
            "status": {
                "name": "In Progress",
                "statusCategory": {"key": "indeterminate"}
            },
            "priority": {
                "name": "Medium"
            },
            "assignee": None,
            "customfield_10011": "MVP",  # Epic Name
            "customfield_10012": "blue"  # Epic Color
        }
    }


@pytest.fixture
def sample_sprint_response():
    """Sample JIRA Agile API response for a sprint."""
    return {
        "id": 456,
        "self": "https://test.atlassian.net/rest/agile/1.0/sprint/456",
        "state": "active",
        "name": "Sprint 42",
        "startDate": "2025-01-20T00:00:00.000Z",
        "endDate": "2025-02-03T00:00:00.000Z",
        "originBoardId": 123,
        "goal": "Launch MVP"
    }


@pytest.fixture
def sample_board_response():
    """Sample JIRA Agile API response for a board."""
    return {
        "id": 123,
        "self": "https://test.atlassian.net/rest/agile/1.0/board/123",
        "name": "PROJ Scrum Board",
        "type": "scrum",
        "location": {
            "projectKey": "PROJ",
            "projectName": "Test Project"
        }
    }


@pytest.fixture
def sample_issue_response():
    """Sample JIRA API response for a standard issue."""
    return {
        "id": "10101",
        "key": "PROJ-101",
        "self": "https://test.atlassian.net/rest/api/3/issue/10101",
        "fields": {
            "summary": "User authentication",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": "Implement auth"}
                        ]
                    }
                ]
            },
            "issuetype": {
                "id": "10001",
                "name": "Story",
                "subtask": False
            },
            "project": {
                "key": "PROJ",
                "name": "Test Project"
            },
            "status": {
                "name": "To Do"
            },
            "priority": {
                "name": "High"
            },
            "assignee": {
                "accountId": "557058:test-user-id",
                "displayName": "Test User"
            },
            "customfield_10016": 5,  # Story Points
            "customfield_10014": 456  # Sprint ID
        }
    }


@pytest.fixture
def sample_subtask_response():
    """Sample JIRA API response for a subtask."""
    return {
        "id": "10102",
        "key": "PROJ-102",
        "self": "https://test.atlassian.net/rest/api/3/issue/10102",
        "fields": {
            "summary": "Implement login API",
            "issuetype": {
                "id": "10003",
                "name": "Sub-task",
                "subtask": True
            },
            "parent": {
                "id": "10101",
                "key": "PROJ-101"
            },
            "project": {
                "key": "PROJ"
            },
            "status": {
                "name": "In Progress"
            }
        }
    }


@pytest.fixture
def mock_config_manager(mock_jira_client):
    """Mock config_manager.get_jira_client() to return mock client."""
    def _get_jira_client(profile=None):
        return mock_jira_client
    return _get_jira_client
