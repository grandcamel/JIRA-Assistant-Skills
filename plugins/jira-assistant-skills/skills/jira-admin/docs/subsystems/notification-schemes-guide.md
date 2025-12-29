# Notification Schemes Guide

Deep-dive reference for JIRA notification scheme management including creation, configuration, and event-recipient mappings.

---

## When to Use Notification Scheme Scripts

Use these scripts when you need to:
- List and inspect notification schemes across your JIRA instance
- View which events trigger notifications and who receives them
- Create new notification schemes for different project types
- Update notification scheme metadata (name, description)
- Add event-to-recipient notification mappings
- Remove notifications from schemes
- Delete unused notification schemes
- See which projects use a specific notification scheme

---

## Understanding Notification Schemes

### What are Notification Schemes?

Notification schemes define who receives email notifications when specific events occur on JIRA issues. They map events (issue created, assigned, commented, etc.) to recipients (assignees, reporters, watchers, groups, etc.).

### Key Concepts

- **Events:** System-defined triggers (e.g., "Issue Created", "Issue Assigned", "Issue Commented")
- **Recipients:** Notification targets (current assignee, reporter, watchers, groups, project roles)
- **Scheme:** Collection of event-to-recipient mappings
- **Project Association:** Each company-managed project uses one notification scheme

---

## Scripts Reference

| Script | Description |
|--------|-------------|
| `list_notification_schemes.py` | List all notification schemes with optional filtering and event counts |
| `get_notification_scheme.py` | Get detailed scheme info with event-to-recipient mappings |
| `create_notification_scheme.py` | Create a new notification scheme with optional initial events |
| `update_notification_scheme.py` | Update scheme name and/or description |
| `add_notification.py` | Add event-recipient notifications to a scheme |
| `remove_notification.py` | Remove a specific notification from a scheme |
| `delete_notification_scheme.py` | Delete a notification scheme (must not be in use) |

---

## Examples

### List and Inspect Schemes

```bash
# List all notification schemes
python list_notification_schemes.py
python list_notification_schemes.py --output json

# Filter by name
python list_notification_schemes.py --filter "Default"
python list_notification_schemes.py --filter "Development"

# Show event counts
python list_notification_schemes.py --show-events

# Get detailed scheme information
python get_notification_scheme.py 10000
python get_notification_scheme.py --name "Default Notification Scheme"
python get_notification_scheme.py 10000 --show-projects
python get_notification_scheme.py 10000 --output json
```

### Create Notification Schemes

```bash
# Create minimal scheme (name only)
python create_notification_scheme.py --name "New Project Notifications"

# Create with description
python create_notification_scheme.py \
  --name "Development Team Notifications" \
  --description "Notifications for development projects"

# Create with initial notifications
python create_notification_scheme.py \
  --name "Dev Notifications" \
  --event "Issue created" \
  --notify CurrentAssignee \
  --notify Reporter \
  --notify Group:developers

# Create from JSON template
python create_notification_scheme.py --template scheme_template.json

# Dry run to preview
python create_notification_scheme.py --name "Test" --dry-run
```

### Update Notification Schemes

```bash
# Update name
python update_notification_scheme.py 10000 --name "Renamed Scheme"

# Update description
python update_notification_scheme.py 10000 --description "Updated description"

# Update both
python update_notification_scheme.py 10000 \
  --name "Production Notifications" \
  --description "Notifications for production projects"

# Dry run to preview changes
python update_notification_scheme.py 10000 --name "Test" --dry-run
```

### Add Notifications to Schemes

```bash
# Add single notification
python add_notification.py 10000 \
  --event "Issue created" \
  --notify CurrentAssignee

# Add group notification
python add_notification.py 10000 \
  --event "Issue created" \
  --notify Group:developers

# Add multiple notifications to same event
python add_notification.py 10000 \
  --event "Issue resolved" \
  --notify CurrentAssignee \
  --notify Reporter \
  --notify AllWatchers

# Add project role notification
python add_notification.py 10000 \
  --event "Issue assigned" \
  --notify ProjectRole:10002

# Use event ID instead of name
python add_notification.py 10000 --event-id 1 --notify Reporter

# Dry run to preview
python add_notification.py 10000 --event "Issue created" --notify Reporter --dry-run
```

### Remove Notifications

```bash
# Remove by notification ID
python remove_notification.py 10000 --notification-id 12

# Remove by event and recipient
python remove_notification.py 10000 \
  --event "Issue created" \
  --recipient Group:developers

# Force removal without confirmation
python remove_notification.py 10000 --notification-id 12 --force

# Dry run to preview
python remove_notification.py 10000 --notification-id 12 --dry-run
```

### Delete Notification Schemes

```bash
# Delete with confirmation prompt
python delete_notification_scheme.py 10050

# Force delete without confirmation
python delete_notification_scheme.py 10050 --force

# Dry run to preview
python delete_notification_scheme.py 10050 --dry-run
```

---

## Recipient Types Reference

| Type | Format | Description |
|------|--------|-------------|
| `CurrentAssignee` | `CurrentAssignee` | Person currently assigned to the issue |
| `Reporter` | `Reporter` | Person who created the issue |
| `CurrentUser` | `CurrentUser` | Person performing the action |
| `ProjectLead` | `ProjectLead` | Project lead |
| `ComponentLead` | `ComponentLead` | Lead of the affected component |
| `AllWatchers` | `AllWatchers` | All users watching the issue |
| `Group` | `Group:group-name` | All members of a specific group |
| `ProjectRole` | `ProjectRole:role-id` | All users with a specific project role |
| `User` | `User:account-id` | Specific user by account ID |

---

## Common Events Reference

| Event Name | Event ID | Description |
|------------|----------|-------------|
| Issue created | 1 | A new issue has been created |
| Issue updated | 2 | An issue has been modified |
| Issue assigned | 3 | An issue has been assigned |
| Issue resolved | 4 | An issue has been resolved |
| Issue closed | 5 | An issue has been closed |
| Issue commented | 6 | A comment has been added |
| Issue reopened | 7 | An issue has been reopened |
| Issue deleted | 8 | An issue has been deleted |
| Issue moved | 9 | An issue has been moved to a different project |
| Work logged | 10 | Hours logged against an issue |

---

## Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| List/view schemes | Browse projects (for associated projects) |
| Get scheme details | Browse projects |
| Create scheme | Administer Jira (global) |
| Update scheme | Administer Jira (global) |
| Add notification | Administer Jira (global) |
| Remove notification | Administer Jira (global) |
| Delete scheme | Administer Jira (global) |

---

## Important Notes

1. **Schemes must not be in use** to be deleted - reassign projects first
2. **Event IDs may vary** by JIRA instance - use event names when possible
3. **Only company-managed projects** support notification schemes (team-managed projects use a different model)
4. **Group and ProjectRole recipients** require parameter (group name or role ID)
5. **Dry-run mode** available on all mutating operations to preview changes
6. **Force flag** bypasses confirmation prompts on delete/remove operations

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| **403 Forbidden** | Insufficient permissions | Verify Administer Jira permission |
| **404 Not Found** | Scheme doesn't exist | Check scheme ID |
| **409 Conflict** | Scheme in use | Reassign projects first |
| **400 Bad Request** | Invalid event or recipient | Check event name and recipient format |

---

## Template Files

JSON templates are available in `assets/templates/`:
- `notification_scheme_minimal.json` - Minimal notifications
- `notification_scheme_basic.json` - Common event-recipient mappings
- `notification_scheme_comprehensive.json` - Full notifications

---

## Related Guides

- [BEST_PRACTICES.md](../BEST_PRACTICES.md#notification-schemes) - Notification best practices
- [DECISION-TREE.md](../DECISION-TREE.md#i-want-to-set-up-notifications) - Quick script finder
- [QUICK-REFERENCE.md](../QUICK-REFERENCE.md#notifications) - Command syntax reference
- [VOODOO_CONSTANTS.md](../VOODOO_CONSTANTS.md#notification-event-ids) - Complete event ID reference
