"""
Shared pytest fixtures for jira-lifecycle skill tests.

Provides mock JIRA API responses and client fixtures for testing
workflow and lifecycle operations without hitting real JIRA instance.
"""

import copy
import pytest
from unittest.mock import Mock
import sys
from pathlib import Path


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "lifecycle: mark test as lifecycle skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")

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
def sample_issue_list():
    """Sample list of issues (search result format)."""
    return {
        'startAt': 0,
        'maxResults': 50,
        'total': 2,
        'issues': [
            {
                'id': '10101',
                'key': 'PROJ-123',
                'fields': {
                    'summary': 'First test issue',
                    'status': {'name': 'To Do'}
                }
            },
            {
                'id': '10102',
                'key': 'PROJ-124',
                'fields': {
                    'summary': 'Second test issue',
                    'status': {'name': 'In Progress'}
                }
            }
        ]
    }


@pytest.fixture
def mock_config_manager(mock_jira_client):
    """Mock config_manager.get_jira_client() to return mock client."""
    def _get_jira_client(profile=None):
        return mock_jira_client
    return _get_jira_client


@pytest.fixture
def sample_version():
    """Sample version response."""
    return {
        'id': '10000',
        'name': 'v1.0.0',
        'description': 'First release',
        'archived': False,
        'released': False,
        'startDate': '2025-01-01',
        'releaseDate': '2025-03-01',
        'project': 'PROJ',
        'projectId': 10000,
        'self': 'https://test.atlassian.net/rest/api/3/version/10000'
    }


@pytest.fixture
def sample_version_released():
    """Sample released version."""
    return {
        'id': '10001',
        'name': 'v0.9.0',
        'description': 'Beta release',
        'archived': False,
        'released': True,
        'startDate': '2024-10-01',
        'releaseDate': '2024-12-15',
        'projectId': 10000,
        'self': 'https://test.atlassian.net/rest/api/3/version/10001'
    }


@pytest.fixture
def sample_version_archived():
    """Sample archived version."""
    return {
        'id': '10002',
        'name': 'v0.5.0',
        'description': 'Legacy version',
        'archived': True,
        'released': True,
        'startDate': '2024-01-01',
        'releaseDate': '2024-06-01',
        'projectId': 10000,
        'self': 'https://test.atlassian.net/rest/api/3/version/10002'
    }


@pytest.fixture
def sample_versions_list():
    """Sample list of versions for a project."""
    return [
        {
            'id': '10003',
            'name': 'v1.2.0',
            'description': 'Next major release',
            'archived': False,
            'released': False,
            'startDate': '2025-03-01',
            'releaseDate': '2025-06-01',
            'projectId': 10000
        },
        {
            'id': '10000',
            'name': 'v1.0.0',
            'description': 'First release',
            'archived': False,
            'released': False,
            'startDate': '2025-01-01',
            'releaseDate': '2025-03-01',
            'projectId': 10000
        },
        {
            'id': '10001',
            'name': 'v0.9.0',
            'description': 'Beta release',
            'archived': False,
            'released': True,
            'startDate': '2024-10-01',
            'releaseDate': '2024-12-15',
            'projectId': 10000
        },
        {
            'id': '10002',
            'name': 'v0.5.0',
            'description': 'Legacy version',
            'archived': True,
            'released': True,
            'startDate': '2024-01-01',
            'releaseDate': '2024-06-01',
            'projectId': 10000
        }
    ]


@pytest.fixture
def sample_version_issue_counts():
    """Sample version issue counts."""
    return {
        'self': 'https://test.atlassian.net/rest/api/3/version/10000/relatedIssueCounts',
        'issuesFixedCount': 45,
        'issuesAffectedCount': 12,
        'issueCountWithCustomFieldsShowingVersion': 0
    }


@pytest.fixture
def sample_version_unresolved_count():
    """Sample unresolved issue count for version."""
    return {
        'self': 'https://test.atlassian.net/rest/api/3/version/10000/unresolvedIssueCount',
        'issuesUnresolvedCount': 3,
        'issuesCount': 48
    }


@pytest.fixture
def sample_component():
    """Sample component response."""
    return {
        'id': '10000',
        'name': 'Backend API',
        'description': 'Server-side API components',
        'project': 'PROJ',
        'projectId': 10000,
        'lead': {
            'accountId': '5b10a2844c20165700ede21g',
            'displayName': 'Alice Smith',
            'emailAddress': 'alice@company.com'
        },
        'leadAccountId': '5b10a2844c20165700ede21g',
        'assigneeType': 'COMPONENT_LEAD',
        'assignee': {
            'accountId': '5b10a2844c20165700ede21g',
            'displayName': 'Alice Smith'
        },
        'realAssigneeType': 'COMPONENT_LEAD',
        'realAssignee': {
            'accountId': '5b10a2844c20165700ede21g',
            'displayName': 'Alice Smith'
        },
        'self': 'https://test.atlassian.net/rest/api/3/component/10000'
    }


@pytest.fixture
def sample_components_list():
    """Sample list of components for a project."""
    return [
        {
            'id': '10003',
            'name': 'UI/Frontend',
            'description': 'User interface components',
            'project': 'PROJ',
            'projectId': 10000,
            'lead': {'displayName': 'Carol Lee', 'accountId': '5b10a2844c20165700ede23i'},
            'leadAccountId': '5b10a2844c20165700ede23i',
            'assigneeType': 'COMPONENT_LEAD'
        },
        {
            'id': '10000',
            'name': 'Backend API',
            'description': 'Server-side API components',
            'project': 'PROJ',
            'projectId': 10000,
            'lead': {'displayName': 'Alice Smith', 'accountId': '5b10a2844c20165700ede21g'},
            'leadAccountId': '5b10a2844c20165700ede21g',
            'assigneeType': 'COMPONENT_LEAD'
        },
        {
            'id': '10001',
            'name': 'Database',
            'description': 'Database layer and migrations',
            'project': 'PROJ',
            'projectId': 10000,
            'lead': {'displayName': 'Bob Jones', 'accountId': '5b10a2844c20165700ede22h'},
            'leadAccountId': '5b10a2844c20165700ede22h',
            'assigneeType': 'PROJECT_DEFAULT'
        },
        {
            'id': '10002',
            'name': 'Infrastructure',
            'description': 'DevOps and infrastructure',
            'project': 'PROJ',
            'projectId': 10000,
            'assigneeType': 'UNASSIGNED'
        }
    ]


@pytest.fixture
def sample_component_issue_counts():
    """Sample component issue counts."""
    return {
        'self': 'https://test.atlassian.net/rest/api/3/component/10000/relatedIssueCounts',
        'issueCount': 78
    }


@pytest.fixture
def sample_project():
    """Sample project response."""
    return {
        'id': '10000',
        'key': 'PROJ',
        'name': 'Test Project',
        'projectTypeKey': 'software',
        'simplified': False,
        'style': 'classic',
        'lead': {
            'accountId': '5b10a2844c20165700ede21g',
            'displayName': 'Alice Smith'
        },
        'self': 'https://test.atlassian.net/rest/api/3/project/10000'
    }
