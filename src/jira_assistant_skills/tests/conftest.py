"""
Root conftest.py for jira-as CLI tests.

Provides shared fixtures for all CLI command tests.

Fixtures:
- mock_jira_client: Fully-mocked JiraClient for unit tests
- sample_issue: Sample JIRA issue with common fields
- sample_issue_minimal: Minimal issue for simple tests
- sample_issues: List of 3 sample issues
- sample_transitions: List of workflow transitions
- sample_project: Sample project data
- cli_runner: Click test runner
"""

from unittest.mock import MagicMock, Mock

import pytest
from click.testing import CliRunner

# =============================================================================
# Click Test Runner
# =============================================================================


@pytest.fixture
def cli_runner():
    """Click test runner for CLI command testing."""
    return CliRunner()


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


# =============================================================================
# Issue-Specific Fixtures
# =============================================================================


@pytest.fixture
def sample_issue_with_time_tracking():
    """Sample JIRA issue with time tracking information."""
    return {
        "id": "10003",
        "key": "PROJ-125",
        "self": "https://test.atlassian.net/rest/api/3/issue/10003",
        "fields": {
            "summary": "Issue with Time Tracking",
            "issuetype": {"id": "10001", "name": "Bug", "subtask": False},
            "status": {"id": "1", "name": "Open"},
            "project": {"id": "10000", "key": "PROJ", "name": "Test Project"},
            "timetracking": {
                "originalEstimate": "2d",
                "remainingEstimate": "1d 4h",
                "timeSpent": "4h",
                "originalEstimateSeconds": 57600,
                "remainingEstimateSeconds": 36000,
                "timeSpentSeconds": 14400,
            },
        },
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
            "issuetype": {"id": "10001", "name": "Bug", "subtask": False},
            "status": {"id": "1", "name": "Open"},
            "project": {"id": "10000", "key": "PROJ", "name": "Test Project"},
            "issuelinks": [
                {
                    "id": "10200",
                    "type": {
                        "id": "10000",
                        "name": "Blocks",
                        "inward": "is blocked by",
                        "outward": "blocks",
                    },
                    "outwardIssue": {
                        "id": "10005",
                        "key": "PROJ-127",
                        "fields": {
                            "summary": "Blocked Issue",
                            "status": {"name": "Open"},
                        },
                    },
                },
                {
                    "id": "10201",
                    "type": {
                        "id": "10001",
                        "name": "Relates",
                        "inward": "relates to",
                        "outward": "relates to",
                    },
                    "inwardIssue": {
                        "id": "10006",
                        "key": "PROJ-128",
                        "fields": {
                            "summary": "Related Issue",
                            "status": {"name": "In Progress"},
                        },
                    },
                },
            ],
        },
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
            "issuetype": {"id": "10003", "name": "Story", "subtask": False},
            "status": {"id": "1", "name": "Open"},
            "project": {"id": "10000", "key": "PROJ", "name": "Test Project"},
            "customfield_10014": "PROJ-100",  # Epic Link
            "customfield_10016": 5.0,  # Story Points
        },
    }


@pytest.fixture
def sample_created_issue():
    """Sample response from creating an issue."""
    return {
        "id": "10010",
        "key": "PROJ-130",
        "self": "https://test.atlassian.net/rest/api/3/issue/10010",
    }


@pytest.fixture
def sample_transitions_with_done():
    """Sample workflow transitions including Done transition."""
    return [
        {"id": "21", "name": "In Progress", "to": {"name": "In Progress", "id": "3"}},
        {"id": "31", "name": "Done", "to": {"name": "Done", "id": "4"}},
        {"id": "41", "name": "In Review", "to": {"name": "In Review", "id": "5"}},
    ]


# =============================================================================
# Version Fixtures
# =============================================================================


@pytest.fixture
def sample_versions():
    """Sample project versions."""
    return [
        {
            "id": "10001",
            "name": "v1.0.0",
            "description": "First release",
            "released": True,
            "archived": False,
            "releaseDate": "2025-01-01",
        },
        {
            "id": "10002",
            "name": "v1.1.0",
            "description": "Minor release",
            "released": False,
            "archived": False,
        },
        {
            "id": "10003",
            "name": "v0.9.0",
            "description": "Beta release",
            "released": True,
            "archived": True,
            "releaseDate": "2024-12-01",
        },
    ]


@pytest.fixture
def sample_created_version():
    """Sample response from creating a version."""
    return {
        "id": "10004",
        "name": "v1.0.0",
        "self": "https://test.atlassian.net/rest/api/3/version/10004",
        "released": False,
        "archived": False,
    }


# =============================================================================
# Component Fixtures
# =============================================================================


@pytest.fixture
def sample_components():
    """Sample project components."""
    return [
        {
            "id": "10100",
            "name": "Backend",
            "description": "Backend services",
            "lead": {"accountId": "user-123", "displayName": "John Doe"},
            "assigneeType": "PROJECT_LEAD",
        },
        {
            "id": "10101",
            "name": "Frontend",
            "description": "UI components",
            "lead": {"accountId": "user-456", "displayName": "Jane Smith"},
            "assigneeType": "COMPONENT_LEAD",
        },
    ]


@pytest.fixture
def sample_created_component():
    """Sample response from creating a component."""
    return {
        "id": "10102",
        "name": "Backend",
        "self": "https://test.atlassian.net/rest/api/3/component/10102",
    }


# =============================================================================
# Comment Fixtures
# =============================================================================


@pytest.fixture
def sample_comment():
    """Sample comment."""
    return {
        "id": "10001",
        "self": "https://test.atlassian.net/rest/api/3/issue/PROJ-123/comment/10001",
        "author": {
            "accountId": "user-123",
            "displayName": "John Doe",
            "emailAddress": "john@example.com",
        },
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Test comment body"}],
                }
            ],
        },
        "created": "2025-01-15T10:30:00.000+0000",
        "updated": "2025-01-15T10:30:00.000+0000",
    }


@pytest.fixture
def sample_comments_response():
    """Sample response from get_comments API."""
    return {
        "startAt": 0,
        "maxResults": 50,
        "total": 2,
        "comments": [
            {
                "id": "10001",
                "author": {"accountId": "user-123", "displayName": "John Doe"},
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "First comment"}],
                        }
                    ],
                },
                "created": "2025-01-15T10:30:00.000+0000",
            },
            {
                "id": "10002",
                "author": {"accountId": "user-456", "displayName": "Jane Smith"},
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Second comment"}],
                        }
                    ],
                },
                "created": "2025-01-16T14:00:00.000+0000",
            },
        ],
    }


# =============================================================================
# Attachment Fixtures
# =============================================================================


@pytest.fixture
def sample_attachments():
    """Sample attachments."""
    return [
        {
            "id": "10001",
            "filename": "screenshot.png",
            "size": 102400,
            "mimeType": "image/png",
            "created": "2025-01-15T10:30:00.000+0000",
            "author": {"accountId": "user-123", "displayName": "John Doe"},
            "content": "https://test.atlassian.net/secure/attachment/10001/screenshot.png",
        },
        {
            "id": "10002",
            "filename": "document.pdf",
            "size": 2048000,
            "mimeType": "application/pdf",
            "created": "2025-01-16T14:00:00.000+0000",
            "author": {"accountId": "user-456", "displayName": "Jane Smith"},
            "content": "https://test.atlassian.net/secure/attachment/10002/document.pdf",
        },
    ]


# =============================================================================
# Watcher Fixtures
# =============================================================================


@pytest.fixture
def sample_watchers():
    """Sample watchers."""
    return [
        {
            "accountId": "user-123",
            "displayName": "John Doe",
            "emailAddress": "john@example.com",
        },
        {
            "accountId": "user-456",
            "displayName": "Jane Smith",
            "emailAddress": "jane@example.com",
        },
    ]


# =============================================================================
# Changelog Fixtures
# =============================================================================


@pytest.fixture
def sample_changelog():
    """Sample changelog/activity."""
    return {
        "startAt": 0,
        "maxResults": 100,
        "total": 2,
        "values": [
            {
                "id": "1001",
                "author": {"accountId": "user-123", "displayName": "John Doe"},
                "created": "2025-01-15T10:30:00.000+0000",
                "items": [
                    {
                        "field": "status",
                        "fieldtype": "jira",
                        "from": "10001",
                        "fromString": "To Do",
                        "to": "10002",
                        "toString": "In Progress",
                    }
                ],
            },
            {
                "id": "1002",
                "author": {"accountId": "user-456", "displayName": "Jane Smith"},
                "created": "2025-01-16T14:00:00.000+0000",
                "items": [
                    {
                        "field": "assignee",
                        "fieldtype": "jira",
                        "from": None,
                        "fromString": None,
                        "to": "user-789",
                        "toString": "Bob Wilson",
                    }
                ],
            },
        ],
    }


# =============================================================================
# Issue Link Fixtures
# =============================================================================


@pytest.fixture
def sample_link_types():
    """Sample link types."""
    return [
        {
            "id": "10000",
            "name": "Blocks",
            "inward": "is blocked by",
            "outward": "blocks",
        },
        {
            "id": "10001",
            "name": "Relates",
            "inward": "relates to",
            "outward": "relates to",
        },
        {
            "id": "10002",
            "name": "Duplicate",
            "inward": "is duplicated by",
            "outward": "duplicates",
        },
        {
            "id": "10003",
            "name": "Cloners",
            "inward": "is cloned by",
            "outward": "clones",
        },
    ]


@pytest.fixture
def sample_issue_links():
    """Sample issue links."""
    return [
        {
            "id": "10200",
            "type": {
                "id": "10000",
                "name": "Blocks",
                "inward": "is blocked by",
                "outward": "blocks",
            },
            "outwardIssue": {
                "id": "10005",
                "key": "PROJ-127",
                "fields": {
                    "summary": "Blocked Issue",
                    "status": {"name": "Open"},
                },
            },
        },
        {
            "id": "10201",
            "type": {
                "id": "10001",
                "name": "Relates",
                "inward": "relates to",
                "outward": "relates to",
            },
            "inwardIssue": {
                "id": "10006",
                "key": "PROJ-128",
                "fields": {
                    "summary": "Related Issue",
                    "status": {"name": "In Progress"},
                },
            },
        },
    ]


@pytest.fixture
def sample_blocker_links():
    """Sample blocker links (issue is blocked by others)."""
    return [
        {
            "id": "10300",
            "type": {
                "id": "10000",
                "name": "Blocks",
                "inward": "is blocked by",
                "outward": "blocks",
            },
            "outwardIssue": {
                "id": "10010",
                "key": "PROJ-200",
                "fields": {
                    "summary": "Blocker Issue 1",
                    "status": {"name": "Open"},
                },
            },
        },
        {
            "id": "10301",
            "type": {
                "id": "10000",
                "name": "Blocks",
                "inward": "is blocked by",
                "outward": "blocks",
            },
            "outwardIssue": {
                "id": "10011",
                "key": "PROJ-201",
                "fields": {
                    "summary": "Blocker Issue 2",
                    "status": {"name": "Done"},
                },
            },
        },
    ]


@pytest.fixture
def sample_cloned_issue():
    """Sample response from cloning an issue."""
    return {
        "id": "10020",
        "key": "PROJ-300",
        "self": "https://test.atlassian.net/rest/api/3/issue/10020",
    }


# =============================================================================
# Field Fixtures
# =============================================================================


@pytest.fixture
def sample_fields():
    """Sample custom fields."""
    return [
        {
            "id": "customfield_10001",
            "name": "Story Points",
            "custom": True,
            "searchable": True,
            "navigable": True,
            "schema": {"type": "number"},
        },
        {
            "id": "customfield_10002",
            "name": "Epic Link",
            "custom": True,
            "searchable": True,
            "navigable": True,
            "schema": {"type": "string"},
        },
        {
            "id": "customfield_10003",
            "name": "Sprint",
            "custom": True,
            "searchable": True,
            "navigable": True,
            "schema": {"type": "array"},
        },
        {
            "id": "customfield_10004",
            "name": "Team",
            "custom": True,
            "searchable": True,
            "navigable": True,
            "schema": {"type": "string"},
        },
        {
            "id": "summary",
            "name": "Summary",
            "custom": False,
            "searchable": True,
            "navigable": True,
            "schema": {"type": "string"},
        },
    ]


@pytest.fixture
def sample_created_field():
    """Sample response from creating a field."""
    return {
        "id": "customfield_10005",
        "name": "Custom Text Field",
        "schema": {
            "type": "string",
            "custom": "com.atlassian.jira.plugin.system.customfieldtypes:textfield",
        },
    }


@pytest.fixture
def sample_project_meta():
    """Sample project metadata with fields."""
    return {
        "projects": [
            {
                "id": "10000",
                "key": "PROJ",
                "name": "Test Project",
                "issuetypes": [
                    {
                        "id": "10001",
                        "name": "Task",
                        "fields": {
                            "summary": {"name": "Summary", "required": True},
                            "description": {"name": "Description", "required": False},
                            "customfield_10001": {
                                "name": "Story Points",
                                "required": False,
                            },
                            "customfield_10002": {
                                "name": "Epic Link",
                                "required": False,
                            },
                        },
                    },
                    {
                        "id": "10002",
                        "name": "Bug",
                        "fields": {
                            "summary": {"name": "Summary", "required": True},
                            "description": {"name": "Description", "required": False},
                            "priority": {"name": "Priority", "required": True},
                        },
                    },
                ],
            }
        ]
    }


@pytest.fixture
def sample_project_classic():
    """Sample company-managed (classic) project."""
    return {
        "id": "10000",
        "key": "PROJ",
        "name": "Test Project",
        "projectTypeKey": "software",
        "style": "classic",
        "simplified": False,
    }


@pytest.fixture
def sample_project_nextgen():
    """Sample team-managed (next-gen) project."""
    return {
        "id": "10001",
        "key": "TEAM",
        "name": "Team Project",
        "projectTypeKey": "software",
        "style": "next-gen",
        "simplified": True,
    }


@pytest.fixture
def sample_screens():
    """Sample screens."""
    return {
        "values": [
            {"id": 1, "name": "Default Screen"},
            {"id": 2, "name": "Bug Screen"},
        ]
    }


@pytest.fixture
def sample_screen_tabs():
    """Sample screen tabs."""
    return [{"id": 10001, "name": "Field Tab"}]


@pytest.fixture
def sample_screen_fields():
    """Sample screen tab fields."""
    return [
        {"id": "summary", "name": "Summary"},
        {"id": "description", "name": "Description"},
    ]
