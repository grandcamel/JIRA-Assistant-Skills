"""
Shared pytest fixtures for jira-issue skill tests.

Provides mock JIRA API responses and client fixtures for testing
issue CRUD operations.
"""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")


from unittest.mock import Mock, MagicMock
from copy import deepcopy
import sys
from pathlib import Path

# Add paths to sys.path before any imports that depend on them
_this_dir = Path(__file__).parent
_shared_lib_path = str(_this_dir.parent.parent / 'shared' / 'scripts' / 'lib')
_scripts_path = str(_this_dir.parent / 'scripts')

# Insert at beginning to ensure our paths take precedence
for path in [_shared_lib_path, _scripts_path]:
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture
def mock_jira_client():
    """Mock JiraClient for testing without API calls."""
    client = Mock()
    client.base_url = "https://test.atlassian.net"
    client.email = "test@example.com"
    client.close = Mock()
    client.get_current_user_id = Mock(return_value="557058:test-user-id")
    return client


@pytest.fixture
def sample_issue():
    """Sample JIRA issue for testing."""
    return {
        "id": "10001",
        "key": "PROJ-123",
        "self": "https://test.atlassian.net/rest/api/3/issue/10001",
        "fields": {
            "summary": "Test Issue Summary",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": "This is a test description."}
                        ]
                    }
                ]
            },
            "issuetype": {
                "id": "10001",
                "name": "Bug",
                "subtask": False
            },
            "status": {
                "id": "1",
                "name": "Open",
                "statusCategory": {
                    "id": 2,
                    "key": "new",
                    "name": "To Do"
                }
            },
            "priority": {
                "id": "3",
                "name": "Medium"
            },
            "assignee": {
                "accountId": "557058:test-user-id",
                "displayName": "Test User",
                "emailAddress": "test@example.com",
                "active": True
            },
            "reporter": {
                "accountId": "557058:reporter-id",
                "displayName": "Reporter User",
                "emailAddress": "reporter@example.com",
                "active": True
            },
            "project": {
                "id": "10000",
                "key": "PROJ",
                "name": "Test Project"
            },
            "labels": ["bug", "urgent"],
            "components": [
                {"id": "10100", "name": "Backend"},
                {"id": "10101", "name": "API"}
            ],
            "created": "2025-01-15T10:30:00.000+0000",
            "updated": "2025-01-20T14:45:00.000+0000"
        }
    }


@pytest.fixture
def sample_issue_minimal():
    """Sample JIRA issue with minimal fields."""
    return {
        "id": "10002",
        "key": "PROJ-124",
        "self": "https://test.atlassian.net/rest/api/3/issue/10002",
        "fields": {
            "summary": "Minimal Issue",
            "issuetype": {
                "id": "10002",
                "name": "Task",
                "subtask": False
            },
            "status": {
                "id": "1",
                "name": "Open"
            },
            "project": {
                "id": "10000",
                "key": "PROJ",
                "name": "Test Project"
            }
        }
    }


@pytest.fixture
def sample_issue_with_time_tracking():
    """Sample JIRA issue with time tracking information."""
    return {
        "id": "10003",
        "key": "PROJ-125",
        "self": "https://test.atlassian.net/rest/api/3/issue/10003",
        "fields": {
            "summary": "Issue with Time Tracking",
            "issuetype": {
                "id": "10001",
                "name": "Bug",
                "subtask": False
            },
            "status": {
                "id": "1",
                "name": "Open"
            },
            "project": {
                "id": "10000",
                "key": "PROJ",
                "name": "Test Project"
            },
            "timetracking": {
                "originalEstimate": "2d",
                "remainingEstimate": "1d 4h",
                "timeSpent": "4h",
                "originalEstimateSeconds": 57600,
                "remainingEstimateSeconds": 36000,
                "timeSpentSeconds": 14400
            }
        }
    }


@pytest.fixture
def sample_issue_with_links():
    """Sample JIRA issue with issue links."""
    return {
        "id": "10004",
        "key": "PROJ-126",
        "self": "https://test.atlassian.net/rest/api/3/issue/10004",
        "fields": {
            "summary": "Issue with Links",
            "issuetype": {
                "id": "10001",
                "name": "Bug",
                "subtask": False
            },
            "status": {
                "id": "1",
                "name": "Open"
            },
            "project": {
                "id": "10000",
                "key": "PROJ",
                "name": "Test Project"
            },
            "issuelinks": [
                {
                    "id": "10200",
                    "type": {
                        "id": "10000",
                        "name": "Blocks",
                        "inward": "is blocked by",
                        "outward": "blocks"
                    },
                    "outwardIssue": {
                        "id": "10005",
                        "key": "PROJ-127",
                        "fields": {
                            "summary": "Blocked Issue",
                            "status": {"name": "Open"}
                        }
                    }
                },
                {
                    "id": "10201",
                    "type": {
                        "id": "10001",
                        "name": "Relates",
                        "inward": "relates to",
                        "outward": "relates to"
                    },
                    "inwardIssue": {
                        "id": "10006",
                        "key": "PROJ-128",
                        "fields": {
                            "summary": "Related Issue",
                            "status": {"name": "In Progress"}
                        }
                    }
                }
            ]
        }
    }


@pytest.fixture
def sample_issue_with_agile():
    """Sample JIRA issue with Agile fields (epic, story points)."""
    return {
        "id": "10007",
        "key": "PROJ-129",
        "self": "https://test.atlassian.net/rest/api/3/issue/10007",
        "fields": {
            "summary": "Story with Agile Fields",
            "issuetype": {
                "id": "10003",
                "name": "Story",
                "subtask": False
            },
            "status": {
                "id": "1",
                "name": "Open"
            },
            "project": {
                "id": "10000",
                "key": "PROJ",
                "name": "Test Project"
            },
            "customfield_10014": "PROJ-100",  # Epic Link
            "customfield_10016": 5.0  # Story Points
        }
    }


@pytest.fixture
def sample_created_issue():
    """Sample response from creating an issue."""
    return {
        "id": "10010",
        "key": "PROJ-130",
        "self": "https://test.atlassian.net/rest/api/3/issue/10010"
    }


@pytest.fixture
def sample_created_issue_with_links():
    """Sample response from creating an issue with links."""
    return {
        "id": "10011",
        "key": "PROJ-131",
        "self": "https://test.atlassian.net/rest/api/3/issue/10011",
        "links_created": ["blocks PROJ-123", "relates to PROJ-124"]
    }


@pytest.fixture
def sample_issue_detailed(sample_issue):
    """Sample issue with all detailed fields populated."""
    issue = deepcopy(sample_issue)
    issue["fields"]["subtasks"] = [
        {
            "id": "10020",
            "key": "PROJ-140",
            "fields": {
                "summary": "Subtask 1",
                "status": {"name": "Open"}
            }
        },
        {
            "id": "10021",
            "key": "PROJ-141",
            "fields": {
                "summary": "Subtask 2",
                "status": {"name": "Done"}
            }
        }
    ]
    return issue


@pytest.fixture
def mock_config_manager(mock_jira_client):
    """Mock config_manager.get_jira_client() to return mock client."""
    def _get_jira_client(profile=None):
        return mock_jira_client
    return _get_jira_client
