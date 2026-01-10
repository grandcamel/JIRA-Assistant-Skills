"""
Pytest fixtures for jira-bulk tests.

Note: Common markers (unit, integration, bulk) are defined in the root pytest.ini.
"""

import pytest

# Shared fixtures from root conftest.py:
# mock_jira_client, sample_issues, sample_transitions, sample_issue, sample_project


@pytest.fixture
def sample_issue_with_subtasks():
    """Sample issue with subtasks for clone testing."""
    return {
        "key": "PROJ-1",
        "id": "10001",
        "fields": {
            "summary": "Parent issue",
            "description": {"type": "doc", "version": 1, "content": []},
            "status": {"name": "To Do", "id": "1"},
            "priority": {"name": "Medium", "id": "3"},
            "issuetype": {"name": "Story", "id": "10001"},
            "assignee": None,
            "project": {"key": "PROJ", "id": "10000"},
            "labels": ["feature"],
            "components": [{"id": "10000", "name": "Backend"}],
            "subtasks": [
                {
                    "key": "PROJ-4",
                    "id": "10004",
                    "fields": {"summary": "Subtask 1", "status": {"name": "To Do"}},
                },
                {
                    "key": "PROJ-5",
                    "id": "10005",
                    "fields": {"summary": "Subtask 2", "status": {"name": "Done"}},
                },
            ],
            "issuelinks": [
                {
                    "type": {
                        "name": "Blocks",
                        "inward": "is blocked by",
                        "outward": "blocks",
                    },
                    "outwardIssue": {
                        "key": "PROJ-10",
                        "fields": {"summary": "Blocked issue"},
                    },
                }
            ],
        },
    }


