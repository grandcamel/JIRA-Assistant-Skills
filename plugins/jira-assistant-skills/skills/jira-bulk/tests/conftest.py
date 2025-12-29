"""
Pytest fixtures for jira-bulk tests.
"""

import sys
from pathlib import Path
from unittest.mock import patch
import pytest

# Add shared lib to path


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "bulk: mark test as bulk operations skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")


@pytest.fixture
def mock_jira_client():
    """Create a mock JiraClient with common methods."""
    from unittest.mock import MagicMock
    client = MagicMock()
    client.search_issues = MagicMock()
    client.get_issue = MagicMock()
    client.get_transitions = MagicMock()
    client.transition_issue = MagicMock()
    client.assign_issue = MagicMock()
    client.update_issue = MagicMock()
    client.create_issue = MagicMock()
    client.get_current_user_id = MagicMock(return_value='current-user-account-id')
    client.close = MagicMock()
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    return client


@pytest.fixture
def sample_issues():
    """Sample issue data for testing."""
    return [
        {
            'key': 'PROJ-1',
            'id': '10001',
            'fields': {
                'summary': 'First issue',
                'status': {'name': 'To Do', 'id': '1'},
                'priority': {'name': 'Medium', 'id': '3'},
                'issuetype': {'name': 'Task', 'id': '10001'},
                'assignee': None,
                'project': {'key': 'PROJ', 'id': '10000'},
                'labels': [],
            }
        },
        {
            'key': 'PROJ-2',
            'id': '10002',
            'fields': {
                'summary': 'Second issue',
                'status': {'name': 'In Progress', 'id': '2'},
                'priority': {'name': 'High', 'id': '2'},
                'issuetype': {'name': 'Bug', 'id': '10002'},
                'assignee': {'accountId': 'user-123', 'displayName': 'John Doe'},
                'project': {'key': 'PROJ', 'id': '10000'},
                'labels': ['bug'],
            }
        },
        {
            'key': 'PROJ-3',
            'id': '10003',
            'fields': {
                'summary': 'Third issue',
                'status': {'name': 'To Do', 'id': '1'},
                'priority': {'name': 'Low', 'id': '4'},
                'issuetype': {'name': 'Task', 'id': '10001'},
                'assignee': {'accountId': 'user-456', 'displayName': 'Jane Smith'},
                'project': {'key': 'PROJ', 'id': '10000'},
                'labels': ['feature'],
            }
        },
    ]


@pytest.fixture
def sample_transitions():
    """Sample transition data for testing."""
    return [
        {
            'id': '21',
            'name': 'In Progress',
            'to': {'name': 'In Progress', 'id': '3'}
        },
        {
            'id': '31',
            'name': 'Done',
            'to': {'name': 'Done', 'id': '4'}
        },
        {
            'id': '41',
            'name': 'In Review',
            'to': {'name': 'In Review', 'id': '5'}
        },
    ]


@pytest.fixture
def sample_issue_with_subtasks():
    """Sample issue with subtasks for clone testing."""
    return {
        'key': 'PROJ-1',
        'id': '10001',
        'fields': {
            'summary': 'Parent issue',
            'description': {'type': 'doc', 'version': 1, 'content': []},
            'status': {'name': 'To Do', 'id': '1'},
            'priority': {'name': 'Medium', 'id': '3'},
            'issuetype': {'name': 'Story', 'id': '10001'},
            'assignee': None,
            'project': {'key': 'PROJ', 'id': '10000'},
            'labels': ['feature'],
            'components': [{'id': '10000', 'name': 'Backend'}],
            'subtasks': [
                {
                    'key': 'PROJ-4',
                    'id': '10004',
                    'fields': {
                        'summary': 'Subtask 1',
                        'status': {'name': 'To Do'}
                    }
                },
                {
                    'key': 'PROJ-5',
                    'id': '10005',
                    'fields': {
                        'summary': 'Subtask 2',
                        'status': {'name': 'Done'}
                    }
                },
            ],
            'issuelinks': [
                {
                    'type': {'name': 'Blocks', 'inward': 'is blocked by', 'outward': 'blocks'},
                    'outwardIssue': {'key': 'PROJ-10', 'fields': {'summary': 'Blocked issue'}}
                }
            ],
        }
    }


@pytest.fixture
def mock_get_jira_client(mock_jira_client):
    """Patch get_jira_client to return mock client."""
    with patch('config_manager.get_jira_client', return_value=mock_jira_client):
        yield mock_jira_client
