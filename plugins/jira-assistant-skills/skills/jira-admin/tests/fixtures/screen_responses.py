"""
Mock responses for Screen, Screen Scheme, and Issue Type Screen Scheme APIs.

These fixtures provide realistic API responses for testing screen management scripts.
"""

# ========== Screens API Responses ==========

SCREENS_RESPONSE = {
    "maxResults": 100,
    "startAt": 0,
    "total": 5,
    "isLast": True,
    "values": [
        {
            "id": 1,
            "name": "Default Screen",
            "description": "The default screen for all issue operations",
        },
        {
            "id": 2,
            "name": "Resolve Issue Screen",
            "description": "Screen shown when resolving issues",
        },
        {
            "id": 3,
            "name": "Workflow Screen",
            "description": "Screen for workflow transitions",
        },
        {
            "id": 10,
            "name": "Bug Create Screen",
            "description": "Custom screen for creating bugs",
            "scope": {"type": "PROJECT", "project": {"id": "10000"}},
        },
        {"id": 11, "name": "Epic Screen", "description": "Screen for epic issue types"},
    ],
}

DEFAULT_SCREEN = {
    "id": 1,
    "name": "Default Screen",
    "description": "The default screen for all issue operations",
}

BUG_CREATE_SCREEN = {
    "id": 10,
    "name": "Bug Create Screen",
    "description": "Custom screen for creating bugs",
    "scope": {"type": "PROJECT", "project": {"id": "10000"}},
}

EPIC_SCREEN = {
    "id": 11,
    "name": "Epic Screen",
    "description": "Screen for epic issue types",
}

# ========== Screen Tabs API Responses ==========

DEFAULT_SCREEN_TABS = [
    {"id": 10000, "name": "Field Tab"},
    {"id": 10001, "name": "Custom Fields"},
]

SINGLE_TAB = [{"id": 10000, "name": "Field Tab"}]

# ========== Screen Tab Fields API Responses ==========

FIELD_TAB_FIELDS = [
    {"id": "summary", "name": "Summary"},
    {"id": "issuetype", "name": "Issue Type"},
    {"id": "priority", "name": "Priority"},
    {"id": "description", "name": "Description"},
    {"id": "assignee", "name": "Assignee"},
    {"id": "reporter", "name": "Reporter"},
    {"id": "labels", "name": "Labels"},
]

CUSTOM_FIELDS_TAB_FIELDS = [
    {"id": "customfield_10016", "name": "Story Points"},
    {"id": "customfield_10014", "name": "Epic Link"},
]

ALL_SCREEN_FIELDS = FIELD_TAB_FIELDS + CUSTOM_FIELDS_TAB_FIELDS

AVAILABLE_FIELDS = [
    {"id": "customfield_10020", "name": "Sprint"},
    {"id": "customfield_10025", "name": "Severity"},
    {"id": "duedate", "name": "Due Date"},
    {"id": "timetracking", "name": "Time Tracking"},
]

ADDED_FIELD_RESPONSE = {"id": "customfield_10020", "name": "Sprint"}

# ========== Screen Schemes API Responses ==========

SCREEN_SCHEMES_RESPONSE = {
    "maxResults": 100,
    "startAt": 0,
    "total": 3,
    "isLast": True,
    "values": [
        {
            "id": 1,
            "name": "Default Screen Scheme",
            "description": "The default screen scheme",
            "screens": {"default": 1, "edit": 1, "view": 1, "create": 1},
        },
        {
            "id": 2,
            "name": "Bug Screen Scheme",
            "description": "Custom screen scheme for bugs",
            "screens": {"default": 2, "edit": 2, "view": 1},
        },
        {
            "id": 3,
            "name": "Software Development Scheme",
            "description": "Screens for software projects",
            "screens": {"default": 1, "edit": 3, "view": 1, "create": 1},
        },
    ],
}

DEFAULT_SCREEN_SCHEME = {
    "id": 1,
    "name": "Default Screen Scheme",
    "description": "The default screen scheme",
    "screens": {"default": 1, "edit": 1, "view": 1, "create": 1},
}

BUG_SCREEN_SCHEME = {
    "id": 2,
    "name": "Bug Screen Scheme",
    "description": "Custom screen scheme for bugs",
    "screens": {"default": 2, "edit": 2, "view": 1},
}

# ========== Issue Type Screen Schemes API Responses ==========

ISSUE_TYPE_SCREEN_SCHEMES_RESPONSE = {
    "maxResults": 100,
    "startAt": 0,
    "total": 3,
    "isLast": True,
    "values": [
        {
            "id": "10000",
            "name": "Default Issue Type Screen Scheme",
            "description": "The default issue type screen scheme",
        },
        {
            "id": "10001",
            "name": "Software Project Screen Scheme",
            "description": "Screen scheme for software projects",
        },
        {
            "id": "10002",
            "name": "Bug Tracking Screen Scheme",
            "description": "Screen scheme for bug tracking",
        },
    ],
}

DEFAULT_ISSUE_TYPE_SCREEN_SCHEME = {
    "id": "10000",
    "name": "Default Issue Type Screen Scheme",
    "description": "The default issue type screen scheme",
}

SOFTWARE_ISSUE_TYPE_SCREEN_SCHEME = {
    "id": "10001",
    "name": "Software Project Screen Scheme",
    "description": "Screen scheme for software projects",
}

# ========== Issue Type Screen Scheme Mappings Response ==========

ISSUE_TYPE_SCREEN_SCHEME_MAPPINGS = {
    "maxResults": 100,
    "startAt": 0,
    "total": 5,
    "isLast": True,
    "values": [
        {
            "issueTypeScreenSchemeId": "10000",
            "issueTypeId": "10001",  # Bug
            "screenSchemeId": "2",  # Bug Screen Scheme
        },
        {
            "issueTypeScreenSchemeId": "10000",
            "issueTypeId": "10002",  # Story
            "screenSchemeId": "1",  # Default Screen Scheme
        },
        {
            "issueTypeScreenSchemeId": "10000",
            "issueTypeId": "10003",  # Epic
            "screenSchemeId": "3",  # Epic Screen Scheme
        },
        {
            "issueTypeScreenSchemeId": "10000",
            "issueTypeId": "10004",  # Task
            "screenSchemeId": "1",  # Default Screen Scheme
        },
        {
            "issueTypeScreenSchemeId": "10000",
            "issueTypeId": "default",
            "screenSchemeId": "1",  # Default Screen Scheme
        },
    ],
}

# ========== Project Issue Type Screen Schemes Response ==========

PROJECT_ISSUE_TYPE_SCREEN_SCHEMES = {
    "maxResults": 100,
    "startAt": 0,
    "total": 2,
    "isLast": True,
    "values": [
        {
            "issueTypeScreenScheme": {
                "id": "10000",
                "name": "Default Issue Type Screen Scheme",
                "description": "The default issue type screen scheme",
            },
            "projectIds": ["10000", "10001", "10002"],
        },
        {
            "issueTypeScreenScheme": {
                "id": "10001",
                "name": "Software Project Screen Scheme",
                "description": "Screen scheme for software projects",
            },
            "projectIds": ["10003"],
        },
    ],
}

# ========== Empty Responses ==========

EMPTY_SCREENS_RESPONSE = {
    "maxResults": 100,
    "startAt": 0,
    "total": 0,
    "isLast": True,
    "values": [],
}

EMPTY_SCREEN_SCHEMES_RESPONSE = {
    "maxResults": 100,
    "startAt": 0,
    "total": 0,
    "isLast": True,
    "values": [],
}

EMPTY_ISSUE_TYPE_SCREEN_SCHEMES_RESPONSE = {
    "maxResults": 100,
    "startAt": 0,
    "total": 0,
    "isLast": True,
    "values": [],
}

# ========== Paginated Responses ==========

SCREENS_PAGE_1 = {
    "maxResults": 2,
    "startAt": 0,
    "total": 5,
    "isLast": False,
    "values": [
        {"id": 1, "name": "Default Screen", "description": "Default"},
        {"id": 2, "name": "Resolve Issue Screen", "description": "Resolve"},
    ],
}

SCREENS_PAGE_2 = {
    "maxResults": 2,
    "startAt": 2,
    "total": 5,
    "isLast": False,
    "values": [
        {"id": 3, "name": "Workflow Screen", "description": "Workflow"},
        {"id": 10, "name": "Bug Create Screen", "description": "Bugs"},
    ],
}

SCREENS_PAGE_3 = {
    "maxResults": 2,
    "startAt": 4,
    "total": 5,
    "isLast": True,
    "values": [{"id": 11, "name": "Epic Screen", "description": "Epic"}],
}

# ========== Issue Types for Project Screen Discovery ==========

PROJECT_ISSUE_TYPES = [
    {
        "id": "10001",
        "name": "Bug",
        "description": "A problem which impairs or prevents the functions of the product.",
        "subtask": False,
    },
    {"id": "10002", "name": "Story", "description": "A user story", "subtask": False},
    {
        "id": "10003",
        "name": "Epic",
        "description": "A big user story",
        "subtask": False,
    },
    {"id": "10004", "name": "Task", "description": "A task", "subtask": False},
]

# ========== Sample Project Response ==========

SAMPLE_PROJECT = {
    "id": "10000",
    "key": "PROJ",
    "name": "My Project",
    "description": "Sample project for testing",
    "projectTypeKey": "software",
}
