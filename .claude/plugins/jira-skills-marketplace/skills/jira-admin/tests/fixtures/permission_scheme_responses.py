"""
Sample JIRA API responses for permission scheme operations.

These fixtures mirror actual JIRA API responses for testing.
"""

# Sample permission schemes list response
PERMISSION_SCHEMES_RESPONSE = {
    "permissionSchemes": [
        {
            "id": 10000,
            "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10000",
            "name": "Default Software Scheme",
            "description": "Default permission scheme for software projects"
        },
        {
            "id": 10001,
            "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10001",
            "name": "Internal Projects Scheme",
            "description": "Restricted scheme for internal projects"
        },
        {
            "id": 10050,
            "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10050",
            "name": "Custom Development Scheme",
            "description": "Permission scheme for development projects"
        }
    ]
}

# Sample single permission scheme with grants
PERMISSION_SCHEME_DETAIL_RESPONSE = {
    "expand": "permissions,user,group,projectRole",
    "id": 10000,
    "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10000",
    "name": "Default Software Scheme",
    "description": "Default permission scheme for software projects",
    "permissions": [
        {
            "id": 10100,
            "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10000/permission/10100",
            "holder": {
                "type": "anyone"
            },
            "permission": "BROWSE_PROJECTS"
        },
        {
            "id": 10101,
            "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10000/permission/10101",
            "holder": {
                "type": "group",
                "parameter": "jira-developers",
                "value": "ca85fac0-d974-40ca-a615-7af99c48d24f"
            },
            "permission": "CREATE_ISSUES"
        },
        {
            "id": 10102,
            "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10000/permission/10102",
            "holder": {
                "type": "group",
                "parameter": "jira-developers",
                "value": "ca85fac0-d974-40ca-a615-7af99c48d24f"
            },
            "permission": "EDIT_ISSUES"
        },
        {
            "id": 10103,
            "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10000/permission/10103",
            "holder": {
                "type": "projectRole",
                "parameter": "Developers",
                "value": "10360"
            },
            "permission": "EDIT_ISSUES"
        },
        {
            "id": 10104,
            "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10000/permission/10104",
            "holder": {
                "type": "group",
                "parameter": "jira-administrators",
                "value": "9f4b7d8e-1234-5678-90ab-cdef12345678"
            },
            "permission": "ADMINISTER_PROJECTS"
        },
        {
            "id": 10105,
            "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10000/permission/10105",
            "holder": {
                "type": "projectLead"
            },
            "permission": "ADMINISTER_PROJECTS"
        }
    ]
}

# Sample scheme with minimal grants
MINIMAL_SCHEME_RESPONSE = {
    "id": 10050,
    "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10050",
    "name": "Custom Development Scheme",
    "description": "Permission scheme for development projects",
    "permissions": [
        {
            "id": 10200,
            "holder": {
                "type": "anyone"
            },
            "permission": "BROWSE_PROJECTS"
        }
    ]
}

# Sample created scheme response
CREATED_SCHEME_RESPONSE = {
    "expand": "permissions",
    "id": 10100,
    "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10100",
    "name": "New Test Scheme",
    "description": "Test scheme created via API",
    "permissions": []
}

# Sample created scheme with grants
CREATED_SCHEME_WITH_GRANTS_RESPONSE = {
    "expand": "permissions",
    "id": 10101,
    "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10101",
    "name": "New Scheme with Grants",
    "description": "Test scheme with initial grants",
    "permissions": [
        {
            "id": 10300,
            "holder": {
                "type": "anyone"
            },
            "permission": "BROWSE_PROJECTS"
        },
        {
            "id": 10301,
            "holder": {
                "type": "group",
                "parameter": "jira-developers"
            },
            "permission": "CREATE_ISSUES"
        }
    ]
}

# Sample updated scheme response
UPDATED_SCHEME_RESPONSE = {
    "id": 10000,
    "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10000",
    "name": "Updated Scheme Name",
    "description": "Updated description",
    "permissions": []
}

# Sample permission grants response
PERMISSION_GRANTS_RESPONSE = {
    "permissions": [
        {
            "id": 10100,
            "holder": {
                "type": "anyone"
            },
            "permission": "BROWSE_PROJECTS"
        },
        {
            "id": 10101,
            "holder": {
                "type": "group",
                "parameter": "jira-developers"
            },
            "permission": "CREATE_ISSUES"
        }
    ]
}

# Sample created grant response
CREATED_GRANT_RESPONSE = {
    "id": 10500,
    "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10000/permission/10500",
    "holder": {
        "type": "group",
        "parameter": "jira-developers",
        "value": "ca85fac0-d974-40ca-a615-7af99c48d24f"
    },
    "permission": "LINK_ISSUES"
}

# Sample all permissions response
ALL_PERMISSIONS_RESPONSE = {
    "permissions": {
        "BROWSE_PROJECTS": {
            "key": "BROWSE_PROJECTS",
            "name": "Browse Projects",
            "type": "PROJECT",
            "description": "Ability to browse projects and the issues within them."
        },
        "CREATE_ISSUES": {
            "key": "CREATE_ISSUES",
            "name": "Create Issues",
            "type": "PROJECT",
            "description": "Ability to create issues."
        },
        "EDIT_ISSUES": {
            "key": "EDIT_ISSUES",
            "name": "Edit Issues",
            "type": "PROJECT",
            "description": "Ability to edit issues."
        },
        "DELETE_ISSUES": {
            "key": "DELETE_ISSUES",
            "name": "Delete Issues",
            "type": "PROJECT",
            "description": "Ability to delete issues."
        },
        "ASSIGN_ISSUES": {
            "key": "ASSIGN_ISSUES",
            "name": "Assign Issues",
            "type": "PROJECT",
            "description": "Ability to assign issues to other users."
        },
        "ASSIGNABLE_USER": {
            "key": "ASSIGNABLE_USER",
            "name": "Assignable User",
            "type": "PROJECT",
            "description": "Users with this permission may be assigned to issues."
        },
        "RESOLVE_ISSUES": {
            "key": "RESOLVE_ISSUES",
            "name": "Resolve Issues",
            "type": "PROJECT",
            "description": "Ability to resolve and reopen issues."
        },
        "CLOSE_ISSUES": {
            "key": "CLOSE_ISSUES",
            "name": "Close Issues",
            "type": "PROJECT",
            "description": "Ability to close issues."
        },
        "TRANSITION_ISSUES": {
            "key": "TRANSITION_ISSUES",
            "name": "Transition Issues",
            "type": "PROJECT",
            "description": "Ability to transition issues."
        },
        "MOVE_ISSUES": {
            "key": "MOVE_ISSUES",
            "name": "Move Issues",
            "type": "PROJECT",
            "description": "Ability to move issues between projects."
        },
        "LINK_ISSUES": {
            "key": "LINK_ISSUES",
            "name": "Link Issues",
            "type": "PROJECT",
            "description": "Ability to link issues together."
        },
        "ADD_COMMENTS": {
            "key": "ADD_COMMENTS",
            "name": "Add Comments",
            "type": "PROJECT",
            "description": "Ability to add comments to issues."
        },
        "EDIT_ALL_COMMENTS": {
            "key": "EDIT_ALL_COMMENTS",
            "name": "Edit All Comments",
            "type": "PROJECT",
            "description": "Ability to edit any comments on issues."
        },
        "EDIT_OWN_COMMENTS": {
            "key": "EDIT_OWN_COMMENTS",
            "name": "Edit Own Comments",
            "type": "PROJECT",
            "description": "Ability to edit own comments on issues."
        },
        "DELETE_ALL_COMMENTS": {
            "key": "DELETE_ALL_COMMENTS",
            "name": "Delete All Comments",
            "type": "PROJECT",
            "description": "Ability to delete any comments."
        },
        "DELETE_OWN_COMMENTS": {
            "key": "DELETE_OWN_COMMENTS",
            "name": "Delete Own Comments",
            "type": "PROJECT",
            "description": "Ability to delete own comments."
        },
        "CREATE_ATTACHMENTS": {
            "key": "CREATE_ATTACHMENTS",
            "name": "Create Attachments",
            "type": "PROJECT",
            "description": "Ability to create attachments."
        },
        "DELETE_ALL_ATTACHMENTS": {
            "key": "DELETE_ALL_ATTACHMENTS",
            "name": "Delete All Attachments",
            "type": "PROJECT",
            "description": "Ability to delete any attachments."
        },
        "DELETE_OWN_ATTACHMENTS": {
            "key": "DELETE_OWN_ATTACHMENTS",
            "name": "Delete Own Attachments",
            "type": "PROJECT",
            "description": "Ability to delete own attachments."
        },
        "WORK_ON_ISSUES": {
            "key": "WORK_ON_ISSUES",
            "name": "Work On Issues",
            "type": "PROJECT",
            "description": "Ability to log work on issues."
        },
        "ADMINISTER_PROJECTS": {
            "key": "ADMINISTER_PROJECTS",
            "name": "Administer Projects",
            "type": "PROJECT",
            "description": "Ability to administer a project in Jira."
        },
        "MANAGE_SPRINTS": {
            "key": "MANAGE_SPRINTS",
            "name": "Manage Sprints",
            "type": "PROJECT",
            "description": "Ability to manage sprints."
        },
        "MANAGE_WATCHERS": {
            "key": "MANAGE_WATCHERS",
            "name": "Manage Watchers",
            "type": "PROJECT",
            "description": "Ability to manage the watchers of an issue."
        },
        "VIEW_DEV_TOOLS": {
            "key": "VIEW_DEV_TOOLS",
            "name": "View Development Tools",
            "type": "PROJECT",
            "description": "Ability to view development tools on issues."
        },
        "MODIFY_REPORTER": {
            "key": "MODIFY_REPORTER",
            "name": "Modify Reporter",
            "type": "PROJECT",
            "description": "Ability to change the reporter of issues."
        },
        "VIEW_VOTERS_AND_WATCHERS": {
            "key": "VIEW_VOTERS_AND_WATCHERS",
            "name": "View Voters and Watchers",
            "type": "PROJECT",
            "description": "Ability to view voters and watchers on issues."
        },
        "SCHEDULE_ISSUES": {
            "key": "SCHEDULE_ISSUES",
            "name": "Schedule Issues",
            "type": "PROJECT",
            "description": "Ability to schedule issues (set due date)."
        },
        "SET_ISSUE_SECURITY": {
            "key": "SET_ISSUE_SECURITY",
            "name": "Set Issue Security",
            "type": "PROJECT",
            "description": "Ability to set issue security level."
        },
        "ADMINISTER": {
            "key": "ADMINISTER",
            "name": "Administer Jira",
            "type": "GLOBAL",
            "description": "Ability to perform most administration functions."
        }
    }
}

# Sample project permission scheme response
PROJECT_PERMISSION_SCHEME_RESPONSE = {
    "id": 10000,
    "self": "https://test.atlassian.net/rest/api/3/permissionscheme/10000",
    "name": "Default Software Scheme",
    "description": "Default permission scheme for software projects"
}

# Sample project roles response
PROJECT_ROLES_RESPONSE = [
    {
        "self": "https://test.atlassian.net/rest/api/3/role/10002",
        "name": "Administrators",
        "id": 10002,
        "description": "A project role that represents administrators"
    },
    {
        "self": "https://test.atlassian.net/rest/api/3/role/10001",
        "name": "Developers",
        "id": 10001,
        "description": "A project role that represents developers"
    },
    {
        "self": "https://test.atlassian.net/rest/api/3/role/10000",
        "name": "Users",
        "id": 10000,
        "description": "A project role that represents general users"
    }
]

# Sample projects list for scheme assignment
PROJECTS_LIST_RESPONSE = {
    "values": [
        {
            "id": "10000",
            "key": "PROJ",
            "name": "Test Project"
        },
        {
            "id": "10001",
            "key": "DEV",
            "name": "Development Project"
        },
        {
            "id": "10002",
            "key": "QA",
            "name": "QA Project"
        }
    ],
    "isLast": True
}

# Empty scheme list response
EMPTY_SCHEMES_RESPONSE = {
    "permissionSchemes": []
}

# Error responses
SCHEME_NOT_FOUND_ERROR = {
    "errorMessages": ["Permission scheme not found: 99999"],
    "errors": {}
}

SCHEME_IN_USE_ERROR = {
    "errorMessages": ["The permission scheme cannot be deleted because it is used by one or more projects."],
    "errors": {}
}

PERMISSION_DENIED_ERROR = {
    "errorMessages": ["You do not have permission to view permission schemes."],
    "errors": {}
}

INVALID_HOLDER_ERROR = {
    "errorMessages": ["Invalid holder: group 'nonexistent-group' does not exist"],
    "errors": {}
}
