"""
Mock JIRA API responses for workflow management tests.

Contains sample workflow, workflow scheme, and status data
for unit testing workflow management scripts.
"""

# ========== Workflow Responses ==========

WORKFLOWS_RESPONSE = {
    "self": "https://test.atlassian.net/rest/api/3/workflow",
    "startAt": 0,
    "maxResults": 50,
    "total": 4,
    "isLast": True,
    "values": [
        {
            "id": {
                "name": "Software Development Workflow",
                "entityId": "c6c7e6b0-19c4-4516-9a47-93f76124d4d4"
            },
            "description": "Workflow for software development projects",
            "isDefault": False
        },
        {
            "id": {
                "name": "Bug Workflow",
                "entityId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            },
            "description": "Simplified workflow for bug tracking",
            "isDefault": False
        },
        {
            "id": {
                "name": "jira",
                "entityId": "builtin-default-workflow"
            },
            "description": "The default JIRA workflow",
            "isDefault": True
        },
        {
            "id": {
                "name": "Epic Workflow",
                "entityId": "d4e5f6a7-b8c9-0123-4567-890abcdef123"
            },
            "description": "Workflow for managing epics",
            "isDefault": False
        }
    ]
}

# Single workflow with full details
SOFTWARE_WORKFLOW = {
    "id": {
        "name": "Software Development Workflow",
        "entityId": "c6c7e6b0-19c4-4516-9a47-93f76124d4d4"
    },
    "description": "Workflow for software development projects",
    "version": {
        "versionNumber": 3,
        "id": "12345"
    },
    "scope": {
        "type": "GLOBAL",
        "project": None
    },
    "isDefault": False,
    "transitions": [
        {
            "id": "11",
            "name": "Start Progress",
            "description": "Move issue to In Progress",
            "from": ["10000"],
            "to": "10001",
            "type": "DIRECTED",
            "screen": None,
            "rules": {
                "conditions": [],
                "validators": [],
                "postFunctions": []
            }
        },
        {
            "id": "21",
            "name": "Send to Review",
            "description": "Send for code review",
            "from": ["10001"],
            "to": "10002",
            "type": "DIRECTED",
            "screen": None,
            "rules": {
                "conditions": [],
                "validators": [],
                "postFunctions": []
            }
        },
        {
            "id": "31",
            "name": "Approve",
            "description": "Approve code review",
            "from": ["10002"],
            "to": "10003",
            "type": "DIRECTED",
            "screen": None,
            "rules": {
                "conditions": [],
                "validators": [],
                "postFunctions": []
            }
        },
        {
            "id": "41",
            "name": "Complete",
            "description": "Mark as complete",
            "from": ["10003"],
            "to": "10004",
            "type": "DIRECTED",
            "screen": None,
            "rules": {
                "conditions": [],
                "validators": [],
                "postFunctions": []
            }
        },
        {
            "id": "51",
            "name": "Reopen",
            "description": "Reopen issue",
            "from": ["10004"],
            "to": "10000",
            "type": "DIRECTED",
            "screen": None,
            "rules": {
                "conditions": [],
                "validators": [],
                "postFunctions": []
            }
        }
    ],
    "statuses": [
        {
            "id": "10000",
            "name": "To Do",
            "statusCategory": "TODO",
            "statusReference": "1",
            "layout": {"x": 100, "y": 200}
        },
        {
            "id": "10001",
            "name": "In Progress",
            "statusCategory": "IN_PROGRESS",
            "statusReference": "3",
            "layout": {"x": 300, "y": 200}
        },
        {
            "id": "10002",
            "name": "Code Review",
            "statusCategory": "IN_PROGRESS",
            "statusReference": "10001",
            "layout": {"x": 500, "y": 200}
        },
        {
            "id": "10003",
            "name": "Testing",
            "statusCategory": "IN_PROGRESS",
            "statusReference": "10002",
            "layout": {"x": 700, "y": 200}
        },
        {
            "id": "10004",
            "name": "Done",
            "statusCategory": "DONE",
            "statusReference": "10003",
            "layout": {"x": 900, "y": 200}
        }
    ],
    "created": "2025-01-15T10:30:00.000+0000",
    "updated": "2025-11-20T14:45:00.000+0000"
}

BUG_WORKFLOW = {
    "id": {
        "name": "Bug Workflow",
        "entityId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    },
    "description": "Simplified workflow for bug tracking",
    "version": {
        "versionNumber": 1,
        "id": "12346"
    },
    "scope": {
        "type": "GLOBAL",
        "project": None
    },
    "isDefault": False,
    "transitions": [
        {
            "id": "11",
            "name": "Start Investigation",
            "from": ["1"],
            "to": "3",
            "type": "DIRECTED"
        },
        {
            "id": "21",
            "name": "Resolve",
            "from": ["3"],
            "to": "10001",
            "type": "DIRECTED"
        },
        {
            "id": "31",
            "name": "Close",
            "from": ["10001"],
            "to": "10002",
            "type": "DIRECTED"
        }
    ],
    "statuses": [
        {
            "id": "1",
            "name": "Open",
            "statusCategory": "TODO"
        },
        {
            "id": "3",
            "name": "In Progress",
            "statusCategory": "IN_PROGRESS"
        },
        {
            "id": "10001",
            "name": "Resolved",
            "statusCategory": "DONE"
        },
        {
            "id": "10002",
            "name": "Closed",
            "statusCategory": "DONE"
        }
    ]
}

WORKFLOW_SEARCH_RESPONSE = {
    "self": "https://test.atlassian.net/rest/api/3/workflow/search",
    "startAt": 0,
    "maxResults": 50,
    "total": 2,
    "isLast": True,
    "values": [
        SOFTWARE_WORKFLOW,
        BUG_WORKFLOW
    ]
}

# ========== Workflow Scheme Responses ==========

WORKFLOW_SCHEMES_RESPONSE = {
    "self": "https://test.atlassian.net/rest/api/3/workflowscheme",
    "startAt": 0,
    "maxResults": 50,
    "total": 3,
    "isLast": True,
    "values": [
        {
            "id": 10100,
            "name": "Software Development Scheme",
            "description": "Workflow scheme for software projects",
            "defaultWorkflow": "jira",
            "issueTypeMappings": {
                "10000": "Software Development Workflow",
                "10001": "Bug Workflow"
            },
            "draft": False,
            "self": "https://test.atlassian.net/rest/api/3/workflowscheme/10100"
        },
        {
            "id": 10101,
            "name": "Agile Development Scheme",
            "description": "Workflow scheme for agile teams",
            "defaultWorkflow": "jira",
            "issueTypeMappings": {
                "10002": "Epic Workflow"
            },
            "draft": False,
            "self": "https://test.atlassian.net/rest/api/3/workflowscheme/10101"
        },
        {
            "id": 10000,
            "name": "Default Workflow Scheme",
            "description": "The default workflow scheme",
            "defaultWorkflow": "jira",
            "issueTypeMappings": {},
            "draft": False,
            "self": "https://test.atlassian.net/rest/api/3/workflowscheme/10000"
        }
    ]
}

SOFTWARE_SCHEME_DETAIL = {
    "id": 10100,
    "name": "Software Development Scheme",
    "description": "Workflow scheme for software projects",
    "defaultWorkflow": "jira",
    "issueTypeMappings": {
        "10000": "Software Development Workflow",
        "10001": "Bug Workflow",
        "10002": "Epic Workflow"
    },
    "draft": False,
    "lastModified": "2025-11-15T09:20:00.000+0000",
    "lastModifiedUser": {
        "accountId": "557058:12345678-1234-1234-1234-123456789012",
        "displayName": "John Admin"
    },
    "issueTypes": {
        "10000": {
            "id": "10000",
            "name": "Story",
            "workflow": "Software Development Workflow"
        },
        "10001": {
            "id": "10001",
            "name": "Bug",
            "workflow": "Bug Workflow"
        },
        "10002": {
            "id": "10002",
            "name": "Epic",
            "workflow": "Epic Workflow"
        }
    },
    "self": "https://test.atlassian.net/rest/api/3/workflowscheme/10100"
}

PROJECT_WORKFLOW_SCHEME = {
    "workflowScheme": {
        "id": 10100,
        "name": "Software Development Scheme",
        "description": "Workflow scheme for software projects",
        "defaultWorkflow": "jira",
        "self": "https://test.atlassian.net/rest/api/3/workflowscheme/10100"
    }
}

ASSIGN_SCHEME_TASK_RESPONSE = {
    "taskId": "10050",
    "self": "https://test.atlassian.net/rest/api/3/task/10050",
    "status": "ENQUEUED",
    "message": "Workflow scheme assignment started"
}

TASK_COMPLETE_RESPONSE = {
    "taskId": "10050",
    "self": "https://test.atlassian.net/rest/api/3/task/10050",
    "status": "COMPLETE",
    "message": "Workflow scheme assigned successfully",
    "progress": 100
}

TASK_IN_PROGRESS_RESPONSE = {
    "taskId": "10050",
    "self": "https://test.atlassian.net/rest/api/3/task/10050",
    "status": "RUNNING",
    "message": "Migrating issues to new workflow",
    "progress": 45
}

TASK_FAILED_RESPONSE = {
    "taskId": "10050",
    "self": "https://test.atlassian.net/rest/api/3/task/10050",
    "status": "FAILED",
    "message": "Migration failed due to status mapping error",
    "progress": 45,
    "error": {
        "errorMessages": ["Status 'Old Status' not found in target workflow"],
        "errors": {}
    }
}

# ========== Status Responses ==========

ALL_STATUSES_RESPONSE = [
    {
        "id": "10000",
        "name": "To Do",
        "description": "Work that needs to be done",
        "iconUrl": "https://test.atlassian.net/images/icons/statuses/generic.png",
        "statusCategory": {
            "id": 2,
            "key": "new",
            "colorName": "blue-gray",
            "name": "To Do",
            "self": "https://test.atlassian.net/rest/api/3/statuscategory/2"
        },
        "scope": {
            "type": "GLOBAL",
            "project": None
        },
        "self": "https://test.atlassian.net/rest/api/3/status/10000"
    },
    {
        "id": "10001",
        "name": "In Progress",
        "description": "Work in progress",
        "iconUrl": "https://test.atlassian.net/images/icons/statuses/inprogress.png",
        "statusCategory": {
            "id": 4,
            "key": "indeterminate",
            "colorName": "yellow",
            "name": "In Progress",
            "self": "https://test.atlassian.net/rest/api/3/statuscategory/4"
        },
        "scope": {
            "type": "GLOBAL",
            "project": None
        },
        "self": "https://test.atlassian.net/rest/api/3/status/10001"
    },
    {
        "id": "10002",
        "name": "Code Review",
        "description": "Code is under review",
        "iconUrl": "https://test.atlassian.net/images/icons/statuses/inprogress.png",
        "statusCategory": {
            "id": 4,
            "key": "indeterminate",
            "colorName": "yellow",
            "name": "In Progress",
            "self": "https://test.atlassian.net/rest/api/3/statuscategory/4"
        },
        "scope": {
            "type": "GLOBAL",
            "project": None
        },
        "self": "https://test.atlassian.net/rest/api/3/status/10002"
    },
    {
        "id": "10003",
        "name": "Testing",
        "description": "Work is being tested",
        "iconUrl": "https://test.atlassian.net/images/icons/statuses/inprogress.png",
        "statusCategory": {
            "id": 4,
            "key": "indeterminate",
            "colorName": "yellow",
            "name": "In Progress",
            "self": "https://test.atlassian.net/rest/api/3/statuscategory/4"
        },
        "scope": {
            "type": "GLOBAL",
            "project": None
        },
        "self": "https://test.atlassian.net/rest/api/3/status/10003"
    },
    {
        "id": "10004",
        "name": "Done",
        "description": "Work is complete",
        "iconUrl": "https://test.atlassian.net/images/icons/statuses/closed.png",
        "statusCategory": {
            "id": 3,
            "key": "done",
            "colorName": "green",
            "name": "Done",
            "self": "https://test.atlassian.net/rest/api/3/statuscategory/3"
        },
        "scope": {
            "type": "GLOBAL",
            "project": None
        },
        "self": "https://test.atlassian.net/rest/api/3/status/10004"
    },
    {
        "id": "1",
        "name": "Open",
        "description": "New issue",
        "iconUrl": "https://test.atlassian.net/images/icons/statuses/open.png",
        "statusCategory": {
            "id": 2,
            "key": "new",
            "colorName": "blue-gray",
            "name": "To Do",
            "self": "https://test.atlassian.net/rest/api/3/statuscategory/2"
        },
        "scope": {
            "type": "GLOBAL",
            "project": None
        },
        "self": "https://test.atlassian.net/rest/api/3/status/1"
    },
    {
        "id": "3",
        "name": "In Progress",
        "description": "Issue is being worked on",
        "iconUrl": "https://test.atlassian.net/images/icons/statuses/inprogress.png",
        "statusCategory": {
            "id": 4,
            "key": "indeterminate",
            "colorName": "yellow",
            "name": "In Progress",
            "self": "https://test.atlassian.net/rest/api/3/statuscategory/4"
        },
        "scope": {
            "type": "GLOBAL",
            "project": None
        },
        "self": "https://test.atlassian.net/rest/api/3/status/3"
    }
]

STATUS_SEARCH_RESPONSE = {
    "self": "https://test.atlassian.net/rest/api/3/statuses/search",
    "startAt": 0,
    "maxResults": 200,
    "total": 5,
    "isLast": True,
    "values": ALL_STATUSES_RESPONSE[:5]
}

SINGLE_STATUS = {
    "id": "10000",
    "name": "To Do",
    "description": "Work that needs to be done",
    "iconUrl": "https://test.atlassian.net/images/icons/statuses/generic.png",
    "statusCategory": {
        "id": 2,
        "key": "new",
        "colorName": "blue-gray",
        "name": "To Do",
        "self": "https://test.atlassian.net/rest/api/3/statuscategory/2"
    },
    "scope": {
        "type": "GLOBAL",
        "project": None
    },
    "self": "https://test.atlassian.net/rest/api/3/status/10000"
}

# ========== Issue Workflow Responses ==========

ISSUE_TRANSITIONS = {
    "expand": "transitions",
    "transitions": [
        {
            "id": "11",
            "name": "Start Progress",
            "hasScreen": False,
            "isGlobal": False,
            "isInitial": False,
            "isAvailable": True,
            "isConditional": False,
            "isLooped": False,
            "to": {
                "self": "https://test.atlassian.net/rest/api/3/status/10001",
                "description": "Work in progress",
                "iconUrl": "https://test.atlassian.net/images/icons/statuses/inprogress.png",
                "name": "In Progress",
                "id": "10001",
                "statusCategory": {
                    "id": 4,
                    "key": "indeterminate",
                    "colorName": "yellow",
                    "name": "In Progress"
                }
            }
        },
        {
            "id": "51",
            "name": "Done",
            "hasScreen": False,
            "isGlobal": True,
            "isInitial": False,
            "isAvailable": True,
            "isConditional": False,
            "isLooped": False,
            "to": {
                "self": "https://test.atlassian.net/rest/api/3/status/10004",
                "description": "Work is complete",
                "iconUrl": "https://test.atlassian.net/images/icons/statuses/closed.png",
                "name": "Done",
                "id": "10004",
                "statusCategory": {
                    "id": 3,
                    "key": "done",
                    "colorName": "green",
                    "name": "Done"
                }
            }
        }
    ]
}

ISSUE_WITH_STATUS = {
    "key": "PROJ-123",
    "id": "10123",
    "fields": {
        "summary": "Test issue",
        "status": {
            "self": "https://test.atlassian.net/rest/api/3/status/10000",
            "description": "Work that needs to be done",
            "iconUrl": "https://test.atlassian.net/images/icons/statuses/generic.png",
            "name": "To Do",
            "id": "10000",
            "statusCategory": {
                "id": 2,
                "key": "new",
                "colorName": "blue-gray",
                "name": "To Do"
            }
        },
        "issuetype": {
            "self": "https://test.atlassian.net/rest/api/3/issuetype/10000",
            "id": "10000",
            "name": "Story",
            "subtask": False
        },
        "project": {
            "self": "https://test.atlassian.net/rest/api/3/project/10000",
            "id": "10000",
            "key": "PROJ",
            "name": "Test Project"
        }
    }
}

# ========== Workflow Schemes for Workflow ==========

SCHEMES_FOR_WORKFLOW = {
    "self": "https://test.atlassian.net/rest/api/3/workflow/c6c7e6b0-19c4-4516-9a47-93f76124d4d4/workflowSchemes",
    "startAt": 0,
    "maxResults": 50,
    "total": 2,
    "isLast": True,
    "values": [
        {
            "id": 10100,
            "name": "Software Development Scheme",
            "description": "Workflow scheme for software projects"
        },
        {
            "id": 10101,
            "name": "Agile Development Scheme",
            "description": "Workflow scheme for agile teams"
        }
    ]
}

# ========== Empty Response Variants ==========

EMPTY_WORKFLOWS_RESPONSE = {
    "self": "https://test.atlassian.net/rest/api/3/workflow",
    "startAt": 0,
    "maxResults": 50,
    "total": 0,
    "isLast": True,
    "values": []
}

EMPTY_SCHEMES_RESPONSE = {
    "self": "https://test.atlassian.net/rest/api/3/workflowscheme",
    "startAt": 0,
    "maxResults": 50,
    "total": 0,
    "isLast": True,
    "values": []
}

EMPTY_STATUSES_RESPONSE = []

# ========== Pagination Response Variants ==========

WORKFLOWS_PAGE_1 = {
    "self": "https://test.atlassian.net/rest/api/3/workflow",
    "startAt": 0,
    "maxResults": 2,
    "total": 4,
    "isLast": False,
    "values": WORKFLOWS_RESPONSE["values"][:2]
}

WORKFLOWS_PAGE_2 = {
    "self": "https://test.atlassian.net/rest/api/3/workflow",
    "startAt": 2,
    "maxResults": 2,
    "total": 4,
    "isLast": True,
    "values": WORKFLOWS_RESPONSE["values"][2:]
}
