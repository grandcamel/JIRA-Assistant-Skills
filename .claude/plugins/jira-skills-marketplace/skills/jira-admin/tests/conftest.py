"""
Shared pytest fixtures for jira-admin skill tests.

Provides mock JIRA API responses and client fixtures for testing
issue type and issue type scheme management.
"""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "admin: mark test as admin skill test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
from unittest.mock import Mock, MagicMock
import sys
from pathlib import Path

# Add paths to sys.path before any imports that depend on them
_this_dir = Path(__file__).parent
_shared_lib_path = str(_this_dir.parent.parent / 'shared' / 'scripts' / 'lib')
_scripts_path = str(_this_dir.parent / 'scripts')
_tests_path = str(_this_dir)
_fixtures_path = str(_this_dir / 'fixtures')

# Insert at beginning to ensure our paths take precedence
for path in [_shared_lib_path, _scripts_path, _tests_path, _fixtures_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

from fixtures.issue_type_responses import (
    ISSUE_TYPES_RESPONSE,
    EPIC_RESPONSE,
    STORY_RESPONSE,
    SUBTASK_RESPONSE,
    CREATED_ISSUE_TYPE_RESPONSE,
    PROJECT_SCOPED_ISSUE_TYPE,
    ISSUE_TYPE_SCHEMES_RESPONSE,
    DEFAULT_SCHEME_RESPONSE,
    SOFTWARE_SCHEME_RESPONSE,
    CREATED_SCHEME_RESPONSE,
    SCHEME_FOR_PROJECTS_RESPONSE,
    SCHEME_MAPPINGS_RESPONSE,
    ALTERNATIVES_RESPONSE,
)

from fixtures.notification_scheme_responses import (
    NOTIFICATION_SCHEMES_RESPONSE,
    NOTIFICATION_SCHEME_DETAIL_RESPONSE,
    NOTIFICATION_SCHEME_ALL_TYPES,
    PROJECT_MAPPINGS_RESPONSE,
    CREATED_NOTIFICATION_SCHEME,
    EMPTY_NOTIFICATION_SCHEMES,
    EMPTY_SCHEME,
    NOTIFICATION_EVENTS,
    RECIPIENT_TYPES,
)

from fixtures.permission_scheme_responses import (
    PERMISSION_SCHEMES_RESPONSE,
    PERMISSION_SCHEME_DETAIL_RESPONSE,
    MINIMAL_SCHEME_RESPONSE,
    CREATED_SCHEME_RESPONSE as PERMISSION_CREATED_SCHEME_RESPONSE,
    CREATED_SCHEME_WITH_GRANTS_RESPONSE,
    UPDATED_SCHEME_RESPONSE,
    PERMISSION_GRANTS_RESPONSE,
    CREATED_GRANT_RESPONSE,
    ALL_PERMISSIONS_RESPONSE,
    PROJECT_PERMISSION_SCHEME_RESPONSE,
    PROJECT_ROLES_RESPONSE,
    EMPTY_SCHEMES_RESPONSE,
    SCHEME_NOT_FOUND_ERROR,
    SCHEME_IN_USE_ERROR,
    PERMISSION_DENIED_ERROR,
)

from fixtures.screen_responses import (
    SCREENS_RESPONSE,
    DEFAULT_SCREEN,
    BUG_CREATE_SCREEN,
    EPIC_SCREEN,
    DEFAULT_SCREEN_TABS,
    SINGLE_TAB,
    FIELD_TAB_FIELDS,
    CUSTOM_FIELDS_TAB_FIELDS,
    ALL_SCREEN_FIELDS,
    AVAILABLE_FIELDS,
    ADDED_FIELD_RESPONSE,
    SCREEN_SCHEMES_RESPONSE,
    DEFAULT_SCREEN_SCHEME,
    BUG_SCREEN_SCHEME,
    ISSUE_TYPE_SCREEN_SCHEMES_RESPONSE,
    DEFAULT_ISSUE_TYPE_SCREEN_SCHEME,
    SOFTWARE_ISSUE_TYPE_SCREEN_SCHEME,
    ISSUE_TYPE_SCREEN_SCHEME_MAPPINGS,
    PROJECT_ISSUE_TYPE_SCREEN_SCHEMES,
    EMPTY_SCREENS_RESPONSE,
    EMPTY_SCREEN_SCHEMES_RESPONSE,
    EMPTY_ISSUE_TYPE_SCREEN_SCHEMES_RESPONSE,
    SCREENS_PAGE_1,
    SCREENS_PAGE_2,
    SCREENS_PAGE_3,
    PROJECT_ISSUE_TYPES,
    SAMPLE_PROJECT,
)

from fixtures.workflow_responses import (
    WORKFLOWS_RESPONSE,
    SOFTWARE_WORKFLOW,
    BUG_WORKFLOW,
    WORKFLOW_SEARCH_RESPONSE,
    WORKFLOW_SCHEMES_RESPONSE as WORKFLOW_SCHEMES_LIST_RESPONSE,
    SOFTWARE_SCHEME_DETAIL,
    PROJECT_WORKFLOW_SCHEME,
    ASSIGN_SCHEME_TASK_RESPONSE,
    TASK_COMPLETE_RESPONSE,
    TASK_IN_PROGRESS_RESPONSE,
    TASK_FAILED_RESPONSE,
    ALL_STATUSES_RESPONSE,
    STATUS_SEARCH_RESPONSE,
    SINGLE_STATUS,
    ISSUE_TRANSITIONS,
    ISSUE_WITH_STATUS,
    SCHEMES_FOR_WORKFLOW,
    EMPTY_WORKFLOWS_RESPONSE,
    EMPTY_SCHEMES_RESPONSE as WORKFLOW_EMPTY_SCHEMES_RESPONSE,
    EMPTY_STATUSES_RESPONSE,
    WORKFLOWS_PAGE_1,
    WORKFLOWS_PAGE_2,
)


@pytest.fixture
def mock_jira_client():
    """Mock JiraClient for testing without API calls."""
    client = Mock()
    client.base_url = "https://test.atlassian.net"
    client.email = "test@example.com"
    client.close = Mock()
    return client


@pytest.fixture
def issue_types_response():
    """Sample JIRA API response for all issue types."""
    return ISSUE_TYPES_RESPONSE.copy()


@pytest.fixture
def epic_response():
    """Sample JIRA API response for Epic issue type."""
    return EPIC_RESPONSE.copy()


@pytest.fixture
def story_response():
    """Sample JIRA API response for Story issue type."""
    return STORY_RESPONSE.copy()


@pytest.fixture
def subtask_response():
    """Sample JIRA API response for Subtask issue type."""
    return SUBTASK_RESPONSE.copy()


@pytest.fixture
def created_issue_type_response():
    """Sample JIRA API response for newly created issue type."""
    return CREATED_ISSUE_TYPE_RESPONSE.copy()


@pytest.fixture
def project_scoped_issue_type():
    """Sample project-scoped issue type."""
    return PROJECT_SCOPED_ISSUE_TYPE.copy()


@pytest.fixture
def issue_type_schemes_response():
    """Sample JIRA API response for issue type schemes list."""
    return ISSUE_TYPE_SCHEMES_RESPONSE.copy()


@pytest.fixture
def default_scheme_response():
    """Sample JIRA API response for default issue type scheme."""
    return DEFAULT_SCHEME_RESPONSE.copy()


@pytest.fixture
def software_scheme_response():
    """Sample JIRA API response for software development scheme."""
    return SOFTWARE_SCHEME_RESPONSE.copy()


@pytest.fixture
def created_scheme_response():
    """Sample JIRA API response for newly created scheme."""
    return CREATED_SCHEME_RESPONSE.copy()


@pytest.fixture
def scheme_for_projects_response():
    """Sample JIRA API response for schemes assigned to projects."""
    return SCHEME_FOR_PROJECTS_RESPONSE.copy()


@pytest.fixture
def scheme_mappings_response():
    """Sample JIRA API response for scheme mappings."""
    return SCHEME_MAPPINGS_RESPONSE.copy()


@pytest.fixture
def alternatives_response():
    """Sample JIRA API response for alternative issue types."""
    return ALTERNATIVES_RESPONSE.copy()


@pytest.fixture
def mock_config_manager(mock_jira_client):
    """Mock config_manager.get_jira_client() to return mock client."""
    def _get_jira_client(profile=None):
        return mock_jira_client
    return _get_jira_client


# ========== User Management Fixtures ==========

@pytest.fixture
def sample_user():
    """Sample user object for testing."""
    return {
        "accountId": "5b10ac8d82e05b22cc7d4ef5",
        "accountType": "atlassian",
        "displayName": "John Doe",
        "emailAddress": "john.doe@example.com",
        "active": True,
        "timeZone": "America/New_York",
        "locale": "en-US",
        "avatarUrls": {
            "48x48": "https://avatar.url/48x48",
            "24x24": "https://avatar.url/24x24",
            "16x16": "https://avatar.url/16x16",
            "32x32": "https://avatar.url/32x32"
        }
    }


@pytest.fixture
def sample_user_with_groups(sample_user):
    """Sample user with groups expanded."""
    user = sample_user.copy()
    user["groups"] = {
        "size": 3,
        "items": [
            {"name": "jira-users", "groupId": "group-id-1"},
            {"name": "jira-developers", "groupId": "group-id-2"},
            {"name": "jira-administrators", "groupId": "group-id-3"}
        ]
    }
    user["applicationRoles"] = {
        "size": 1,
        "items": [
            {"name": "Jira Software", "key": "jira-software"}
        ]
    }
    return user


@pytest.fixture
def sample_inactive_user():
    """Sample inactive user for testing."""
    return {
        "accountId": "inactive-user-123",
        "accountType": "atlassian",
        "displayName": "Inactive User",
        "emailAddress": "inactive@example.com",
        "active": False,
        "timeZone": "UTC",
        "locale": "en-US"
    }


@pytest.fixture
def privacy_restricted_user():
    """User with privacy controls enabled (missing email, timezone, locale)."""
    return {
        "accountId": "a1b2c3d4e5f6g7h8i9j0k1l2",
        "accountType": "atlassian",
        "displayName": "Jane Smith",
        "active": True
        # Note: emailAddress, timeZone, locale are missing due to privacy controls
    }


@pytest.fixture
def deleted_user():
    """User who has been deleted/anonymized."""
    return {
        "accountId": "unknown",
        "accountType": "atlassian",
        "displayName": "Deleted User",
        "active": False
    }


@pytest.fixture
def sample_users():
    """List of sample users for search results."""
    return [
        {
            "accountId": "5b10ac8d82e05b22cc7d4ef5",
            "displayName": "John Doe",
            "emailAddress": "john.doe@example.com",
            "active": True
        },
        {
            "accountId": "a1b2c3d4e5f6g7h8i9j0k1l2",
            "displayName": "John Smith",
            "emailAddress": "john.smith@example.com",
            "active": True
        },
        {
            "accountId": "9z8y7x6w5v4u3t2s1r0q9p8o",
            "displayName": "Johnny Bravo",
            "emailAddress": "johnny@example.com",
            "active": False
        }
    ]


@pytest.fixture
def sample_user_groups():
    """Sample user groups response."""
    return [
        {"name": "jira-users", "groupId": "group-id-1", "self": "https://site.atlassian.net/rest/api/3/group?groupId=group-id-1"},
        {"name": "jira-developers", "groupId": "group-id-2", "self": "https://site.atlassian.net/rest/api/3/group?groupId=group-id-2"},
        {"name": "jira-administrators", "groupId": "group-id-3", "self": "https://site.atlassian.net/rest/api/3/group?groupId=group-id-3"}
    ]


# ========== Group Management Fixtures ==========

@pytest.fixture
def sample_group():
    """Sample group object for testing."""
    return {
        "name": "jira-developers",
        "groupId": "276f955c-63d7-42c8-9520-92d01dca0625",
        "self": "https://site.atlassian.net/rest/api/3/group?groupId=276f955c-63d7-42c8-9520-92d01dca0625"
    }


@pytest.fixture
def sample_groups():
    """List of sample groups for list/search results."""
    return [
        {
            "name": "jira-administrators",
            "groupId": "admin-group-id-123",
            "self": "https://site.atlassian.net/rest/api/3/group?groupId=admin-group-id-123"
        },
        {
            "name": "jira-developers",
            "groupId": "276f955c-63d7-42c8-9520-92d01dca0625",
            "self": "https://site.atlassian.net/rest/api/3/group?groupId=276f955c-63d7-42c8-9520-92d01dca0625"
        },
        {
            "name": "jira-users",
            "groupId": "users-group-id-456",
            "self": "https://site.atlassian.net/rest/api/3/group?groupId=users-group-id-456"
        },
        {
            "name": "project-admins",
            "groupId": "project-admins-id-789",
            "self": "https://site.atlassian.net/rest/api/3/group?groupId=project-admins-id-789"
        }
    ]


@pytest.fixture
def sample_groups_picker_response(sample_groups):
    """Sample response from groups picker API."""
    return {
        "header": "Showing 4 of 4 matching groups",
        "total": 4,
        "groups": sample_groups
    }


@pytest.fixture
def sample_group_members():
    """Sample group members response."""
    return {
        "self": "https://site.atlassian.net/rest/api/3/group/member",
        "maxResults": 50,
        "startAt": 0,
        "total": 3,
        "isLast": True,
        "values": [
            {
                "accountId": "5b10ac8d82e05b22cc7d4ef5",
                "displayName": "John Doe",
                "emailAddress": "john.doe@example.com",
                "active": True
            },
            {
                "accountId": "a1b2c3d4e5f6g7h8i9j0k1l2",
                "displayName": "Jane Smith",
                "active": True
                # emailAddress missing due to privacy
            },
            {
                "accountId": "9z8y7x6w5v4u3t2s1r0q9p8o",
                "displayName": "Bob Johnson",
                "emailAddress": "bob.j@example.com",
                "active": True
            }
        ]
    }


@pytest.fixture
def sample_empty_group_members():
    """Sample empty group members response."""
    return {
        "self": "https://site.atlassian.net/rest/api/3/group/member",
        "maxResults": 50,
        "startAt": 0,
        "total": 0,
        "isLast": True,
        "values": []
    }


@pytest.fixture
def system_groups():
    """List of protected system group names."""
    return [
        "jira-administrators",
        "jira-users",
        "jira-software-users",
        "site-admins"
    ]


# ========== Notification Scheme Fixtures ==========

@pytest.fixture
def sample_notification_schemes():
    """Sample notification schemes list for testing."""
    import copy
    return copy.deepcopy(NOTIFICATION_SCHEMES_RESPONSE)


@pytest.fixture
def sample_notification_scheme_detail():
    """Sample detailed notification scheme for testing."""
    import copy
    return copy.deepcopy(NOTIFICATION_SCHEME_DETAIL_RESPONSE)


@pytest.fixture
def sample_notification_scheme_with_all_types():
    """Sample scheme with all notification types for testing."""
    import copy
    return copy.deepcopy(NOTIFICATION_SCHEME_ALL_TYPES)


@pytest.fixture
def sample_project_mappings():
    """Sample project-to-scheme mappings for testing."""
    import copy
    return copy.deepcopy(PROJECT_MAPPINGS_RESPONSE)


@pytest.fixture
def sample_created_notification_scheme():
    """Sample response from creating a notification scheme."""
    import copy
    return copy.deepcopy(CREATED_NOTIFICATION_SCHEME)


@pytest.fixture
def empty_notification_schemes():
    """Empty notification schemes response for testing."""
    import copy
    return copy.deepcopy(EMPTY_NOTIFICATION_SCHEMES)


@pytest.fixture
def empty_scheme():
    """Notification scheme with no events configured."""
    import copy
    return copy.deepcopy(EMPTY_SCHEME)


@pytest.fixture
def sample_notification_events():
    """Sample notification event types for testing."""
    import copy
    return copy.deepcopy(NOTIFICATION_EVENTS)


@pytest.fixture
def sample_recipient_types():
    """Sample valid notification recipient types."""
    import copy
    return copy.deepcopy(RECIPIENT_TYPES)


# ========== Automation Rules Fixtures ==========

@pytest.fixture
def mock_automation_client():
    """Create a mock AutomationClient with common methods."""
    client = MagicMock()
    client.cloud_id = 'test-cloud-id-12345'
    client.base_url = 'https://api.atlassian.com/automation/public/jira/test-cloud-id-12345'

    # Rule discovery methods
    client.get_rules = MagicMock()
    client.search_rules = MagicMock()
    client.get_rule = MagicMock()

    # State management methods
    client.update_rule_state = MagicMock()
    client.enable_rule = MagicMock()
    client.disable_rule = MagicMock()

    # Manual rules methods
    client.get_manual_rules = MagicMock()
    client.invoke_manual_rule = MagicMock()

    # Template methods
    client.get_templates = MagicMock()
    client.get_template = MagicMock()
    client.create_rule_from_template = MagicMock()

    # Rule creation/update methods
    client.create_rule = MagicMock()
    client.update_rule = MagicMock()
    client.update_rule_scope = MagicMock()

    # Context manager support
    client.close = MagicMock()
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)

    return client


@pytest.fixture
def sample_automation_rules():
    """Sample automation rule data for testing."""
    return [
        {
            'id': 'ari:cloud:jira::site/12345-rule-001',
            'name': 'Auto-assign to lead',
            'state': 'ENABLED',
            'ruleScope': {
                'resources': ['ari:cloud:jira:12345:project/10000']
            },
            'canManage': True,
            'trigger': {
                'type': 'jira.issue.event.trigger:created'
            },
            'created': '2025-01-15T10:30:00.000Z',
            'updated': '2025-01-20T14:45:00.000Z'
        },
        {
            'id': 'ari:cloud:jira::site/12345-rule-002',
            'name': 'Comment on status change',
            'state': 'DISABLED',
            'ruleScope': {
                'resources': []  # Global scope
            },
            'canManage': True,
            'trigger': {
                'type': 'jira.issue.event.trigger:transitioned'
            },
            'created': '2025-01-10T09:00:00.000Z',
            'updated': '2025-01-18T16:30:00.000Z'
        },
        {
            'id': 'ari:cloud:jira::site/12345-rule-003',
            'name': 'Notify on high priority',
            'state': 'ENABLED',
            'ruleScope': {
                'resources': ['ari:cloud:jira:12345:project/10001']
            },
            'canManage': False,
            'trigger': {
                'type': 'jira.issue.field.changed:priority'
            },
            'created': '2025-01-05T11:15:00.000Z',
            'updated': '2025-01-12T08:20:00.000Z'
        },
    ]


@pytest.fixture
def sample_rule_detail():
    """Sample detailed automation rule configuration."""
    return {
        'id': 'ari:cloud:jira::site/12345-rule-001',
        'name': 'Auto-assign to lead',
        'description': 'Automatically assigns new issues to project lead',
        'state': 'ENABLED',
        'ruleScope': {
            'resources': ['ari:cloud:jira:12345:project/10000']
        },
        'trigger': {
            'type': 'jira.issue.event.trigger:created',
            'configuration': {
                'issueEvent': 'issue_created'
            }
        },
        'components': [
            {
                'type': 'jira.issue.assign',
                'value': '{{project.lead.accountId}}',
                'children': []
            }
        ],
        'connections': [],
        'canManage': True,
        'created': '2025-01-15T10:30:00.000Z',
        'updated': '2025-01-20T14:45:00.000Z',
        'authorAccountId': '557058:f58131cb-b67d-43c7-b30d-6b58d40bd077'
    }


@pytest.fixture
def sample_manual_rules():
    """Sample manually-triggered automation rules."""
    return [
        {
            'id': '12345',
            'name': 'Escalate to Manager',
            'description': 'Escalate issue to manager for review',
            'contextType': 'issue'
        },
        {
            'id': '12346',
            'name': 'Request More Info',
            'description': 'Request additional information from reporter',
            'contextType': 'issue'
        }
    ]


@pytest.fixture
def sample_automation_templates():
    """Sample automation templates."""
    return [
        {
            'id': 'template-001',
            'name': 'Assign issues to project lead',
            'description': 'Automatically assigns new issues to the project lead',
            'category': 'Issue Management',
            'tags': ['assignment', 'automation'],
            'parameters': [
                {
                    'name': 'projectKey',
                    'type': 'string',
                    'required': True,
                    'description': 'Project key to apply the rule'
                }
            ]
        },
        {
            'id': 'template-002',
            'name': 'Close stale issues',
            'description': 'Automatically closes issues with no activity for 30 days',
            'category': 'Issue Management',
            'tags': ['cleanup', 'automation'],
            'parameters': [
                {
                    'name': 'daysInactive',
                    'type': 'number',
                    'required': True,
                    'description': 'Days of inactivity before closing'
                }
            ]
        }
    ]


@pytest.fixture
def sample_rules_response(sample_automation_rules):
    """Sample paginated rules response."""
    return {
        'values': sample_automation_rules,
        'links': {
            'next': '?cursor=next_page_token'
        },
        'hasMore': False
    }


@pytest.fixture
def mock_get_automation_client(mock_automation_client):
    """Patch get_automation_client to return mock client."""
    from unittest.mock import patch
    with patch('config_manager.get_automation_client', return_value=mock_automation_client):
        yield mock_automation_client


# ========== Project Management Fixtures ==========

@pytest.fixture
def sample_project_response():
    """Sample JIRA API response for a project."""
    return {
        "self": "https://test.atlassian.net/rest/api/3/project/10000",
        "id": "10000",
        "key": "PROJ",
        "name": "Test Project",
        "description": "A test project for development",
        "avatarUrls": {
            "48x48": "https://test.atlassian.net/secure/projectavatar?avatarId=10324",
            "24x24": "https://test.atlassian.net/secure/projectavatar?size=small&avatarId=10324",
            "16x16": "https://test.atlassian.net/secure/projectavatar?size=xsmall&avatarId=10324",
            "32x32": "https://test.atlassian.net/secure/projectavatar?size=medium&avatarId=10324"
        },
        "projectTypeKey": "software",
        "simplified": False,
        "style": "classic",
        "isPrivate": False,
        "lead": {
            "self": "https://test.atlassian.net/rest/api/3/user?accountId=557058:test-user-id",
            "accountId": "557058:test-user-id",
            "displayName": "Test User",
            "emailAddress": "test@example.com",
            "active": True
        },
        "url": "https://example.com/project",
        "assigneeType": "PROJECT_LEAD",
        "projectCategory": {
            "self": "https://test.atlassian.net/rest/api/3/projectCategory/10000",
            "id": "10000",
            "name": "Development",
            "description": "Development projects"
        }
    }


@pytest.fixture
def sample_project_create_response():
    """Sample JIRA API response for project creation."""
    return {
        "self": "https://test.atlassian.net/rest/api/3/project/10000",
        "id": "10000",
        "key": "PROJ",
        "name": "Test Project",
        "avatarUrls": {
            "48x48": "https://test.atlassian.net/secure/projectavatar?avatarId=10324"
        },
        "projectTypeKey": "software",
        "simplified": False,
        "style": "classic",
        "isPrivate": False
    }


@pytest.fixture
def sample_project_list_response():
    """Sample JIRA API response for project search/list."""
    return {
        "self": "https://test.atlassian.net/rest/api/3/project/search",
        "nextPage": "https://test.atlassian.net/rest/api/3/project/search?startAt=50",
        "maxResults": 50,
        "startAt": 0,
        "total": 2,
        "isLast": True,
        "values": [
            {
                "self": "https://test.atlassian.net/rest/api/3/project/10000",
                "id": "10000",
                "key": "PROJ",
                "name": "Test Project",
                "projectTypeKey": "software",
                "simplified": False,
                "style": "classic",
                "isPrivate": False,
                "avatarUrls": {
                    "48x48": "https://test.atlassian.net/secure/projectavatar?avatarId=10324"
                },
                "projectCategory": {
                    "id": "10000",
                    "name": "Development"
                }
            },
            {
                "self": "https://test.atlassian.net/rest/api/3/project/10001",
                "id": "10001",
                "key": "KANBAN",
                "name": "Kanban Board",
                "projectTypeKey": "software",
                "simplified": True,
                "style": "next-gen",
                "isPrivate": False,
                "avatarUrls": {
                    "48x48": "https://test.atlassian.net/secure/projectavatar?avatarId=10325"
                }
            }
        ]
    }


@pytest.fixture
def sample_category_response():
    """Sample JIRA API response for a project category."""
    return {
        "self": "https://test.atlassian.net/rest/api/3/projectCategory/10000",
        "id": "10000",
        "name": "Development",
        "description": "All development projects"
    }


@pytest.fixture
def sample_categories_list():
    """Sample JIRA API response for project categories list."""
    return [
        {
            "self": "https://test.atlassian.net/rest/api/3/projectCategory/10000",
            "id": "10000",
            "name": "Development",
            "description": "All development projects"
        },
        {
            "self": "https://test.atlassian.net/rest/api/3/projectCategory/10001",
            "id": "10001",
            "name": "Marketing",
            "description": "Marketing and campaigns"
        },
        {
            "self": "https://test.atlassian.net/rest/api/3/projectCategory/10002",
            "id": "10002",
            "name": "Support",
            "description": "Customer support projects"
        }
    ]


@pytest.fixture
def sample_project_types():
    """Sample JIRA API response for project types."""
    return [
        {
            "key": "software",
            "formattedKey": "Software",
            "descriptionI18nKey": "jira.project.type.software.description",
            "icon": "https://test.atlassian.net/images/icons/project/software.svg"
        },
        {
            "key": "business",
            "formattedKey": "Business",
            "descriptionI18nKey": "jira.project.type.business.description",
            "icon": "https://test.atlassian.net/images/icons/project/business.svg"
        },
        {
            "key": "service_desk",
            "formattedKey": "Service Desk",
            "descriptionI18nKey": "jira.project.type.service_desk.description",
            "icon": "https://test.atlassian.net/images/icons/project/servicedesk.svg"
        }
    ]


@pytest.fixture
def sample_avatars_response():
    """Sample JIRA API response for project avatars."""
    return {
        "system": [
            {
                "id": "10200",
                "owner": "system",
                "isSystemAvatar": True,
                "urls": {
                    "48x48": "https://test.atlassian.net/secure/projectavatar?avatarId=10200",
                    "24x24": "https://test.atlassian.net/secure/projectavatar?size=small&avatarId=10200"
                }
            },
            {
                "id": "10201",
                "owner": "system",
                "isSystemAvatar": True,
                "urls": {
                    "48x48": "https://test.atlassian.net/secure/projectavatar?avatarId=10201",
                    "24x24": "https://test.atlassian.net/secure/projectavatar?size=small&avatarId=10201"
                }
            }
        ],
        "custom": [
            {
                "id": "10300",
                "owner": "PROJ",
                "isSystemAvatar": False,
                "urls": {
                    "48x48": "https://test.atlassian.net/secure/projectavatar?avatarId=10300"
                }
            }
        ]
    }


@pytest.fixture
def sample_task_response():
    """Sample JIRA API response for async task status."""
    return {
        "self": "https://test.atlassian.net/rest/api/3/task/10000",
        "id": "10000",
        "description": "Project deletion",
        "status": "COMPLETE",
        "message": "Project PROJ deleted successfully",
        "result": "Project deleted",
        "submittedBy": "557058:test-user-id",
        "progress": 100,
        "elapsedRuntime": 5000,
        "submitted": 1704067200000,
        "started": 1704067200100,
        "finished": 1704067205100,
        "lastUpdate": 1704067205100
    }


@pytest.fixture
def sample_trash_projects():
    """Sample JIRA API response for trashed projects."""
    return {
        "self": "https://test.atlassian.net/rest/api/3/project/search",
        "maxResults": 50,
        "startAt": 0,
        "total": 1,
        "isLast": True,
        "values": [
            {
                "self": "https://test.atlassian.net/rest/api/3/project/10002",
                "id": "10002",
                "key": "OLD",
                "name": "Old Project",
                "projectTypeKey": "software",
                "simplified": False,
                "style": "classic",
                "isPrivate": False,
                "deleted": True,
                "deletedDate": "2025-01-10T12:00:00.000+0000",
                "deletedBy": {
                    "accountId": "557058:test-user-id",
                    "displayName": "Test User"
                },
                "retentionTillDate": "2025-03-11T12:00:00.000+0000"
            }
        ]
    }


# ========== Screen Management Fixtures ==========

@pytest.fixture
def screens_response():
    """Sample JIRA API response for all screens."""
    import copy
    return copy.deepcopy(SCREENS_RESPONSE)


@pytest.fixture
def default_screen():
    """Sample default screen for testing."""
    import copy
    return copy.deepcopy(DEFAULT_SCREEN)


@pytest.fixture
def bug_create_screen():
    """Sample bug create screen with project scope."""
    import copy
    return copy.deepcopy(BUG_CREATE_SCREEN)


@pytest.fixture
def epic_screen():
    """Sample epic screen for testing."""
    import copy
    return copy.deepcopy(EPIC_SCREEN)


@pytest.fixture
def default_screen_tabs():
    """Sample screen tabs for default screen."""
    import copy
    return copy.deepcopy(DEFAULT_SCREEN_TABS)


@pytest.fixture
def single_tab():
    """Sample single tab response."""
    import copy
    return copy.deepcopy(SINGLE_TAB)


@pytest.fixture
def field_tab_fields():
    """Sample fields in Field Tab."""
    import copy
    return copy.deepcopy(FIELD_TAB_FIELDS)


@pytest.fixture
def custom_fields_tab_fields():
    """Sample fields in Custom Fields tab."""
    import copy
    return copy.deepcopy(CUSTOM_FIELDS_TAB_FIELDS)


@pytest.fixture
def all_screen_fields():
    """Sample all fields from all tabs."""
    import copy
    return copy.deepcopy(ALL_SCREEN_FIELDS)


@pytest.fixture
def available_fields():
    """Sample available fields that can be added."""
    import copy
    return copy.deepcopy(AVAILABLE_FIELDS)


@pytest.fixture
def added_field_response():
    """Sample response when adding a field."""
    import copy
    return copy.deepcopy(ADDED_FIELD_RESPONSE)


@pytest.fixture
def screen_schemes_response():
    """Sample JIRA API response for screen schemes."""
    import copy
    return copy.deepcopy(SCREEN_SCHEMES_RESPONSE)


@pytest.fixture
def default_screen_scheme():
    """Sample default screen scheme."""
    import copy
    return copy.deepcopy(DEFAULT_SCREEN_SCHEME)


@pytest.fixture
def bug_screen_scheme():
    """Sample bug screen scheme."""
    import copy
    return copy.deepcopy(BUG_SCREEN_SCHEME)


@pytest.fixture
def issue_type_screen_schemes_response():
    """Sample JIRA API response for issue type screen schemes."""
    import copy
    return copy.deepcopy(ISSUE_TYPE_SCREEN_SCHEMES_RESPONSE)


@pytest.fixture
def default_issue_type_screen_scheme():
    """Sample default issue type screen scheme."""
    import copy
    return copy.deepcopy(DEFAULT_ISSUE_TYPE_SCREEN_SCHEME)


@pytest.fixture
def software_issue_type_screen_scheme():
    """Sample software issue type screen scheme."""
    import copy
    return copy.deepcopy(SOFTWARE_ISSUE_TYPE_SCREEN_SCHEME)


@pytest.fixture
def issue_type_screen_scheme_mappings():
    """Sample issue type to screen scheme mappings."""
    import copy
    return copy.deepcopy(ISSUE_TYPE_SCREEN_SCHEME_MAPPINGS)


@pytest.fixture
def project_issue_type_screen_schemes():
    """Sample project to issue type screen scheme mappings."""
    import copy
    return copy.deepcopy(PROJECT_ISSUE_TYPE_SCREEN_SCHEMES)


@pytest.fixture
def empty_screens_response():
    """Empty screens response for testing."""
    import copy
    return copy.deepcopy(EMPTY_SCREENS_RESPONSE)


@pytest.fixture
def empty_screen_schemes_response():
    """Empty screen schemes response for testing."""
    import copy
    return copy.deepcopy(EMPTY_SCREEN_SCHEMES_RESPONSE)


@pytest.fixture
def empty_issue_type_screen_schemes_response():
    """Empty issue type screen schemes response for testing."""
    import copy
    return copy.deepcopy(EMPTY_ISSUE_TYPE_SCREEN_SCHEMES_RESPONSE)


@pytest.fixture
def screens_page_1():
    """First page of paginated screens."""
    import copy
    return copy.deepcopy(SCREENS_PAGE_1)


@pytest.fixture
def screens_page_2():
    """Second page of paginated screens."""
    import copy
    return copy.deepcopy(SCREENS_PAGE_2)


@pytest.fixture
def screens_page_3():
    """Third page of paginated screens."""
    import copy
    return copy.deepcopy(SCREENS_PAGE_3)


@pytest.fixture
def project_issue_types():
    """Sample project issue types."""
    import copy
    return copy.deepcopy(PROJECT_ISSUE_TYPES)


@pytest.fixture
def sample_project():
    """Sample project for testing."""
    import copy
    return copy.deepcopy(SAMPLE_PROJECT)


# ========== Permission Scheme Fixtures ==========

@pytest.fixture
def permission_schemes_response():
    """Sample JIRA API response for permission schemes list."""
    import copy
    return copy.deepcopy(PERMISSION_SCHEMES_RESPONSE)


@pytest.fixture
def permission_scheme_detail():
    """Sample JIRA API response for single permission scheme with grants."""
    import copy
    return copy.deepcopy(PERMISSION_SCHEME_DETAIL_RESPONSE)


@pytest.fixture
def minimal_permission_scheme():
    """Sample permission scheme with minimal grants."""
    import copy
    return copy.deepcopy(MINIMAL_SCHEME_RESPONSE)


@pytest.fixture
def created_permission_scheme():
    """Sample JIRA API response for newly created permission scheme."""
    import copy
    return copy.deepcopy(PERMISSION_CREATED_SCHEME_RESPONSE)


@pytest.fixture
def created_scheme_with_grants():
    """Sample created scheme with initial grants."""
    import copy
    return copy.deepcopy(CREATED_SCHEME_WITH_GRANTS_RESPONSE)


@pytest.fixture
def updated_permission_scheme():
    """Sample JIRA API response for updated permission scheme."""
    import copy
    return copy.deepcopy(UPDATED_SCHEME_RESPONSE)


@pytest.fixture
def permission_grants():
    """Sample permission grants response."""
    import copy
    return copy.deepcopy(PERMISSION_GRANTS_RESPONSE)


@pytest.fixture
def created_permission_grant():
    """Sample JIRA API response for created permission grant."""
    import copy
    return copy.deepcopy(CREATED_GRANT_RESPONSE)


@pytest.fixture
def all_permissions():
    """Sample JIRA API response for all available permissions."""
    import copy
    return copy.deepcopy(ALL_PERMISSIONS_RESPONSE)


@pytest.fixture
def project_permission_scheme():
    """Sample JIRA API response for project's permission scheme."""
    import copy
    return copy.deepcopy(PROJECT_PERMISSION_SCHEME_RESPONSE)


@pytest.fixture
def project_roles():
    """Sample JIRA API response for project roles."""
    import copy
    return copy.deepcopy(PROJECT_ROLES_RESPONSE)


@pytest.fixture
def empty_permission_schemes():
    """Sample empty permission schemes response."""
    import copy
    return copy.deepcopy(EMPTY_SCHEMES_RESPONSE)


# ========== Workflow Management Fixtures ==========

@pytest.fixture
def workflows_response():
    """Sample JIRA API response for workflows list."""
    import copy
    return copy.deepcopy(WORKFLOWS_RESPONSE)


@pytest.fixture
def software_workflow():
    """Sample Software Development Workflow with full details."""
    import copy
    return copy.deepcopy(SOFTWARE_WORKFLOW)


@pytest.fixture
def bug_workflow():
    """Sample Bug Workflow for testing."""
    import copy
    return copy.deepcopy(BUG_WORKFLOW)


@pytest.fixture
def workflow_search_response():
    """Sample workflow search response with transitions."""
    import copy
    return copy.deepcopy(WORKFLOW_SEARCH_RESPONSE)


@pytest.fixture
def workflow_schemes_list_response():
    """Sample workflow schemes list response."""
    import copy
    return copy.deepcopy(WORKFLOW_SCHEMES_LIST_RESPONSE)


@pytest.fixture
def software_scheme_detail():
    """Sample Software Development Scheme with full details."""
    import copy
    return copy.deepcopy(SOFTWARE_SCHEME_DETAIL)


@pytest.fixture
def project_workflow_scheme():
    """Sample project workflow scheme response."""
    import copy
    return copy.deepcopy(PROJECT_WORKFLOW_SCHEME)


@pytest.fixture
def assign_scheme_task_response():
    """Sample async task response for scheme assignment."""
    import copy
    return copy.deepcopy(ASSIGN_SCHEME_TASK_RESPONSE)


@pytest.fixture
def task_complete_response():
    """Sample completed task response."""
    import copy
    return copy.deepcopy(TASK_COMPLETE_RESPONSE)


@pytest.fixture
def task_in_progress_response():
    """Sample in-progress task response."""
    import copy
    return copy.deepcopy(TASK_IN_PROGRESS_RESPONSE)


@pytest.fixture
def task_failed_response():
    """Sample failed task response."""
    import copy
    return copy.deepcopy(TASK_FAILED_RESPONSE)


@pytest.fixture
def all_statuses_response():
    """Sample all statuses response."""
    import copy
    return copy.deepcopy(ALL_STATUSES_RESPONSE)


@pytest.fixture
def status_search_response():
    """Sample status search response."""
    import copy
    return copy.deepcopy(STATUS_SEARCH_RESPONSE)


@pytest.fixture
def single_status():
    """Sample single status object."""
    import copy
    return copy.deepcopy(SINGLE_STATUS)


@pytest.fixture
def issue_transitions():
    """Sample issue transitions response."""
    import copy
    return copy.deepcopy(ISSUE_TRANSITIONS)


@pytest.fixture
def issue_with_status():
    """Sample issue with status information."""
    import copy
    return copy.deepcopy(ISSUE_WITH_STATUS)


@pytest.fixture
def schemes_for_workflow():
    """Sample workflow schemes using a workflow."""
    import copy
    return copy.deepcopy(SCHEMES_FOR_WORKFLOW)


@pytest.fixture
def empty_workflows_response():
    """Empty workflows response for testing."""
    import copy
    return copy.deepcopy(EMPTY_WORKFLOWS_RESPONSE)


@pytest.fixture
def empty_workflow_schemes_response():
    """Empty workflow schemes response for testing."""
    import copy
    return copy.deepcopy(WORKFLOW_EMPTY_SCHEMES_RESPONSE)


@pytest.fixture
def empty_statuses_response():
    """Empty statuses response for testing."""
    import copy
    return copy.deepcopy(EMPTY_STATUSES_RESPONSE)


@pytest.fixture
def workflows_page_1():
    """First page of paginated workflows."""
    import copy
    return copy.deepcopy(WORKFLOWS_PAGE_1)


@pytest.fixture
def workflows_page_2():
    """Second page of paginated workflows."""
    import copy
    return copy.deepcopy(WORKFLOWS_PAGE_2)


@pytest.fixture
def task_failed_response():
    """Sample failed task response for workflow scheme assignment."""
    import copy
    return copy.deepcopy(TASK_FAILED_RESPONSE)


# ========== Permission Scheme Error Fixtures ==========

@pytest.fixture
def scheme_not_found_error():
    """Sample error response when permission scheme is not found."""
    import copy
    return copy.deepcopy(SCHEME_NOT_FOUND_ERROR)


@pytest.fixture
def scheme_in_use_error():
    """Sample error response when permission scheme is in use by projects."""
    import copy
    return copy.deepcopy(SCHEME_IN_USE_ERROR)


@pytest.fixture
def permission_denied_error():
    """Sample error response when user lacks permission to view schemes."""
    import copy
    return copy.deepcopy(PERMISSION_DENIED_ERROR)
