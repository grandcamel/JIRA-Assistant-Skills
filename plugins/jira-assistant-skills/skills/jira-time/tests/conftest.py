"""
Shared pytest fixtures for jira-time skill tests.

Provides mock JIRA API responses and client fixtures for testing
time tracking operations without hitting real JIRA instance.

Note: Common markers (unit, integration, time) are defined in the root pytest.ini.
"""

import copy
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add shared lib to path so imports work in tests
shared_lib_path = str(
    Path(__file__).parent.parent.parent.parent / "shared" / "scripts" / "lib"
)
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)

# Add scripts to path for importing
scripts_path = str(Path(__file__).parent.parent / "scripts")
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
def sample_worklog():
    """Sample worklog entry returned by JIRA API."""
    return {
        "id": "10045",
        "self": "https://test.atlassian.net/rest/api/3/issue/10123/worklog/10045",
        "author": {
            "accountId": "5b10a2844c20165700ede21g",
            "emailAddress": "alice@company.com",
            "displayName": "Alice Smith",
            "active": True,
        },
        "updateAuthor": {
            "accountId": "5b10a2844c20165700ede21g",
            "emailAddress": "alice@company.com",
            "displayName": "Alice Smith",
            "active": True,
        },
        "created": "2025-01-15T09:30:00.000+0000",
        "updated": "2025-01-15T09:30:00.000+0000",
        "started": "2025-01-15T09:00:00.000+0000",
        "timeSpent": "2h",
        "timeSpentSeconds": 7200,
        "comment": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Debugging authentication issue"}
                    ],
                }
            ],
        },
        "issueId": "10123",
    }


@pytest.fixture
def sample_worklogs(sample_worklog):
    """Sample list of worklogs for an issue."""
    # Use deepcopy to prevent fixture mutation
    worklog_copy = copy.deepcopy(sample_worklog)
    return {
        "startAt": 0,
        "maxResults": 20,
        "total": 3,
        "worklogs": [
            worklog_copy,
            {
                "id": "10046",
                "self": "https://test.atlassian.net/rest/api/3/issue/10123/worklog/10046",
                "author": {
                    "accountId": "5b10a2844c20165700ede22h",
                    "emailAddress": "bob@company.com",
                    "displayName": "Bob Jones",
                    "active": True,
                },
                "updateAuthor": {
                    "accountId": "5b10a2844c20165700ede22h",
                    "emailAddress": "bob@company.com",
                    "displayName": "Bob Jones",
                    "active": True,
                },
                "created": "2025-01-15T14:30:00.000+0000",
                "updated": "2025-01-15T14:30:00.000+0000",
                "started": "2025-01-15T14:00:00.000+0000",
                "timeSpent": "1h 30m",
                "timeSpentSeconds": 5400,
                "comment": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Code review"}],
                        }
                    ],
                },
                "issueId": "10123",
            },
            {
                "id": "10047",
                "self": "https://test.atlassian.net/rest/api/3/issue/10123/worklog/10047",
                "author": {
                    "accountId": "5b10a2844c20165700ede21g",
                    "emailAddress": "alice@company.com",
                    "displayName": "Alice Smith",
                    "active": True,
                },
                "updateAuthor": {
                    "accountId": "5b10a2844c20165700ede21g",
                    "emailAddress": "alice@company.com",
                    "displayName": "Alice Smith",
                    "active": True,
                },
                "created": "2025-01-16T10:30:00.000+0000",
                "updated": "2025-01-16T10:30:00.000+0000",
                "started": "2025-01-16T10:00:00.000+0000",
                "timeSpent": "4h",
                "timeSpentSeconds": 14400,
                "comment": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Implemented fix"}],
                        }
                    ],
                },
                "issueId": "10123",
            },
        ],
    }


@pytest.fixture
def sample_time_tracking():
    """Sample time tracking fields for an issue."""
    return {
        "originalEstimate": "2d",
        "originalEstimateSeconds": 57600,
        "remainingEstimate": "1d 4h",
        "remainingEstimateSeconds": 43200,
        "timeSpent": "4h",
        "timeSpentSeconds": 14400,
    }


@pytest.fixture
def sample_issue_with_time_tracking(sample_time_tracking, sample_worklogs):
    """Sample JIRA issue with time tracking fields."""
    return {
        "id": "10123",
        "key": "PROJ-123",
        "self": "https://test.atlassian.net/rest/api/3/issue/10123",
        "fields": {
            "summary": "Authentication refactor",
            "status": {"name": "In Progress"},
            "issuetype": {"name": "Story"},
            "timetracking": sample_time_tracking,
            "worklog": sample_worklogs,
        },
    }


@pytest.fixture
def sample_issue_no_time_tracking():
    """Sample JIRA issue with no time tracking data."""
    return {
        "id": "10124",
        "key": "PROJ-124",
        "self": "https://test.atlassian.net/rest/api/3/issue/10124",
        "fields": {
            "summary": "Quick fix",
            "status": {"name": "To Do"},
            "issuetype": {"name": "Task"},
            "timetracking": {},
        },
    }


@pytest.fixture
def sample_empty_worklogs():
    """Sample empty worklogs response."""
    return {"startAt": 0, "maxResults": 20, "total": 0, "worklogs": []}


