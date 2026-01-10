"""
Root conftest.py for all JIRA Assistant skill tests.

Provides shared fixtures available to all skill tests. Individual skill
conftest.py files can define additional skill-specific fixtures, but should
NOT redefine these base fixtures.

Shared fixtures:
- mock_jira_client: Fully-mocked JiraClient for unit tests
- sample_issue: Sample JIRA issue with common fields
- sample_issue_minimal: Minimal issue for simple tests
- sample_issues: List of 3 sample issues
- sample_transitions: List of workflow transitions
- sample_project: Sample project data
"""

from copy import deepcopy
from unittest.mock import MagicMock, Mock

import pytest


# =============================================================================
# Mock JIRA Client Fixtures
# =============================================================================


@pytest.fixture
def mock_jira_client():
    """
    Mock JiraClient for testing without API calls.

    Provides a fully-mocked client with common methods stubbed out.
    Use this as the base for most unit tests.
    """
    client = MagicMock()
    client.base_url = "https://test.atlassian.net"
    client.email = "test@example.com"
    client.close = Mock()
    client.get_current_user_id = Mock(return_value="557058:test-user-id")

    # Common API methods
    client.search_issues = MagicMock()
    client.get_issue = MagicMock()
    client.create_issue = MagicMock()
    client.update_issue = MagicMock()
    client.delete_issue = MagicMock()
    client.assign_issue = MagicMock()
    client.get_transitions = MagicMock()
    client.transition_issue = MagicMock()

    # Context manager support
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)

    return client


# =============================================================================
# Sample Issue Fixtures
# =============================================================================


@pytest.fixture
def sample_issue():
    """Sample JIRA issue with common fields populated."""
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
                        ],
                    }
                ],
            },
            "issuetype": {"id": "10001", "name": "Bug", "subtask": False},
            "status": {
                "id": "1",
                "name": "Open",
                "statusCategory": {"id": 2, "key": "new", "name": "To Do"},
            },
            "priority": {"id": "3", "name": "Medium"},
            "assignee": {
                "accountId": "557058:test-user-id",
                "displayName": "Test User",
                "emailAddress": "test@example.com",
                "active": True,
            },
            "reporter": {
                "accountId": "557058:reporter-id",
                "displayName": "Reporter User",
                "emailAddress": "reporter@example.com",
                "active": True,
            },
            "project": {"id": "10000", "key": "PROJ", "name": "Test Project"},
            "labels": ["bug", "urgent"],
            "components": [
                {"id": "10100", "name": "Backend"},
                {"id": "10101", "name": "API"},
            ],
            "created": "2025-01-15T10:30:00.000+0000",
            "updated": "2025-01-20T14:45:00.000+0000",
        },
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
            "issuetype": {"id": "10002", "name": "Task", "subtask": False},
            "status": {"id": "1", "name": "Open"},
            "project": {"id": "10000", "key": "PROJ", "name": "Test Project"},
        },
    }


@pytest.fixture
def sample_issues():
    """List of sample issues for bulk operation testing."""
    return [
        {
            "key": "PROJ-1",
            "id": "10001",
            "fields": {
                "summary": "First issue",
                "status": {"name": "To Do", "id": "1"},
                "priority": {"name": "Medium", "id": "3"},
                "issuetype": {"name": "Task", "id": "10001"},
                "assignee": None,
                "project": {"key": "PROJ", "id": "10000"},
                "labels": [],
            },
        },
        {
            "key": "PROJ-2",
            "id": "10002",
            "fields": {
                "summary": "Second issue",
                "status": {"name": "In Progress", "id": "2"},
                "priority": {"name": "High", "id": "2"},
                "issuetype": {"name": "Bug", "id": "10002"},
                "assignee": {"accountId": "user-123", "displayName": "John Doe"},
                "project": {"key": "PROJ", "id": "10000"},
                "labels": ["bug"],
            },
        },
        {
            "key": "PROJ-3",
            "id": "10003",
            "fields": {
                "summary": "Third issue",
                "status": {"name": "To Do", "id": "1"},
                "priority": {"name": "Low", "id": "4"},
                "issuetype": {"name": "Task", "id": "10001"},
                "assignee": {"accountId": "user-456", "displayName": "Jane Smith"},
                "project": {"key": "PROJ", "id": "10000"},
                "labels": ["feature"],
            },
        },
    ]


# =============================================================================
# Sample Project Fixtures
# =============================================================================


@pytest.fixture
def sample_project():
    """Sample JIRA project."""
    return {
        "id": "10000",
        "key": "PROJ",
        "name": "Test Project",
        "self": "https://test.atlassian.net/rest/api/3/project/10000",
        "projectTypeKey": "software",
        "lead": {
            "accountId": "557058:lead-id",
            "displayName": "Project Lead",
        },
    }


# =============================================================================
# Workflow Fixtures
# =============================================================================


@pytest.fixture
def sample_transitions():
    """Sample workflow transitions."""
    return [
        {"id": "21", "name": "In Progress", "to": {"name": "In Progress", "id": "3"}},
        {"id": "31", "name": "Done", "to": {"name": "Done", "id": "4"}},
        {"id": "41", "name": "In Review", "to": {"name": "In Review", "id": "5"}},
    ]
