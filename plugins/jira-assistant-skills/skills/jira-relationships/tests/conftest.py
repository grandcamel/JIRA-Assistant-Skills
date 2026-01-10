"""
Shared pytest fixtures for jira-relationships skill tests.

Provides mock JIRA API responses and client fixtures for testing
issue linking operations without hitting real JIRA instance.

Note: Common markers (unit, integration, relationships) are defined in the root pytest.ini.
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


# mock_jira_client is provided by root conftest.py


@pytest.fixture
def sample_link_types():
    """Sample link types returned by JIRA API."""
    return [
        {
            "id": "10000",
            "name": "Blocks",
            "inward": "is blocked by",
            "outward": "blocks",
            "self": "https://test.atlassian.net/rest/api/3/issueLinkType/10000",
        },
        {
            "id": "10001",
            "name": "Cloners",
            "inward": "is cloned by",
            "outward": "clones",
            "self": "https://test.atlassian.net/rest/api/3/issueLinkType/10001",
        },
        {
            "id": "10002",
            "name": "Duplicate",
            "inward": "is duplicated by",
            "outward": "duplicates",
            "self": "https://test.atlassian.net/rest/api/3/issueLinkType/10002",
        },
        {
            "id": "10003",
            "name": "Relates",
            "inward": "relates to",
            "outward": "relates to",
            "self": "https://test.atlassian.net/rest/api/3/issueLinkType/10003",
        },
    ]


@pytest.fixture
def sample_issue_links():
    """Sample issue links for an issue."""
    return [
        {
            "id": "20001",
            "type": {
                "id": "10000",
                "name": "Blocks",
                "inward": "is blocked by",
                "outward": "blocks",
            },
            "outwardIssue": {
                "id": "10101",
                "key": "PROJ-456",
                "self": "https://test.atlassian.net/rest/api/3/issue/10101",
                "fields": {
                    "summary": "Payment gateway integration",
                    "status": {"name": "In Progress"},
                    "issuetype": {"name": "Story"},
                },
            },
        },
        {
            "id": "20002",
            "type": {
                "id": "10003",
                "name": "Relates",
                "inward": "relates to",
                "outward": "relates to",
            },
            "outwardIssue": {
                "id": "10102",
                "key": "PROJ-789",
                "self": "https://test.atlassian.net/rest/api/3/issue/10102",
                "fields": {
                    "summary": "API documentation",
                    "status": {"name": "To Do"},
                    "issuetype": {"name": "Task"},
                },
            },
        },
        {
            "id": "20003",
            "type": {
                "id": "10000",
                "name": "Blocks",
                "inward": "is blocked by",
                "outward": "blocks",
            },
            "inwardIssue": {
                "id": "10100",
                "key": "PROJ-100",
                "self": "https://test.atlassian.net/rest/api/3/issue/10100",
                "fields": {
                    "summary": "Database schema update",
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Story"},
                },
            },
        },
    ]


@pytest.fixture
def sample_issue_with_links(sample_issue_links):
    """Sample JIRA issue response with links."""
    return {
        "id": "10123",
        "key": "PROJ-123",
        "self": "https://test.atlassian.net/rest/api/3/issue/10123",
        "fields": {
            "summary": "Main feature implementation",
            "status": {"name": "In Progress"},
            "issuetype": {"name": "Story"},
            "issuelinks": copy.deepcopy(sample_issue_links),
        },
    }


@pytest.fixture
def sample_issue_no_links():
    """Sample JIRA issue response with no links."""
    return {
        "id": "10124",
        "key": "PROJ-124",
        "self": "https://test.atlassian.net/rest/api/3/issue/10124",
        "fields": {
            "summary": "Standalone task",
            "status": {"name": "To Do"},
            "issuetype": {"name": "Task"},
            "issuelinks": [],
        },
    }


