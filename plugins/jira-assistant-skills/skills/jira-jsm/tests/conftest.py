"""
Shared pytest fixtures for jira-jsm skill tests.

Provides mock JIRA Service Management API responses and client fixtures
for testing JSM functionality without hitting real JIRA instance.

Note: Common markers (unit, integration, jsm, jsm_*) are defined in the root pytest.ini.
"""

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
    """Mock JiraClient for testing JSM without API calls."""
    client = Mock()
    client.base_url = "https://test.atlassian.net"
    client.email = "test@example.com"
    client.close = Mock()

    # Add context manager support
    client.__enter__ = Mock(return_value=client)
    client.__exit__ = Mock(return_value=False)

    # Mock service desk methods
    client.get_service_desks.return_value = {
        "size": 3,
        "start": 0,
        "limit": 50,
        "isLastPage": True,
        "values": [
            {
                "id": "1",
                "projectId": "10000",
                "projectName": "IT Service Desk",
                "projectKey": "ITS",
            },
            {
                "id": "2",
                "projectId": "10001",
                "projectName": "HR Service Desk",
                "projectKey": "HR",
            },
            {
                "id": "3",
                "projectId": "10002",
                "projectName": "Facilities",
                "projectKey": "FAC",
            },
        ],
    }

    client.get_service_desk.return_value = {
        "id": "1",
        "projectId": "10000",
        "projectName": "IT Service Desk",
        "projectKey": "ITS",
    }

    client.get_request_types.return_value = {
        "size": 2,
        "start": 0,
        "limit": 50,
        "isLastPage": True,
        "values": [
            {
                "id": "25",
                "name": "Get IT help",
                "description": "Request help from your IT team",
                "issueTypeId": "10001",
            },
            {
                "id": "26",
                "name": "Report incident",
                "description": "Report a system problem",
                "issueTypeId": "10002",
            },
        ],
    }

    client.get_request_type.return_value = {
        "id": "25",
        "name": "Get IT help",
        "description": "Request help from your IT team",
        "helpText": "Please provide detailed information",
        "issueTypeId": "10001",
        "serviceDeskId": "1",
    }

    client.get_request_type_fields.return_value = {
        "requestTypeFields": [
            {
                "fieldId": "summary",
                "name": "Summary",
                "description": "Brief description",
                "required": True,
                "jiraSchema": {"type": "string"},
            },
            {
                "fieldId": "description",
                "name": "Description",
                "description": "Detailed description",
                "required": False,
                "jiraSchema": {"type": "string"},
            },
        ],
        "canRaiseOnBehalfOf": False,
        "canAddRequestParticipants": True,
    }

    client.create_service_desk.return_value = {
        "id": "5",
        "projectId": "10005",
        "projectName": "New Service Desk",
        "projectKey": "NSD",
    }

    return client


@pytest.fixture
def sample_customer_response():
    """Sample JSM API response for a customer."""
    return {
        "accountId": "5b10ac8d82e05b22cc7d4ef5",
        "name": "John Customer",
        "emailAddress": "john@example.com",
        "displayName": "John Customer",
        "active": True,
        "timeZone": "America/New_York",
        "_links": {
            "jiraRest": "https://test.atlassian.net/rest/api/2/user?accountId=5b10ac8d82e05b22cc7d4ef5",
            "self": "https://test.atlassian.net/rest/servicedeskapi/customer/5b10ac8d82e05b22cc7d4ef5",
        },
    }


@pytest.fixture
def sample_customers_list_response():
    """Sample JSM API response for listing customers."""
    return {
        "size": 3,
        "start": 0,
        "limit": 50,
        "isLastPage": True,
        "_links": {
            "base": "https://test.atlassian.net/rest/servicedeskapi",
            "context": "",
            "self": "https://test.atlassian.net/rest/servicedeskapi/servicedesk/1/customer",
        },
        "values": [
            {
                "accountId": "5b10ac8d82e05b22cc7d4ef5",
                "name": "John Customer",
                "emailAddress": "john@example.com",
                "displayName": "John Customer",
                "active": True,
            },
            {
                "accountId": "5b109f2e9729b51b54dc274d",
                "name": "Jane Smith",
                "emailAddress": "jane@example.com",
                "displayName": "Jane Smith",
                "active": True,
            },
            {
                "accountId": "5b108c2e9729b51b54dc2751",
                "name": "Bob Johnson",
                "emailAddress": "bob@example.com",
                "displayName": "Bob Johnson",
                "active": False,
            },
        ],
    }


@pytest.fixture
def sample_request_response():
    """Sample JSM API response for a created request."""
    return {
        "issueId": "10010",
        "issueKey": "SD-101",
        "requestTypeId": "10",
        "requestType": {
            "id": "10",
            "name": "Incident",
            "description": "Report an incident",
        },
        "serviceDeskId": "1",
        "createdDate": {
            "iso8601": "2025-01-15T10:30:00+0000",
            "epochMillis": 1736936400000,
            "friendly": "Today 10:30 AM",
        },
        "reporter": {
            "accountId": "557058:abc123",
            "displayName": "Alice Reporter",
            "emailAddress": "alice@example.com",
        },
        "requestFieldValues": [
            {"fieldId": "summary", "label": "Summary", "value": "Email not working"},
            {
                "fieldId": "description",
                "label": "Description",
                "value": "Cannot send emails since this morning",
            },
        ],
        "currentStatus": {
            "status": "Waiting for support",
            "statusCategory": "NEW",
            "statusDate": {
                "iso8601": "2025-01-15T10:30:00+0000",
                "epochMillis": 1736936400000,
            },
        },
        "_links": {
            "self": "https://test.atlassian.net/rest/servicedeskapi/request/SD-101",
            "web": "https://test.atlassian.net/servicedesk/customer/portal/1/SD-101",
            "agent": "https://test.atlassian.net/browse/SD-101",
        },
    }


@pytest.fixture
def sample_request_with_sla():
    """Sample request response with SLA information."""
    return {
        "issueKey": "SD-101",
        "issueId": "10010",
        "requestTypeId": "10",
        "serviceDeskId": "1",
        "currentStatus": {"status": "In Progress", "statusCategory": "IN_PROGRESS"},
        "sla": {
            "values": [
                {
                    "id": "1",
                    "name": "Time to First Response",
                    "ongoingCycle": {
                        "breached": False,
                        "goalDuration": {"millis": 3600000},
                        "elapsedTime": {"millis": 900000},
                        "remainingTime": {"millis": 2700000},
                    },
                },
                {
                    "id": "2",
                    "name": "Time to Resolution",
                    "ongoingCycle": {
                        "breached": False,
                        "goalDuration": {"millis": 14400000},
                        "elapsedTime": {"millis": 12600000},
                        "remainingTime": {"millis": 1800000},
                    },
                },
            ]
        },
    }


@pytest.fixture
def sample_status_history():
    """Sample status history response."""
    return {
        "values": [
            {
                "status": "Open",
                "statusCategory": "NEW",
                "statusDate": {
                    "iso8601": "2025-01-15T10:30:00+0000",
                    "epochMillis": 1736936400000,
                    "friendly": "Today 10:30 AM",
                },
            },
            {
                "status": "In Progress",
                "statusCategory": "IN_PROGRESS",
                "statusDate": {
                    "iso8601": "2025-01-15T11:00:00+0000",
                    "epochMillis": 1736938200000,
                    "friendly": "Today 11:00 AM",
                },
            },
            {
                "status": "Resolved",
                "statusCategory": "DONE",
                "statusDate": {
                    "iso8601": "2025-01-15T14:30:00+0000",
                    "epochMillis": 1736950800000,
                    "friendly": "Today 2:30 PM",
                },
            },
        ]
    }


@pytest.fixture
def sample_transitions_response():
    """Sample transitions response."""
    return {
        "values": [
            {
                "id": "11",
                "name": "Start Progress",
                "to": {"id": "3", "name": "In Progress"},
            },
            {
                "id": "21",
                "name": "Waiting for Customer",
                "to": {"id": "10", "name": "Waiting for customer"},
            },
            {"id": "31", "name": "Resolve", "to": {"id": "5", "name": "Resolved"}},
        ]
    }


@pytest.fixture
def sample_comment_public():
    """Sample public JSM comment."""
    return {
        "id": "10001",
        "body": "Your issue has been resolved. Please verify the fix.",
        "public": True,
        "author": {
            "accountId": "5b10a2844c20165700ede21g",
            "displayName": "Alice Smith",
            "emailAddress": "alice@example.com",
        },
        "created": "2025-01-17T10:30:00.000+0000",
    }


@pytest.fixture
def sample_comment_internal():
    """Sample internal JSM comment."""
    return {
        "id": "10002",
        "body": "Escalating to Tier 2 - requires database access review.",
        "public": False,
        "author": {
            "accountId": "5b10a2844c20165700ede21h",
            "displayName": "Bob Jones",
            "emailAddress": "bob@example.com",
        },
        "created": "2025-01-17T11:00:00.000+0000",
    }


@pytest.fixture
def sample_comments_response():
    """Sample JSM comments list response."""
    return {
        "values": [
            {
                "id": "10001",
                "body": "Customer-visible update",
                "public": True,
                "author": {
                    "accountId": "5b10a2844c20165700ede21g",
                    "displayName": "Alice Smith",
                },
                "created": "2025-01-17T10:30:00.000+0000",
            },
            {
                "id": "10002",
                "body": "Internal note: escalate to Tier 2",
                "public": False,
                "author": {
                    "accountId": "5b10a2844c20165700ede21h",
                    "displayName": "Bob Jones",
                },
                "created": "2025-01-17T11:00:00.000+0000",
            },
            {
                "id": "10003",
                "body": "Working on this now",
                "public": True,
                "author": {
                    "accountId": "5b10a2844c20165700ede21g",
                    "displayName": "Alice Smith",
                },
                "created": "2025-01-17T09:00:00.000+0000",
            },
        ],
        "start": 0,
        "limit": 100,
        "isLastPage": True,
    }


@pytest.fixture
def sample_approval_pending():
    """Sample pending approval."""
    return {
        "id": "10050",
        "name": "Change Approval",
        "finalDecision": "pending",
        "canAnswerApproval": True,
        "approvers": [
            {"accountId": "5b10a2844c20165700ede21g", "displayName": "Manager Alice"}
        ],
        "createdDate": "2025-01-17T09:00:00.000+0000",
        "completedDate": None,
    }


@pytest.fixture
def sample_approval_approved():
    """Sample approved approval."""
    return {
        "id": "10051",
        "name": "Budget Approval",
        "finalDecision": "approve",
        "canAnswerApproval": False,
        "approvers": [
            {"accountId": "5b10a2844c20165700ede21h", "displayName": "Finance Manager"}
        ],
        "createdDate": "2025-01-17T08:00:00.000+0000",
        "completedDate": "2025-01-17T10:30:00.000+0000",
    }


@pytest.fixture
def sample_approvals_response():
    """Sample JSM approvals list response."""
    return {
        "values": [
            {
                "id": "10050",
                "name": "Change Approval",
                "finalDecision": "pending",
                "canAnswerApproval": True,
                "approvers": [
                    {
                        "accountId": "5b10a2844c20165700ede21g",
                        "displayName": "Manager Alice",
                    }
                ],
                "createdDate": "2025-01-17T09:00:00.000+0000",
                "completedDate": None,
            },
            {
                "id": "10051",
                "name": "Security Review",
                "finalDecision": "pending",
                "canAnswerApproval": False,
                "approvers": [
                    {
                        "accountId": "5b10a2844c20165700ede21h",
                        "displayName": "Security Team",
                    }
                ],
                "createdDate": "2025-01-17T09:00:00.000+0000",
                "completedDate": None,
            },
        ],
        "start": 0,
        "limit": 100,
        "isLastPage": True,
    }


# ==========================================
# Knowledge Base Fixtures (Phase 6)
# ==========================================


@pytest.fixture
def sample_kb_article():
    """Sample KB article response."""
    return {
        "id": "131073",
        "title": "How to reset your password",
        "excerpt": "If you forgot your <em>password</em>, follow these steps...",
        "source": {"type": "confluence", "pageId": "131073"},
        "_links": {"self": "https://test.atlassian.net/wiki/spaces/KB/pages/131073"},
    }


@pytest.fixture
def sample_kb_search_results():
    """Sample KB search results response."""
    return [
        {
            "id": "131073",
            "title": "How to reset your password",
            "excerpt": "If you forgot your <em>password</em>, follow these steps to reset it...",
            "source": {"type": "confluence", "pageId": "131073"},
            "_links": {
                "self": "https://test.atlassian.net/wiki/spaces/KB/pages/131073"
            },
        },
        {
            "id": "131074",
            "title": "Password policy requirements",
            "excerpt": "All <em>passwords</em> must meet the following security requirements...",
            "source": {"type": "confluence", "pageId": "131074"},
            "_links": {
                "self": "https://test.atlassian.net/wiki/spaces/KB/pages/131074"
            },
        },
        {
            "id": "131075",
            "title": "Troubleshooting login issues",
            "excerpt": "If you cannot log in, check your <em>password</em> and account status...",
            "source": {"type": "confluence", "pageId": "131075"},
            "_links": {
                "self": "https://test.atlassian.net/wiki/spaces/KB/pages/131075"
            },
        },
    ]


# ==========================================
# Assets/Insight Fixtures (Phase 6)
# ==========================================


@pytest.fixture
def sample_asset():
    """Sample asset object response."""
    return {
        "id": "10001",
        "objectKey": "ASSET-123",
        "label": "web-server-01",
        "objectType": {
            "id": "5",
            "name": "Server",
            "icon": {
                "id": "1",
                "name": "Server",
                "url16": "https://test.atlassian.net/icon16.png",
                "url48": "https://test.atlassian.net/icon48.png",
            },
        },
        "attributes": [
            {
                "id": "100",
                "objectTypeAttribute": {"id": "10", "name": "IP Address", "type": 0},
                "objectAttributeValues": [{"value": "192.168.1.100"}],
            },
            {
                "id": "101",
                "objectTypeAttribute": {"id": "11", "name": "Status", "type": 1},
                "objectAttributeValues": [{"value": "Active"}],
            },
            {
                "id": "102",
                "objectTypeAttribute": {"id": "12", "name": "Location", "type": 0},
                "objectAttributeValues": [{"value": "DC-1"}],
            },
        ],
        "_links": {"self": "/rest/insight/1.0/object/10001"},
    }


@pytest.fixture
def sample_assets_list():
    """Sample assets search results response."""
    return [
        {
            "id": "10001",
            "objectKey": "ASSET-123",
            "label": "web-server-01",
            "objectType": {"id": "5", "name": "Server"},
            "attributes": [
                {
                    "objectTypeAttribute": {"name": "IP Address"},
                    "objectAttributeValues": [{"value": "192.168.1.100"}],
                },
                {
                    "objectTypeAttribute": {"name": "Status"},
                    "objectAttributeValues": [{"value": "Active"}],
                },
            ],
        },
        {
            "id": "10002",
            "objectKey": "ASSET-124",
            "label": "web-server-02",
            "objectType": {"id": "5", "name": "Server"},
            "attributes": [
                {
                    "objectTypeAttribute": {"name": "IP Address"},
                    "objectAttributeValues": [{"value": "192.168.1.101"}],
                },
                {
                    "objectTypeAttribute": {"name": "Status"},
                    "objectAttributeValues": [{"value": "Active"}],
                },
            ],
        },
        {
            "id": "10003",
            "objectKey": "ASSET-125",
            "label": "db-server-01",
            "objectType": {"id": "6", "name": "Database"},
            "attributes": [
                {
                    "objectTypeAttribute": {"name": "IP Address"},
                    "objectAttributeValues": [{"value": "192.168.1.110"}],
                },
                {
                    "objectTypeAttribute": {"name": "Status"},
                    "objectAttributeValues": [{"value": "Active"}],
                },
            ],
        },
    ]


@pytest.fixture(autouse=True)
def mock_config_manager_all(mock_jira_client, monkeypatch):
    """
    Automatically mock config_manager.get_jira_client() for all tests.

    This prevents tests from trying to load actual credentials and
    ensures all tests use the mock client.

    Patches it in all script modules that import it.
    """
    # List of all script modules that use get_jira_client
    script_modules = [
        "create_request",
        "get_request",
        "get_request_status",
        "list_requests",
        "transition_request",
        "approve_request",
        "decline_request",
        "add_request_comment",
        "get_request_comments",
        "get_approvals",
        "list_pending_approvals",
    ]

    # Mock in each script module that imports get_jira_client
    for module_name in script_modules:
        try:
            monkeypatch.setattr(
                f"{module_name}.get_jira_client", lambda: mock_jira_client
            )
        except (AttributeError, ModuleNotFoundError):
            # Module not yet imported or doesn't use get_jira_client
            pass

    yield
