"""
Pytest fixtures for jira-search JQL and filter tests.

Note: Common markers (unit, integration, search) are defined in the root pytest.ini.
"""

import pytest

# mock_jira_client is provided by root conftest.py


@pytest.fixture
def sample_autocomplete_data():
    """Sample JQL autocomplete data response."""
    return {
        "visibleFieldNames": [
            {
                "value": "assignee",
                "displayName": "Assignee",
                "orderable": "true",
                "searchable": "true",
                "cfid": None,
                "operators": [
                    "=",
                    "!=",
                    "in",
                    "not in",
                    "is",
                    "is not",
                    "was",
                    "was in",
                    "was not",
                    "was not in",
                    "changed",
                ],
            },
            {
                "value": "status",
                "displayName": "Status",
                "orderable": "true",
                "searchable": "true",
                "cfid": None,
                "operators": [
                    "=",
                    "!=",
                    "in",
                    "not in",
                    "is",
                    "is not",
                    "was",
                    "was in",
                    "was not",
                    "was not in",
                    "changed",
                ],
            },
            {
                "value": "project",
                "displayName": "Project",
                "orderable": "false",
                "searchable": "true",
                "cfid": None,
                "operators": ["=", "!=", "in", "not in"],
            },
            {
                "value": "priority",
                "displayName": "Priority",
                "orderable": "true",
                "searchable": "true",
                "cfid": None,
                "operators": ["=", "!=", "in", "not in", "is", "is not"],
            },
            {
                "value": "summary",
                "displayName": "Summary",
                "orderable": "false",
                "searchable": "true",
                "cfid": None,
                "operators": ["~", "!~"],
            },
            {
                "value": "created",
                "displayName": "Created",
                "orderable": "true",
                "searchable": "true",
                "cfid": None,
                "operators": ["=", "!=", "<", ">", "<=", ">="],
            },
            {
                "value": "customfield_10016",
                "displayName": "Story Points",
                "orderable": "true",
                "searchable": "true",
                "cfid": "10016",
                "operators": ["=", "!=", "<", ">", "<=", ">=", "is", "is not"],
            },
        ],
        "visibleFunctionNames": [
            {
                "value": "currentUser()",
                "displayName": "currentUser()",
                "isList": "false",
                "types": ["com.atlassian.jira.user.ApplicationUser"],
            },
            {
                "value": "membersOf(group)",
                "displayName": "membersOf(group)",
                "isList": "true",
                "types": ["com.atlassian.jira.user.ApplicationUser"],
            },
            {
                "value": "startOfDay()",
                "displayName": "startOfDay()",
                "isList": "false",
                "types": ["java.util.Date"],
            },
            {
                "value": "startOfWeek()",
                "displayName": "startOfWeek()",
                "isList": "false",
                "types": ["java.util.Date"],
            },
            {
                "value": "endOfMonth()",
                "displayName": "endOfMonth()",
                "isList": "false",
                "types": ["java.util.Date"],
            },
            {
                "value": "now()",
                "displayName": "now()",
                "isList": "false",
                "types": ["java.util.Date"],
            },
        ],
        "jqlReservedWords": [
            "and",
            "or",
            "not",
            "empty",
            "null",
            "order",
            "by",
            "asc",
            "desc",
        ],
    }


@pytest.fixture
def sample_jql_suggestions():
    """Sample JQL field value suggestions."""
    return {
        "results": [
            {"value": "Open", "displayName": "Open"},
            {"value": "In Progress", "displayName": "In Progress"},
            {"value": "Code Review", "displayName": "Code Review"},
            {"value": "Blocked", "displayName": "Blocked"},
            {"value": "Done", "displayName": "Done"},
        ]
    }


@pytest.fixture
def sample_jql_parse_valid():
    """Sample valid JQL parse response."""
    return {
        "queries": [
            {
                "query": "project = PROJ AND status = Open",
                "structure": {
                    "where": {
                        "clauses": [
                            {
                                "field": {"name": "project"},
                                "operator": "=",
                                "operand": {"value": "PROJ"},
                            },
                            {
                                "field": {"name": "status"},
                                "operator": "=",
                                "operand": {"value": "Open"},
                            },
                        ]
                    }
                },
                "errors": [],
            }
        ]
    }


@pytest.fixture
def sample_jql_parse_invalid():
    """Sample invalid JQL parse response."""
    return {
        "queries": [
            {
                "query": "projct = PROJ AND statuss = Open",
                "errors": [
                    "Field 'projct' does not exist or you do not have permission to view it.",
                    "Field 'statuss' does not exist or you do not have permission to view it.",
                ],
            }
        ]
    }


@pytest.fixture
def sample_filter():
    """Sample filter response."""
    return {
        "id": "10042",
        "name": "My Bugs",
        "description": "All open bugs in the project",
        "owner": {
            "accountId": "5b10a2844c20165700ede21g",
            "displayName": "John Smith",
            "emailAddress": "john.smith@company.com",
        },
        "jql": "project = PROJ AND type = Bug AND status != Done",
        "viewUrl": "https://test.atlassian.net/issues/?filter=10042",
        "searchUrl": "https://test.atlassian.net/rest/api/3/search/jql?jql=project+%3D+PROJ+AND+type+%3D+Bug+AND+status+%21%3D+Done",
        "favourite": True,
        "favouritedCount": 5,
        "sharePermissions": [],
        "subscriptions": {
            "size": 0,
            "items": [],
            "max-results": 1000,
            "start-index": 0,
            "end-index": 0,
        },
    }


@pytest.fixture
def sample_filter_list():
    """Sample list of filters."""
    return [
        {
            "id": "10042",
            "name": "My Bugs",
            "jql": "project = PROJ AND type = Bug",
            "favourite": True,
            "owner": {"displayName": "John Smith"},
        },
        {
            "id": "10043",
            "name": "Sprint Issues",
            "jql": "sprint in openSprints()",
            "favourite": False,
            "owner": {"displayName": "John Smith"},
        },
        {
            "id": "10044",
            "name": "Team Dashboard",
            "jql": 'assignee in membersOf("developers")',
            "favourite": True,
            "owner": {"displayName": "John Smith"},
        },
    ]


@pytest.fixture
def sample_filter_search_response():
    """Sample filter search response."""
    return {
        "self": "https://test.atlassian.net/rest/api/3/filter/search?startAt=0&maxResults=50",
        "maxResults": 50,
        "startAt": 0,
        "total": 3,
        "isLast": True,
        "values": [
            {
                "id": "10042",
                "name": "My Bugs",
                "jql": "project = PROJ AND type = Bug",
                "favourite": True,
                "owner": {
                    "displayName": "John Smith",
                    "accountId": "5b10a2844c20165700ede21g",
                },
            },
            {
                "id": "10043",
                "name": "Sprint Issues",
                "jql": "sprint in openSprints()",
                "favourite": False,
                "owner": {
                    "displayName": "John Smith",
                    "accountId": "5b10a2844c20165700ede21g",
                },
            },
        ],
    }


@pytest.fixture
def sample_filter_permissions():
    """Sample filter share permissions."""
    return [
        {
            "id": 10001,
            "type": "project",
            "project": {"id": "10000", "key": "PROJ", "name": "Test Project"},
        },
        {
            "id": 10002,
            "type": "group",
            "group": {"groupId": "abc123", "name": "developers"},
        },
    ]


@pytest.fixture
def sample_filter_with_subscriptions():
    """Sample filter with subscriptions."""
    return {
        "id": "10042",
        "name": "My Bugs",
        "jql": "project = PROJ AND type = Bug",
        "favourite": True,
        "subscriptions": {
            "size": 2,
            "items": [
                {
                    "id": 789,
                    "user": {
                        "displayName": "Alice",
                        "emailAddress": "alice@company.com",
                    },
                },
                {
                    "id": 790,
                    "user": {"displayName": "Bob", "emailAddress": "bob@company.com"},
                },
            ],
        },
    }








