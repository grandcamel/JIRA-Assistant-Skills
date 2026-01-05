"""
Mock responses for issue type and issue type scheme tests.

Contains sample JIRA API responses used in unit tests.
"""

# Standard issue types list response
ISSUE_TYPES_RESPONSE = [
    {
        "id": "10000",
        "name": "Epic",
        "description": "A big user story that needs to be broken down",
        "iconUrl": "https://test.atlassian.net/images/icons/issuetypes/epic.svg",
        "subtask": False,
        "hierarchyLevel": 1,
        "avatarId": 10307,
        "entityId": "uuid-epic-1234",
        "scope": {"type": "GLOBAL"},
    },
    {
        "id": "10001",
        "name": "Story",
        "description": "A user story",
        "iconUrl": "https://test.atlassian.net/images/icons/issuetypes/story.svg",
        "subtask": False,
        "hierarchyLevel": 0,
        "avatarId": 10308,
    },
    {
        "id": "10002",
        "name": "Task",
        "description": "A task that needs to be done",
        "iconUrl": "https://test.atlassian.net/images/icons/issuetypes/task.svg",
        "subtask": False,
        "hierarchyLevel": 0,
        "avatarId": 10318,
    },
    {
        "id": "10003",
        "name": "Bug",
        "description": "A problem that impairs or prevents functionality",
        "iconUrl": "https://test.atlassian.net/images/icons/issuetypes/bug.svg",
        "subtask": False,
        "hierarchyLevel": 0,
        "avatarId": 10303,
    },
    {
        "id": "10004",
        "name": "Subtask",
        "description": "A subtask of another issue",
        "iconUrl": "https://test.atlassian.net/images/icons/issuetypes/subtask.svg",
        "subtask": True,
        "hierarchyLevel": -1,
        "avatarId": 10316,
    },
]

# Single issue type response
EPIC_RESPONSE = {
    "id": "10000",
    "name": "Epic",
    "description": "A big user story that needs to be broken down",
    "iconUrl": "https://test.atlassian.net/images/icons/issuetypes/epic.svg",
    "subtask": False,
    "hierarchyLevel": 1,
    "avatarId": 10307,
    "entityId": "uuid-epic-1234",
}

STORY_RESPONSE = {
    "id": "10001",
    "name": "Story",
    "description": "A user story",
    "iconUrl": "https://test.atlassian.net/images/icons/issuetypes/story.svg",
    "subtask": False,
    "hierarchyLevel": 0,
    "avatarId": 10308,
}

SUBTASK_RESPONSE = {
    "id": "10004",
    "name": "Subtask",
    "description": "A subtask of another issue",
    "iconUrl": "https://test.atlassian.net/images/icons/issuetypes/subtask.svg",
    "subtask": True,
    "hierarchyLevel": -1,
    "avatarId": 10316,
}

# Created issue type response
CREATED_ISSUE_TYPE_RESPONSE = {
    "id": "10005",
    "name": "Incident",
    "description": "An unplanned interruption or reduction in quality of service",
    "iconUrl": "https://test.atlassian.net/images/icons/issuetypes/story.svg",
    "subtask": False,
    "hierarchyLevel": 0,
    "avatarId": 10308,
}

# Project-scoped issue type
PROJECT_SCOPED_ISSUE_TYPE = {
    "id": "10100",
    "name": "Feature",
    "description": "A new feature",
    "iconUrl": "https://test.atlassian.net/images/icons/issuetypes/story.svg",
    "subtask": False,
    "hierarchyLevel": 0,
    "avatarId": 10308,
    "scope": {"type": "PROJECT", "project": {"id": "10000"}},
}

# Issue type schemes list response
ISSUE_TYPE_SCHEMES_RESPONSE = {
    "maxResults": 50,
    "startAt": 0,
    "total": 2,
    "isLast": True,
    "values": [
        {
            "id": "10000",
            "name": "Default Issue Type Scheme",
            "description": "Default issue type scheme is the list of global issue types. All newly created issue types will automatically be added to this scheme.",
            "defaultIssueTypeId": "10001",
            "isDefault": True,
        },
        {
            "id": "10001",
            "name": "Software Development Scheme",
            "description": "Issue types for software development projects",
            "defaultIssueTypeId": "10001",
            "isDefault": False,
        },
    ],
}

# Single issue type scheme response
DEFAULT_SCHEME_RESPONSE = {
    "id": "10000",
    "name": "Default Issue Type Scheme",
    "description": "Default issue type scheme is the list of global issue types.",
    "defaultIssueTypeId": "10001",
    "isDefault": True,
}

SOFTWARE_SCHEME_RESPONSE = {
    "id": "10001",
    "name": "Software Development Scheme",
    "description": "Issue types for software development projects",
    "defaultIssueTypeId": "10001",
    "isDefault": False,
}

# Created issue type scheme response
CREATED_SCHEME_RESPONSE = {"issueTypeSchemeId": "10002"}

# Issue type scheme for projects response
SCHEME_FOR_PROJECTS_RESPONSE = {
    "maxResults": 50,
    "startAt": 0,
    "total": 2,
    "isLast": True,
    "values": [
        {
            "issueTypeScheme": {
                "id": "10000",
                "name": "Default Issue Type Scheme",
                "description": "Default issue type scheme",
                "defaultIssueTypeId": "10001",
                "isDefault": True,
            },
            "projectIds": ["10000"],
        },
        {
            "issueTypeScheme": {
                "id": "10002",
                "name": "Kanban Issue Type Scheme",
                "description": "Kanban-specific issue types",
                "defaultIssueTypeId": "10002",
                "isDefault": False,
            },
            "projectIds": ["10001"],
        },
    ],
}

# Issue type scheme mappings response
SCHEME_MAPPINGS_RESPONSE = {
    "maxResults": 100,
    "startAt": 0,
    "total": 4,
    "isLast": True,
    "values": [
        {"issueTypeSchemeId": "10000", "issueTypeId": "10000"},
        {"issueTypeSchemeId": "10000", "issueTypeId": "10001"},
        {"issueTypeSchemeId": "10000", "issueTypeId": "10002"},
        {"issueTypeSchemeId": "10001", "issueTypeId": "10001"},
    ],
}

# Alternative issue types response (for deletion)
ALTERNATIVES_RESPONSE = [
    {"id": "10001", "name": "Story"},
    {"id": "10002", "name": "Task"},
]
