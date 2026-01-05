"""
Pytest fixtures for jira-collaborate comment, notification, and activity tests.

Note: Common markers (unit, integration, collaborate) are defined in the root pytest.ini.
"""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_jira_client():
    """Create a mock JIRA client."""
    client = MagicMock()
    client.base_url = "https://test.atlassian.net"
    return client


@pytest.fixture
def sample_comment():
    """Sample comment response."""
    return {
        "id": "10001",
        "author": {
            "accountId": "5b10a2844c20165700ede21g",
            "displayName": "Alice Smith",
            "emailAddress": "alice@company.com",
        },
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Started investigating the issue..."}
                    ],
                }
            ],
        },
        "updateAuthor": {
            "accountId": "5b10a2844c20165700ede21g",
            "displayName": "Alice Smith",
            "emailAddress": "alice@company.com",
        },
        "created": "2025-01-14T09:00:00.000+0000",
        "updated": "2025-01-14T09:00:00.000+0000",
        "visibility": None,
        "jsdPublic": True,
    }


@pytest.fixture
def sample_comment_with_visibility():
    """Sample comment with role visibility."""
    return {
        "id": "10002",
        "author": {
            "accountId": "5b10a2844c20165700ede21g",
            "displayName": "Bob Jones",
            "emailAddress": "bob@company.com",
        },
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Internal admin note"}],
                }
            ],
        },
        "updateAuthor": {
            "accountId": "5b10a2844c20165700ede21g",
            "displayName": "Bob Jones",
            "emailAddress": "bob@company.com",
        },
        "created": "2025-01-14T10:00:00.000+0000",
        "updated": "2025-01-14T10:00:00.000+0000",
        "visibility": {
            "type": "role",
            "value": "Administrators",
            "identifier": "Administrators",
        },
        "jsdPublic": False,
    }


@pytest.fixture
def sample_comments_list():
    """Sample comments list response."""
    return {
        "startAt": 0,
        "maxResults": 50,
        "total": 3,
        "comments": [
            {
                "id": "10003",
                "author": {
                    "accountId": "5b10a2844c20165700ede21g",
                    "displayName": "Alice Smith",
                    "emailAddress": "alice@company.com",
                },
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Fixed the issue by updating the API endpoint",
                                }
                            ],
                        }
                    ],
                },
                "created": "2025-01-15T10:30:00.000+0000",
                "updated": "2025-01-15T10:30:00.000+0000",
            },
            {
                "id": "10002",
                "author": {
                    "accountId": "5b10a2844c20165700ede22h",
                    "displayName": "Bob Jones",
                    "emailAddress": "bob@company.com",
                },
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "I will take a look at this tomorrow",
                                }
                            ],
                        }
                    ],
                },
                "created": "2025-01-14T15:15:00.000+0000",
                "updated": "2025-01-14T15:15:00.000+0000",
            },
            {
                "id": "10001",
                "author": {
                    "accountId": "5b10a2844c20165700ede21g",
                    "displayName": "Alice Smith",
                    "emailAddress": "alice@company.com",
                },
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "Started investigating..."}
                            ],
                        }
                    ],
                },
                "created": "2025-01-14T09:00:00.000+0000",
                "updated": "2025-01-14T09:00:00.000+0000",
            },
        ],
    }


@pytest.fixture
def sample_changelog():
    """Sample issue changelog response."""
    return {
        "startAt": 0,
        "maxResults": 100,
        "total": 5,
        "isLast": True,
        "values": [
            {
                "id": "10005",
                "author": {
                    "accountId": "5b10a2844c20165700ede21g",
                    "displayName": "Alice Smith",
                    "emailAddress": "alice@company.com",
                },
                "created": "2025-01-15T10:30:00.000+0000",
                "items": [
                    {
                        "field": "status",
                        "fieldtype": "jira",
                        "fieldId": "status",
                        "from": "3",
                        "fromString": "In Progress",
                        "to": "10000",
                        "toString": "Done",
                    },
                    {
                        "field": "resolution",
                        "fieldtype": "jira",
                        "fieldId": "resolution",
                        "from": None,
                        "fromString": None,
                        "to": "10000",
                        "toString": "Fixed",
                    },
                ],
            },
            {
                "id": "10004",
                "author": {
                    "accountId": "5b10a2844c20165700ede22h",
                    "displayName": "Bob Jones",
                    "emailAddress": "bob@company.com",
                },
                "created": "2025-01-14T15:15:00.000+0000",
                "items": [
                    {
                        "field": "assignee",
                        "fieldtype": "jira",
                        "fieldId": "assignee",
                        "from": None,
                        "fromString": None,
                        "to": "5b10a2844c20165700ede21g",
                        "toString": "Alice Smith",
                    }
                ],
            },
            {
                "id": "10003",
                "author": {
                    "accountId": "5b10a2844c20165700ede21g",
                    "displayName": "Alice Smith",
                    "emailAddress": "alice@company.com",
                },
                "created": "2025-01-14T09:00:00.000+0000",
                "items": [
                    {
                        "field": "status",
                        "fieldtype": "jira",
                        "fieldId": "status",
                        "from": "1",
                        "fromString": "Open",
                        "to": "3",
                        "toString": "In Progress",
                    }
                ],
            },
            {
                "id": "10002",
                "author": {
                    "accountId": "5b10a2844c20165700ede21g",
                    "displayName": "Alice Smith",
                    "emailAddress": "alice@company.com",
                },
                "created": "2025-01-14T09:00:00.000+0000",
                "items": [
                    {
                        "field": "Sprint",
                        "fieldtype": "custom",
                        "fieldId": "customfield_10020",
                        "from": None,
                        "fromString": None,
                        "to": "42",
                        "toString": "Sprint 42",
                    }
                ],
            },
            {
                "id": "10001",
                "author": {
                    "accountId": "5b10a2844c20165700ede23i",
                    "displayName": "Carol Lee",
                    "emailAddress": "carol@company.com",
                },
                "created": "2025-01-13T14:00:00.000+0000",
                "items": [
                    {
                        "field": "priority",
                        "fieldtype": "jira",
                        "fieldId": "priority",
                        "from": "3",
                        "fromString": "Medium",
                        "to": "2",
                        "toString": "High",
                    }
                ],
            },
        ],
    }


@pytest.fixture
def sample_notification_request():
    """Sample notification request."""
    return {
        "subject": "Action Required on PROJ-123",
        "textBody": "Please review this issue and provide feedback.",
        "htmlBody": "<p>Please review this issue and provide feedback.</p>",
        "to": {
            "reporter": True,
            "assignee": True,
            "watchers": True,
            "voters": False,
            "users": [],
            "groups": [],
        },
        "restrict": {"permissions": [], "groups": []},
    }


@pytest.fixture
def sample_notification_with_users():
    """Sample notification request with specific users."""
    return {
        "subject": "Critical Issue Update",
        "textBody": "This issue requires immediate attention.",
        "to": {
            "reporter": False,
            "assignee": False,
            "watchers": False,
            "voters": False,
            "users": [
                {"accountId": "5b10a2844c20165700ede21g"},
                {"accountId": "5b10a2844c20165700ede22h"},
            ],
            "groups": [{"name": "developers"}],
        },
    }
