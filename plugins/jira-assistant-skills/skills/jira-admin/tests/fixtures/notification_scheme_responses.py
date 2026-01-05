"""
Sample notification scheme API responses for testing.

Contains fixture data that mimics JIRA notification scheme API responses.
"""

# Sample notification schemes list response
NOTIFICATION_SCHEMES_RESPONSE = {
    "values": [
        {
            "id": "10000",
            "self": "https://site.atlassian.net/rest/api/3/notificationscheme/10000",
            "name": "Default Notification Scheme",
            "description": "Standard notification setup for most projects",
        },
        {
            "id": "10001",
            "self": "https://site.atlassian.net/rest/api/3/notificationscheme/10001",
            "name": "Development Team Notifications",
            "description": "Custom notifications for dev team",
        },
        {
            "id": "10002",
            "self": "https://site.atlassian.net/rest/api/3/notificationscheme/10002",
            "name": "Customer Support Notifications",
            "description": "Support team notification rules",
        },
    ],
    "startAt": 0,
    "maxResults": 50,
    "total": 3,
    "isLast": True,
}

# Sample detailed notification scheme response
NOTIFICATION_SCHEME_DETAIL_RESPONSE = {
    "id": "10000",
    "self": "https://site.atlassian.net/rest/api/3/notificationscheme/10000",
    "name": "Default Notification Scheme",
    "description": "Standard notification setup for most projects",
    "notificationSchemeEvents": [
        {
            "event": {
                "id": "1",
                "name": "Issue created",
                "description": "This event is fired when an issue is created",
            },
            "notifications": [
                {"id": "10", "notificationType": "CurrentAssignee", "parameter": None},
                {"id": "11", "notificationType": "Reporter", "parameter": None},
                {
                    "id": "12",
                    "notificationType": "Group",
                    "parameter": "jira-administrators",
                },
            ],
        },
        {
            "event": {
                "id": "2",
                "name": "Issue updated",
                "description": "This event is fired when an issue is updated",
            },
            "notifications": [
                {"id": "13", "notificationType": "CurrentAssignee", "parameter": None},
                {"id": "14", "notificationType": "AllWatchers", "parameter": None},
            ],
        },
        {
            "event": {
                "id": "3",
                "name": "Issue assigned",
                "description": "This event is fired when an issue is assigned",
            },
            "notifications": [
                {"id": "15", "notificationType": "CurrentAssignee", "parameter": None},
                {"id": "16", "notificationType": "Reporter", "parameter": None},
            ],
        },
        {
            "event": {
                "id": "6",
                "name": "Issue commented",
                "description": "This event is fired when a comment is added",
            },
            "notifications": [
                {"id": "17", "notificationType": "CurrentAssignee", "parameter": None},
                {"id": "18", "notificationType": "AllWatchers", "parameter": None},
                {"id": "19", "notificationType": "Group", "parameter": "developers"},
            ],
        },
    ],
}

# Sample scheme with all notification types
NOTIFICATION_SCHEME_ALL_TYPES = {
    "id": "10005",
    "name": "Comprehensive Notifications",
    "description": "Scheme with all notification types",
    "notificationSchemeEvents": [
        {
            "event": {"id": "1", "name": "Issue created"},
            "notifications": [
                {"id": "100", "notificationType": "CurrentAssignee", "parameter": None},
                {"id": "101", "notificationType": "Reporter", "parameter": None},
                {"id": "102", "notificationType": "CurrentUser", "parameter": None},
                {"id": "103", "notificationType": "ProjectLead", "parameter": None},
                {"id": "104", "notificationType": "ComponentLead", "parameter": None},
                {
                    "id": "105",
                    "notificationType": "User",
                    "parameter": "5b10ac8d82e05b22cc7d4ef5",
                },
                {
                    "id": "106",
                    "notificationType": "Group",
                    "parameter": "jira-administrators",
                },
                {"id": "107", "notificationType": "ProjectRole", "parameter": "10002"},
                {"id": "108", "notificationType": "AllWatchers", "parameter": None},
            ],
        }
    ],
}

# Sample project-to-scheme mappings
PROJECT_MAPPINGS_RESPONSE = {
    "values": [
        {"projectId": "10000", "notificationSchemeId": "10000"},
        {"projectId": "10001", "notificationSchemeId": "10000"},
        {"projectId": "10002", "notificationSchemeId": "10001"},
    ],
    "startAt": 0,
    "maxResults": 50,
    "total": 3,
    "isLast": True,
}

# Sample create notification scheme response
CREATED_NOTIFICATION_SCHEME = {
    "id": "10100",
    "self": "https://site.atlassian.net/rest/api/3/notificationscheme/10100",
    "name": "New Project Notifications",
    "description": "Custom notifications for new project",
}

# Empty notification schemes response
EMPTY_NOTIFICATION_SCHEMES = {
    "values": [],
    "startAt": 0,
    "maxResults": 50,
    "total": 0,
    "isLast": True,
}

# Empty scheme (no events configured)
EMPTY_SCHEME = {
    "id": "10010",
    "name": "Empty Scheme",
    "description": "No events configured",
    "notificationSchemeEvents": [],
}

# Sample notification events
NOTIFICATION_EVENTS = [
    {"id": "1", "name": "Issue created", "description": "Issue is created"},
    {"id": "2", "name": "Issue updated", "description": "Issue is updated"},
    {"id": "3", "name": "Issue assigned", "description": "Issue is assigned"},
    {"id": "4", "name": "Issue resolved", "description": "Issue is resolved"},
    {"id": "5", "name": "Issue closed", "description": "Issue is closed"},
    {"id": "6", "name": "Issue commented", "description": "Comment is added"},
    {"id": "7", "name": "Issue reopened", "description": "Issue is reopened"},
    {"id": "8", "name": "Issue deleted", "description": "Issue is deleted"},
    {"id": "10", "name": "Work logged", "description": "Work is logged"},
]

# Valid recipient types
RECIPIENT_TYPES = [
    "CurrentAssignee",
    "Reporter",
    "CurrentUser",
    "ProjectLead",
    "ComponentLead",
    "User",
    "Group",
    "ProjectRole",
    "AllWatchers",
    "UserCustomField",
    "GroupCustomField",
]
