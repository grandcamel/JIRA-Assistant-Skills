# JIRA Field IDs, Event IDs, and Constants Reference

Reference guide for "magic numbers" and constants used in JIRA administration.

---

## Common Custom Field IDs

**Important:** Custom field IDs vary by JIRA instance! Use `get_config.py PROJ` to discover YOUR instance's IDs.

| Field | Common ID | Description | How to Find Yours |
|-------|-----------|-------------|--------------------|
| Story Points | `customfield_10016` | Agile estimation field | `get_config.py PROJ` |
| Epic Link | `customfield_10014` | Links issue to epic | Field discovery script |
| Epic Name | `customfield_10011` | Name shown on epic | Field discovery script |
| Epic Color | `customfield_10012` | Epic color coding | Field discovery script |
| Sprint | `customfield_10020` | Sprint assignment | `get_config.py PROJ` |
| Rank | `customfield_10019` | Backlog ordering | Field discovery script |
| Parent Link | `customfield_10015` | Parent issue relationship | Field discovery script |

### Discovering Your Instance's Field IDs

```bash
# View project configuration with field IDs
python get_config.py PROJ

# Use jira-fields skill for comprehensive discovery
python .claude/skills/jira-fields/scripts/list_fields.py --custom-only

# Get specific field details
python .claude/skills/jira-fields/scripts/get_field.py customfield_10016
```

---

## Notification Event IDs

| Event Name | Event ID | Trigger Key |
|------------|----------|-------------|
| Issue created | 1 | `jira.issue.event.trigger:created` |
| Issue updated | 2 | `jira.issue.event.trigger:updated` |
| Issue assigned | 3 | `jira.issue.event.trigger:assigned` |
| Issue resolved | 4 | `jira.issue.event.trigger:resolved` |
| Issue closed | 5 | `jira.issue.event.trigger:closed` |
| Issue commented | 6 | `jira.issue.event.trigger:commented` |
| Issue reopened | 7 | `jira.issue.event.trigger:reopened` |
| Issue deleted | 8 | `jira.issue.event.trigger:deleted` |
| Issue moved | 9 | `jira.issue.event.trigger:moved` |
| Work logged | 10 | `jira.issue.event.trigger:worklogged` |
| Work started | 11 | `jira.issue.event.trigger:workstarted` |
| Work stopped | 12 | `jira.issue.event.trigger:workstopped` |
| Generic event | 13 | Generic custom event |
| Issue comment edited | 14 | Comment modification |
| Issue comment deleted | 15 | Comment removal |
| Issue attachment added | 16 | File attached |
| Issue attachment deleted | 17 | File removed |

### Using Event IDs

```bash
# Add notification using event name (preferred)
python add_notification.py 10000 --event "Issue created" --notify Reporter

# Add notification using event ID (when name doesn't match)
python add_notification.py 10000 --event-id 1 --notify Reporter
```

---

## Permission Keys (Complete List)

### Project Permissions

| Key | Description | Common Holders |
|-----|-------------|----------------|
| `BROWSE_PROJECTS` | View projects and issues | projectRole:Users, anyone |
| `ADMINISTER_PROJECTS` | Administer projects | projectRole:Administrators |
| `CREATE_ISSUES` | Create issues | projectRole:Users |
| `EDIT_ISSUES` | Edit issues | currentAssignee, projectRole:Developers |
| `DELETE_ISSUES` | Delete issues | projectRole:Administrators |
| `ASSIGN_ISSUES` | Assign issues | projectRole:Developers |
| `ASSIGNABLE_USER` | Be assigned to issues | projectRole:Users |
| `RESOLVE_ISSUES` | Resolve/reopen issues | projectRole:Developers |
| `CLOSE_ISSUES` | Close issues | projectRole:Developers |
| `TRANSITION_ISSUES` | Transition issues | projectRole:Users |
| `MOVE_ISSUES` | Move issues between projects | projectRole:Administrators |
| `SCHEDULE_ISSUES` | Schedule issues (due dates) | projectRole:Developers |
| `SET_ISSUE_SECURITY` | Set issue security level | projectRole:Administrators |

### Comment Permissions

| Key | Description |
|-----|-------------|
| `ADD_COMMENTS` | Add comments |
| `EDIT_ALL_COMMENTS` | Edit all comments |
| `EDIT_OWN_COMMENTS` | Edit own comments |
| `DELETE_ALL_COMMENTS` | Delete all comments |
| `DELETE_OWN_COMMENTS` | Delete own comments |

### Attachment Permissions

| Key | Description |
|-----|-------------|
| `CREATE_ATTACHMENTS` | Create attachments |
| `DELETE_ALL_ATTACHMENTS` | Delete all attachments |
| `DELETE_OWN_ATTACHMENTS` | Delete own attachments |

### Time Tracking Permissions

| Key | Description |
|-----|-------------|
| `WORK_ON_ISSUES` | Log work on issues |
| `EDIT_ALL_WORKLOGS` | Edit all worklogs |
| `EDIT_OWN_WORKLOGS` | Edit own worklogs |
| `DELETE_ALL_WORKLOGS` | Delete all worklogs |
| `DELETE_OWN_WORKLOGS` | Delete own worklogs |

### Issue Link Permissions

| Key | Description |
|-----|-------------|
| `LINK_ISSUES` | Link issues |
| `MANAGE_WATCHERS` | Manage watchers |
| `VIEW_VOTERS_AND_WATCHERS` | View voters and watchers |
| `VIEW_READONLY_WORKFLOW` | View read-only workflow |

### Agile Permissions

| Key | Description |
|-----|-------------|
| `MANAGE_SPRINTS` | Manage sprints |
| `VIEW_DEV_TOOLS` | View development tools |

---

## Holder Types Reference

| Type | Format | Example | Description |
|------|--------|---------|-------------|
| `anyone` | `anyone` | `BROWSE_PROJECTS:anyone` | All users (logged in or anonymous) |
| `group` | `group:NAME` | `CREATE_ISSUES:group:jira-developers` | Members of JIRA group |
| `projectRole` | `projectRole:NAME` | `EDIT_ISSUES:projectRole:Developers` | Members of project role |
| `user` | `user:ACCOUNT_ID` | `ADMINISTER:user:5b10ac8d...` | Specific user |
| `projectLead` | `projectLead` | `ADMINISTER_PROJECTS:projectLead` | Project lead only |
| `reporter` | `reporter` | `EDIT_ISSUES:reporter` | Issue reporter |
| `currentAssignee` | `currentAssignee` | `EDIT_ISSUES:currentAssignee` | Current assignee |
| `applicationRole` | `applicationRole:KEY` | `BROWSE:applicationRole:jira-software` | Application role |

---

## Status Categories

| Category | Key | Color | Description |
|----------|-----|-------|-------------|
| TODO | `new` | Blue | Work not started |
| IN_PROGRESS | `indeterminate` | Yellow | Work in progress |
| DONE | `done` | Green | Work completed |

### Common Status IDs

| Status | Typical ID | Category |
|--------|------------|----------|
| Open | 1 | TODO |
| In Progress | 3 | IN_PROGRESS |
| Resolved | 5 | DONE |
| Closed | 6 | DONE |
| Reopened | 4 | TODO |
| To Do | 10000 | TODO |
| Done | 10001 | DONE |

**Note:** Status IDs vary by instance. Use `list_statuses.py` to find yours.

---

## Project Types

| Type Key | Description | License Required |
|----------|-------------|------------------|
| `software` | Jira Software projects | Jira Software |
| `business` | Jira Core/Work Management | Jira Core |
| `service_desk` | Jira Service Management | JSM |

---

## Project Templates

| Shortcut | Full Template Key | Description |
|----------|-------------------|-------------|
| `scrum` | `com.pyxis.greenhopper.jira:gh-scrum-template` | Scrum with sprints |
| `kanban` | `com.pyxis.greenhopper.jira:gh-kanban-template` | Kanban continuous flow |
| `basic` | `com.pyxis.greenhopper.jira:gh-simplified-basic` | Basic software |

---

## Issue Type Hierarchy Levels

| Level | Type | Description |
|-------|------|-------------|
| -1 | Subtask | Child of parent issue |
| 0 | Standard | Regular issue (Bug, Task, Story) |
| 1 | Epic | Container/grouping issue |

---

## Notification Recipient Types

| Type | Format | Description |
|------|--------|-------------|
| `CurrentAssignee` | `CurrentAssignee` | Currently assigned user |
| `Reporter` | `Reporter` | Issue creator |
| `CurrentUser` | `CurrentUser` | Action performer |
| `ProjectLead` | `ProjectLead` | Project lead |
| `ComponentLead` | `ComponentLead` | Component lead |
| `AllWatchers` | `AllWatchers` | All watchers |
| `Group` | `Group:name` | Group members |
| `ProjectRole` | `ProjectRole:id` | Role members |
| `User` | `User:accountId` | Specific user |

---

## Common API Endpoints Reference

### Core APIs

| Endpoint Pattern | Purpose |
|-----------------|---------|
| `/rest/api/3/project` | Project operations |
| `/rest/api/3/issuetype` | Issue type operations |
| `/rest/api/3/permissionscheme` | Permission schemes |
| `/rest/api/3/notificationscheme` | Notification schemes |
| `/rest/api/3/screens` | Screen operations |
| `/rest/api/3/workflow` | Workflow operations |
| `/rest/api/3/workflowscheme` | Workflow schemes |
| `/rest/api/3/user` | User operations |
| `/rest/api/3/group` | Group operations |
| `/rest/api/3/status` | Status operations |

### Automation API (Cloud Only)

| Endpoint Pattern | Purpose |
|-----------------|---------|
| `/gateway/api/automation/internal-api/jira/{cloudId}/pro/rest/GLOBAL/rules` | List rules |
| `/gateway/api/automation/internal-api/jira/{cloudId}/pro/rest/GLOBAL/rule/{id}` | Rule details |

---

## Finding Your Instance's Constants

```bash
# Discover custom field IDs
python get_config.py PROJ

# List all statuses with IDs
python list_statuses.py --output json

# List all permissions
python list_permissions.py

# List all issue types with IDs
python list_issue_types.py --format json

# Get notification event IDs
python get_notification_scheme.py 10000 --output json
```

---

## Notes

1. **IDs are instance-specific** - Always verify with discovery scripts
2. **Use names when possible** - Most scripts accept names instead of IDs
3. **Event IDs may vary** - Some instances have custom events
4. **Custom field prefixes** - All custom fields start with `customfield_`
5. **Account IDs for users** - GDPR requires account IDs, not usernames
