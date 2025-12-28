# Time Tracking Permission Matrix

Quick reference for JIRA time tracking permissions.

---

## Permission by Role

| Permission | Developer | Team Lead | Manager | Admin |
|------------|-----------|-----------|---------|-------|
| View worklogs on visible issues | Yes | Yes | Yes | Yes |
| Log time to assigned issues | Yes | Yes | Yes | Yes |
| Log time to any issue | No | Yes | Yes | Yes |
| Edit own worklogs | Yes | Yes | Yes | Yes |
| Delete own worklogs | Yes | Yes | Yes | Yes |
| Edit all worklogs | No | Yes | Yes | Yes |
| Delete all worklogs | No | No | Yes | Yes |
| Configure time tracking | No | No | No | Yes |

## Permission Descriptions

| Permission | Technical Name | Description |
|------------|----------------|-------------|
| **Work on Issues** | WORK_ISSUE | Log time to issues (requires assignment or broader permission) |
| **Edit Own Worklogs** | WORKLOG_EDIT_OWN | Modify worklogs you created |
| **Delete Own Worklogs** | WORKLOG_DELETE_OWN | Remove worklogs you created |
| **Edit All Worklogs** | WORKLOG_EDIT_ALL | Modify any user's worklogs |
| **Delete All Worklogs** | WORKLOG_DELETE_ALL | Remove any user's worklogs |

## Standard Permissions

**What you can do with standard (developer) permissions:**
- Log time to issues assigned to you
- Edit your own worklogs (within any time window configured)
- Delete your own worklogs
- View all worklogs on issues you can see

**What requires elevated permissions:**
- Edit other users' worklogs (Edit All Worklogs)
- Delete other users' worklogs (Delete All Worklogs)
- Log time to issues not assigned to you (depends on scheme)
- Change time tracking settings (JIRA Admin)

## Configuration Location

```
JIRA Admin Settings:
  Settings > Issues > Permission Schemes > [Your Scheme]
    > Time Tracking Permissions
```

## Recommended Permission Scheme

| Role | Permissions |
|------|-------------|
| Developers | Work on Issues, Edit Own, Delete Own |
| Team Leads | + Edit All Worklogs |
| Managers | + Delete All Worklogs |
| Admins | Full access + Configuration |

## Common Permission Issues

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "You do not have permission to log work" | Missing Work on Issues | Contact admin to add permission |
| "You cannot edit this worklog" | Not your worklog + missing Edit All | Request Edit All or ask owner |
| "You cannot delete this worklog" | Not your worklog + missing Delete All | Request Delete All or ask owner |
| "Time tracking is disabled" | Project-level setting | Enable in Project Settings > Features |

---

**Back to:** [SKILL.md](../../SKILL.md) | [Team Policies](../team-policies.md)
