---
name: "JIRA Administration"
description: "JIRA project and system administration - projects, automation rules, permissions, users, notifications, screens, issue types, workflows. Use when managing projects, configuring automation, or administering JIRA."
---

# JIRA Admin Skill

## When to Use This Skill

Use this skill when you need to:
- **Create, configure, or delete JIRA projects**
- **Manage project categories** (group projects by department, type, etc.)
- **Update project settings** (lead, default assignee, avatar, URL)
- **Archive or restore projects** for compliance or cleanup
- **List and search projects** across your JIRA instance
- **View detailed project configuration** (schemes, issue types, etc.)
- **Manage automation rules** (list, create, update, enable/disable)
- **Invoke manual automation rules** on issues
- **Create automation rules from templates**
- **Manage notification schemes** (create, update, delete)
- **Configure who receives notifications** for issue events
- **Add or remove notifications** from schemes
- **Manage issue types** (create, update, delete issue types)
- **Manage issue type schemes** (create, update, delete schemes)
- **Assign issue type schemes to projects**
- **Add, remove, or reorder issue types** in schemes
- **List and discover workflows** and their configurations
- **View workflow details** including statuses, transitions, and rules
- **Manage workflow schemes** and assign them to projects
- **List and filter statuses** by category or workflow
- **Get workflow information for specific issues**

This skill requires **Administer Jira** global permission for most operations, or **Administer Projects** permission for project-level changes.

## What This Skill Does

### Project Management
- Create new projects with various templates (Scrum, Kanban, Business)
- Get detailed project information and configuration
- Update project properties (name, description, lead, URL)
- Delete projects (moves to trash for 60 days)
- List and search projects with filtering

### Project Categories
- Create and manage project categories
- Assign projects to categories for organization
- List all categories in the instance

### Project Configuration
- Set project avatars (upload custom or select system)
- Change project lead
- Configure default assignee (PROJECT_LEAD, UNASSIGNED, COMPONENT_LEAD)
- View complete project configuration with schemes

### Archive/Restore Operations
- Archive inactive projects (read-only mode)
- Restore archived or deleted projects from trash
- List projects in trash with expiry dates

### Notification Schemes
- List all notification schemes with event counts
- Get detailed scheme configuration with event-recipient mappings
- Create new notification schemes from scratch or templates
- Update scheme metadata (name, description)
- Add notifications (event-recipient mappings) to schemes
- Remove notifications from schemes
- Delete unused notification schemes

### Issue Types
- List all issue types with filtering by hierarchy level
- Get detailed issue type information
- Create new issue types (standard, subtask, or epic)
- Update issue type properties (name, description, avatar)
- Delete issue types with migration to alternatives

### Issue Type Schemes
- List all issue type schemes with pagination
- Get scheme details with issue type mappings
- Create new schemes with specific issue types
- Update scheme metadata and default issue type
- Delete unused schemes
- View scheme-to-project assignments
- Assign schemes to projects
- Add, remove, and reorder issue types within schemes

### Workflow Management (READ-ONLY + Scheme Assignment)
- List all workflows with filtering and pagination
- Get workflow details including statuses, transitions, and rules
- Search workflows by name, scope, or active status
- List all workflow schemes with issue type mappings
- Get workflow scheme details and project associations
- Assign workflow schemes to projects (async operation)
- List all statuses with filtering by category or workflow
- Get workflow information for a specific issue
- **Note:** Workflow creation/modification NOT supported via REST API

## Troubleshooting & Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| **403 Forbidden** | Insufficient permissions | Verify you have "Administer Jira" or "Administer Projects" permission |
| **404 Not Found** | Resource doesn't exist | Check project key, scheme ID, or issue type ID spelling |
| **409 Conflict** | Resource already exists | Choose a different name or key (e.g., project key already in use) |
| **400 Bad Request** | Invalid input format | Validate key format (uppercase, 2-10 chars), check required fields |
| **401 Unauthorized** | Invalid or expired token | Regenerate API token at id.atlassian.com |
| **500 Internal Server Error** | JIRA server issue | Retry the operation; contact Atlassian support if persistent |

### Permission Verification

Before troubleshooting, verify your permissions:
```bash
# Check current user permissions
python search_users.py --me --include-groups

# Verify project access
python list_projects.py --type software
```

### Configuration Debugging

```bash
# View complete project configuration
python get_config.py PROJ --show-schemes

# Check which scheme is assigned to a project
python get_project_issue_type_scheme.py --project-id 10000
python get_workflow_scheme.py --id 10100 --show-projects
```

### Common Operation Failures

**Project Creation Fails:**
- Ensure project key is unique, uppercase, 2-10 characters, starts with a letter
- Verify you have the required JIRA product license (Software, Service Management)
- Check that the template key is valid for your instance

**Scheme Assignment Fails:**
- Cannot delete schemes in use - reassign projects first
- Issue type scheme assignment may fail if project has issues using types not in new scheme
- Workflow scheme assignment requires status migration if statuses differ

**Automation Rule Issues:**
- Complex rule creation may require the JIRA UI
- Ensure Cloud ID is retrievable (required for Automation API)
- Check API token scopes include `manage:jira-automation`

### Dry-Run Mode

All mutating operations support `--dry-run` to preview changes:
```bash
python delete_project.py PROJ --dry-run
python assign_permission_scheme.py --project PROJ --scheme 10050 --dry-run
python create_notification_scheme.py --name "Test" --dry-run
```

## Available Scripts

### Project CRUD Operations

| Script | Description |
|--------|-------------|
| `create_project.py` | Create a new JIRA project |
| `get_project.py` | Get detailed project information |
| `list_projects.py` | List and search projects |
| `update_project.py` | Update project properties |
| `delete_project.py` | Delete a project (moves to trash) |

### Project Categories

| Script | Description |
|--------|-------------|
| `create_category.py` | Create a project category |
| `list_categories.py` | List all project categories |
| `assign_category.py` | Assign a project to a category |

### Project Configuration

| Script | Description |
|--------|-------------|
| `set_avatar.py` | Set project avatar from file or system |
| `set_project_lead.py` | Change project lead |
| `set_default_assignee.py` | Configure default issue assignee |
| `get_config.py` | View full project configuration |

### Archive/Restore

| Script | Description |
|--------|-------------|
| `archive_project.py` | Archive a project (read-only) |
| `restore_project.py` | Restore archived/trashed project |
| `list_projects.py --trash` | List deleted projects in trash |

## Examples

### Create a New Scrum Project

```bash
# Create with Scrum template
python create_project.py --key MOBILE --name "Mobile App" --type software --template scrum

# Create with lead and description
python create_project.py --key WEBAPP --name "Web Application" \
  --type software --template kanban \
  --lead alice@example.com \
  --description "Customer-facing web application"

# Create business project
python create_project.py --key MKTG --name "Marketing" --type business
```

### Get Project Information

```bash
# Get basic info
python get_project.py PROJ

# Get with components and versions
python get_project.py PROJ --show-components --show-versions

# JSON output
python get_project.py PROJ --output json
```

### List Projects

```bash
# List all projects
python list_projects.py

# Filter by type
python list_projects.py --type software

# Search by name
python list_projects.py --search "mobile"

# Include archived projects
python list_projects.py --include-archived

# Export to CSV
python list_projects.py --output csv > projects.csv
```

### Update Project

```bash
# Update name
python update_project.py PROJ --name "New Project Name"

# Update lead
python update_project.py PROJ --lead bob@example.com

# Update multiple fields
python update_project.py PROJ --name "Updated" --description "New desc" --url https://example.com
```

### Delete Project

```bash
# Delete with confirmation prompt
python delete_project.py PROJ

# Skip confirmation
python delete_project.py PROJ --yes

# Dry run to preview
python delete_project.py PROJ --dry-run
```

### Manage Categories

```bash
# Create a category
python create_category.py --name "Development" --description "All dev projects"

# List categories
python list_categories.py

# Assign project to category
python assign_category.py PROJ --category "Development"

# Remove category from project
python assign_category.py PROJ --remove
```

### Project Configuration

```bash
# Set avatar from file
python set_avatar.py PROJ --file /path/to/logo.png

# List available system avatars
python set_avatar.py PROJ --list

# Change project lead
python set_project_lead.py PROJ --lead alice@example.com

# Set default assignee
python set_default_assignee.py PROJ --type PROJECT_LEAD

# View full configuration
python get_config.py PROJ --show-schemes
```

### Archive and Restore

```bash
# Archive inactive project
python archive_project.py OLDPROJ --yes

# List trashed projects
python list_projects.py --trash

# Restore from trash/archive
python restore_project.py OLDPROJ

# Dry-run archive to preview
python archive_project.py OLDPROJ --dry-run
```

## Project Types and Templates

### Project Types
- **software**: Jira Software projects (requires Jira Software license)
- **business**: Jira Core/Work Management projects
- **service_desk**: Jira Service Management projects (requires JSM license)

### Template Shortcuts
| Shortcut | Full Template Key | Description |
|----------|-------------------|-------------|
| `scrum` | `com.pyxis.greenhopper.jira:gh-scrum-template` | Scrum board |
| `kanban` | `com.pyxis.greenhopper.jira:gh-kanban-template` | Kanban board |
| `basic` | `com.pyxis.greenhopper.jira:gh-simplified-basic` | Basic software |

## Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| Create project | Administer Jira (global) |
| Update project (general) | Administer Projects |
| Update project key/schemes | Administer Jira (global) |
| Delete project | Administer Jira (global) |
| Archive/restore project | Administer Jira (global) |
| Create category | Administer Jira (global) |
| Browse projects | Browse Projects |

## Important Notes

1. **Deleted projects remain in trash for 60 days** before permanent deletion
2. **Project keys cannot be changed** after creation without Administer Jira permission
3. **Project type cannot be changed** after creation (API limitation)
4. **Templates are only used during creation** and don't persist
5. **Archived projects are read-only** but can be browsed and restored

## Error Handling

Common errors and solutions:

- **403 Permission Denied**: Contact your JIRA administrator for Administer Jira permission
- **409 Conflict**: Project key already exists - choose a different key
- **400 Invalid Key**: Keys must be uppercase, 2-10 characters, start with a letter
- **404 Not Found**: Project doesn't exist - check the key spelling

---

## Automation Rules Management

### What Automation Management Does

1. **Rule Discovery & Inspection**
   - List all automation rules with filtering by project, state
   - Get detailed rule configuration including triggers and actions
   - Search rules by trigger type, enabled/disabled state, or project scope

2. **Rule State Management**
   - Enable disabled automation rules
   - Disable active automation rules
   - Toggle rule state (enabled <-> disabled)
   - Dry-run mode for previewing changes

3. **Manual Rule Invocation**
   - List manually-triggered automation rules
   - Invoke manual rules on specific issues
   - Pass custom properties to rule execution

4. **Rule Creation & Updates**
   - List available automation templates
   - Get template details and required parameters
   - Create rules from templates with custom configuration
   - Update existing rule name, description, and configuration

### Automation Scripts

#### Rule Discovery
| Script | Description |
|--------|-------------|
| `list_automation_rules.py` | List all automation rules with filtering |
| `get_automation_rule.py` | Get detailed rule configuration |
| `search_automation_rules.py` | Search rules by trigger, state, scope |

#### Rule State Management
| Script | Description |
|--------|-------------|
| `enable_automation_rule.py` | Enable a disabled rule |
| `disable_automation_rule.py` | Disable an active rule |
| `toggle_automation_rule.py` | Toggle rule state |

#### Manual Rules
| Script | Description |
|--------|-------------|
| `list_manual_rules.py` | List manually-triggered rules |
| `invoke_manual_rule.py` | Trigger a manual rule on an issue |

#### Templates & Creation
| Script | Description |
|--------|-------------|
| `list_automation_templates.py` | List available templates |
| `get_automation_template.py` | Get template details |
| `create_rule_from_template.py` | Create rule from template |
| `update_automation_rule.py` | Update rule configuration |

### Automation Examples

```bash
# List all automation rules
python list_automation_rules.py
python list_automation_rules.py --project PROJ
python list_automation_rules.py --state enabled
python list_automation_rules.py --state disabled --output json

# Get rule details
python get_automation_rule.py "ari:cloud:jira::site/12345..."
python get_automation_rule.py --name "Auto-assign to lead"
python get_automation_rule.py RULE_ID --output json

# Search rules
python search_automation_rules.py --trigger "jira.issue.event.trigger:created"
python search_automation_rules.py --state enabled --project PROJ
python search_automation_rules.py --trigger issue_created --state disabled

# Enable/Disable rules
python enable_automation_rule.py RULE_ID
python enable_automation_rule.py --name "Auto-assign to lead"
python disable_automation_rule.py RULE_ID --confirm
python toggle_automation_rule.py RULE_ID

# Dry run mode
python enable_automation_rule.py RULE_ID --dry-run
python disable_automation_rule.py RULE_ID --dry-run

# Manual rules
python list_manual_rules.py --context issue
python invoke_manual_rule.py RULE_ID --issue PROJ-123
python invoke_manual_rule.py RULE_ID --issue PROJ-123 --property '{"priority": "High"}'

# Templates
python list_automation_templates.py
python list_automation_templates.py --category "Issue Management"
python get_automation_template.py TEMPLATE_ID

# Create from template
python create_rule_from_template.py TEMPLATE_ID --project PROJ
python create_rule_from_template.py TEMPLATE_ID --project PROJ --name "My Rule"
python create_rule_from_template.py TEMPLATE_ID --project PROJ --dry-run

# Update rule
python update_automation_rule.py RULE_ID --name "New Rule Name"
python update_automation_rule.py RULE_ID --description "Updated description"
python update_automation_rule.py RULE_ID --config rule_config.json
```

### Automation API Requirements

#### Authentication
- JIRA API token with appropriate scopes
- Jira Administrator permissions (for full rule management)
- Project Administrator permissions (for project-scoped rules only)

#### Required API Token Scopes
- `manage:jira-automation` - For create/update/delete operations
- `read:jira-work` - For list/get operations

#### Cloud ID Requirement
All Automation API calls require the Atlassian Cloud ID, which is automatically retrieved from the JIRA instance using the tenant info endpoint (`/_edge/tenant_info`).

### Automation Limitations

1. **Complex Rule Creation**: Very complex rules with nested conditions may require the UI
2. **Execution History**: No API for viewing rule execution logs (UI only)
3. **Bulk Operations**: No dedicated bulk enable/disable endpoint (must process sequentially)
4. **Analytics**: No API for rule performance metrics
5. **Audit Trail**: Limited audit information in API responses

---

## Permission Schemes

### When to Use Permission Scheme Scripts

Use these scripts when you need to:
- View, create, update, or delete permission schemes
- Manage permission grants within schemes
- Assign permission schemes to projects
- List all available JIRA permissions
- Clone existing permission schemes with modifications

### Permission Scheme Scripts

| Script | Description |
|--------|-------------|
| `list_permission_schemes.py` | List all permission schemes with optional filtering |
| `get_permission_scheme.py` | Get detailed information about a specific scheme |
| `create_permission_scheme.py` | Create a new permission scheme |
| `update_permission_scheme.py` | Update an existing scheme's metadata or grants |
| `delete_permission_scheme.py` | Delete a permission scheme (must not be in use) |
| `assign_permission_scheme.py` | Assign a scheme to one or more projects |
| `list_permissions.py` | List all available JIRA permissions |

### Permission Scheme Examples

```bash
# List all permission schemes
python list_permission_schemes.py
python list_permission_schemes.py --show-grants
python list_permission_schemes.py --filter "Development"
python list_permission_schemes.py --show-projects

# Get detailed scheme information
python get_permission_scheme.py 10000
python get_permission_scheme.py "Default Software Scheme"
python get_permission_scheme.py 10000 --show-projects
python get_permission_scheme.py 10000 --export-template grants.json

# Create permission schemes
python create_permission_scheme.py --name "New Scheme" --description "Description"
python create_permission_scheme.py --name "New Scheme" --template grants.json
python create_permission_scheme.py --name "New Scheme" --clone 10000
python create_permission_scheme.py --name "New Scheme" \
  --grant "BROWSE_PROJECTS:anyone" \
  --grant "CREATE_ISSUES:group:jira-developers"

# Update permission schemes
python update_permission_scheme.py 10000 --name "Updated Name"
python update_permission_scheme.py 10000 --add-grant "EDIT_ISSUES:group:developers"
python update_permission_scheme.py 10000 --remove-grant 10103
python update_permission_scheme.py 10000 --remove-grant "EDIT_ISSUES:group:testers"

# Delete permission schemes
python delete_permission_scheme.py 10050 --confirm
python delete_permission_scheme.py 10050 --check-only
python delete_permission_scheme.py 10050 --force --confirm

# Assign to projects
python assign_permission_scheme.py --project PROJ --scheme 10050
python assign_permission_scheme.py --projects PROJ1,PROJ2 --scheme "Custom Scheme"
python assign_permission_scheme.py --project PROJ --show-current

# List permissions
python list_permissions.py
python list_permissions.py --type PROJECT
python list_permissions.py --search "issue"
```

### Permission Grant Format

When specifying grants, use the format:
```
PERMISSION:HOLDER_TYPE[:HOLDER_PARAMETER]

Examples:
  BROWSE_PROJECTS:anyone
  CREATE_ISSUES:group:jira-developers
  EDIT_ISSUES:projectRole:Developers
  ADMINISTER_PROJECTS:projectLead
  RESOLVE_ISSUES:user:5b10a2844c20165700ede21g
```

### Holder Types

| Type | Description | Parameter Required |
|------|-------------|-------------------|
| `anyone` | All users (logged in or anonymous) | No |
| `group` | JIRA group | Group name |
| `projectRole` | Project role | Role name |
| `user` | Specific user | Account ID |
| `projectLead` | Project lead | No |
| `reporter` | Issue reporter | No |
| `currentAssignee` | Current issue assignee | No |
| `applicationRole` | Application role | Role key |

### Common Permission Keys

**Project Permissions:**
- `BROWSE_PROJECTS` - View projects and issues
- `CREATE_ISSUES` - Create issues
- `EDIT_ISSUES` - Edit issues
- `DELETE_ISSUES` - Delete issues
- `ASSIGN_ISSUES` - Assign issues
- `ASSIGNABLE_USER` - Be assigned to issues
- `RESOLVE_ISSUES` - Resolve/reopen issues
- `CLOSE_ISSUES` - Close issues
- `TRANSITION_ISSUES` - Transition issues
- `MOVE_ISSUES` - Move issues between projects
- `LINK_ISSUES` - Link issues
- `ADD_COMMENTS` - Add comments
- `EDIT_ALL_COMMENTS` - Edit all comments
- `DELETE_ALL_COMMENTS` - Delete all comments
- `CREATE_ATTACHMENTS` - Create attachments
- `WORK_ON_ISSUES` - Log work on issues
- `ADMINISTER_PROJECTS` - Administer projects
- `MANAGE_SPRINTS` - Manage sprints
- `MANAGE_WATCHERS` - Manage watchers

### Permission Scheme Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| List/view schemes | Permission to access Jira |
| Create scheme | Administer Jira (global) |
| Update scheme | Administer Jira (global) |
| Delete scheme | Administer Jira (global) |
| Assign to project | Administer Jira (global) |
| List permissions | None (public endpoint) |

---

## User & Group Management

### When to Use User & Group Scripts

Use these scripts when you need to:
- Search for users by name or email
- Get user details and group memberships
- Create, list, or delete groups
- View group members
- Add or remove users from groups
- Audit team membership and access

### User Management Scripts

| Script | Description |
|--------|-------------|
| `search_users.py` | Search users by name/email, find assignable users for projects |
| `get_user.py` | Get user details by account ID or email, including groups |

### Group Management Scripts

| Script | Description |
|--------|-------------|
| `list_groups.py` | List all groups with optional member counts |
| `get_group_members.py` | Get members of a specific group |
| `create_group.py` | Create a new group |
| `delete_group.py` | Delete a group (requires confirmation) |

### Membership Management Scripts

| Script | Description |
|--------|-------------|
| `add_user_to_group.py` | Add a user to a group |
| `remove_user_from_group.py` | Remove a user from a group |

### User & Group Examples

#### User Search and Retrieval

```bash
# Search for users
python search_users.py "john"
python search_users.py "john.doe@example.com"
python search_users.py "john" --project PROJ --assignable
python search_users.py "john" --all --include-groups

# Get user details
python get_user.py --email john.doe@example.com
python get_user.py --account-id 5b10ac8d82e05b22cc7d4ef5
python get_user.py --me --include-groups
python get_user.py --email john@example.com --output json
```

#### Group Operations

```bash
# List groups
python list_groups.py
python list_groups.py --query "developers"
python list_groups.py --include-members
python list_groups.py --show-system --output json

# Get group members
python get_group_members.py "jira-developers"
python get_group_members.py "jira-developers" --include-inactive
python get_group_members.py --group-id abc123 --output csv > members.csv

# Create a group
python create_group.py "mobile-team"
python create_group.py "external-contractors" --dry-run

# Delete a group
python delete_group.py "old-team" --confirm
python delete_group.py "old-team" --swap "new-team" --confirm
python delete_group.py "test-group" --dry-run
```

#### Membership Operations

```bash
# Add user to group
python add_user_to_group.py john@example.com --group "jira-developers"
python add_user_to_group.py --account-id 5b10ac8d82e05b22cc7d4ef5 --group "mobile-team"
python add_user_to_group.py john@example.com --group "team" --dry-run

# Remove user from group
python remove_user_from_group.py john@example.com --group "jira-developers" --confirm
python remove_user_from_group.py --account-id 5b10ac8d82e05b22cc7d4ef5 --group "old-team" --confirm
python remove_user_from_group.py jane@example.com --group "team" --dry-run
```

### User & Group Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| Search/view users | Browse users and groups |
| Get user details | Browse users and groups |
| List/view groups | Browse users and groups |
| Create group | Site administration |
| Delete group | Site administration |
| Add user to group | Site administration |
| Remove user from group | Site administration |

### GDPR & Privacy Considerations

This feature implements GDPR-compliant user handling:
- Uses `accountId` for all user references (not username)
- Handles privacy-restricted fields gracefully (shown as "[hidden]")
- Respects user privacy settings for email, timezone, and locale
- Properly handles "unknown" account IDs for deleted/anonymized users

### User & Group Important Notes

1. **User creation/deactivation** is NOT available via standard JIRA API - requires Cloud Admin API
2. **System groups** (jira-administrators, jira-users, etc.) cannot be deleted
3. **Adding/removing users is idempotent** - no error if already member or not member
4. **Email lookup may fail** if user has privacy controls enabled
5. **Group names are case-insensitive** for search but case-preserved
6. **All operations require appropriate permissions** - Site administration for most write operations

---

## Notification Schemes

### When to Use Notification Scheme Scripts

Use these scripts when you need to:
- List and inspect notification schemes across your JIRA instance
- View which events trigger notifications and who receives them
- Create new notification schemes for different project types
- Update notification scheme metadata (name, description)
- Add event-to-recipient notification mappings
- Remove notifications from schemes
- Delete unused notification schemes
- See which projects use a specific notification scheme

### What are Notification Schemes?

Notification schemes define who receives email notifications when specific events occur on JIRA issues. They map events (issue created, assigned, commented, etc.) to recipients (assignees, reporters, watchers, groups, etc.).

**Key Concepts:**
- **Events:** System-defined triggers (e.g., "Issue Created", "Issue Assigned", "Issue Commented")
- **Recipients:** Notification targets (current assignee, reporter, watchers, groups, project roles)
- **Scheme:** Collection of event-to-recipient mappings
- **Project Association:** Each company-managed project uses one notification scheme

### Notification Scheme Scripts

| Script | Description |
|--------|-------------|
| `list_notification_schemes.py` | List all notification schemes with optional filtering and event counts |
| `get_notification_scheme.py` | Get detailed scheme info with event-to-recipient mappings |
| `create_notification_scheme.py` | Create a new notification scheme with optional initial events |
| `update_notification_scheme.py` | Update scheme name and/or description |
| `add_notification.py` | Add event-recipient notifications to a scheme |
| `remove_notification.py` | Remove a specific notification from a scheme |
| `delete_notification_scheme.py` | Delete a notification scheme (must not be in use) |

### Notification Scheme Examples

#### List and Inspect Schemes

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

#### Create Notification Schemes

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

#### Update Notification Schemes

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

#### Add Notifications to Schemes

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

#### Remove Notifications

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

#### Delete Notification Schemes

```bash
# Delete with confirmation prompt
python delete_notification_scheme.py 10050

# Force delete without confirmation
python delete_notification_scheme.py 10050 --force

# Dry run to preview
python delete_notification_scheme.py 10050 --dry-run
```

### Recipient Types

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

### Common Events

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

### Notification Scheme Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| List/view schemes | Browse projects (for associated projects) |
| Get scheme details | Browse projects |
| Create scheme | Administer Jira (global) |
| Update scheme | Administer Jira (global) |
| Add notification | Administer Jira (global) |
| Remove notification | Administer Jira (global) |
| Delete scheme | Administer Jira (global) |

### Notification Scheme Important Notes

1. **Schemes must not be in use** to be deleted - reassign projects first
2. **Event IDs may vary** by JIRA instance - use event names when possible
3. **Only company-managed projects** support notification schemes (team-managed projects use a different model)
4. **Group and ProjectRole recipients** require parameter (group name or role ID)
5. **Dry-run mode** available on all mutating operations to preview changes
6. **Force flag** bypasses confirmation prompts on delete/remove operations

---

## Screen Management

### When to Use Screen Management Scripts

Use these scripts when you need to:
- **View and manage screens** - List, inspect, and modify screens
- **Configure screen tabs and fields** - Add or remove fields from screen tabs
- **Manage screen schemes** - View screen schemes and their operation mappings
- **Manage issue type screen schemes** - View project-level screen configurations
- **Discover project screen configuration** - See which screens a project uses

### Understanding JIRA's 3-Tier Screen Hierarchy

JIRA uses a hierarchical system for screen configuration:

```
Project
    |
    +-- Issue Type Screen Scheme (project-level assignment)
            |
            +-- Screen Scheme (per issue type: Bug, Story, Task, etc.)
                    |
                    +-- Screens (per operation: create, edit, view)
                            |
                            +-- Tabs
                                    |
                                    +-- Fields
```

**Level 1: Issue Type Screen Scheme** - Assigned to a project, maps issue types to screen schemes
**Level 2: Screen Scheme** - Maps operations (create/edit/view) to screens
**Level 3: Screen** - Contains tabs and fields that users see when performing operations

### Screen Management Scripts

#### Screen Operations (Level 3)

| Script | Description |
|--------|-------------|
| `list_screens.py` | List all screens with filtering |
| `get_screen.py` | Get screen details with tabs and fields |
| `list_screen_tabs.py` | List tabs for a specific screen |
| `get_screen_fields.py` | Get all fields on a screen or specific tab |
| `add_field_to_screen.py` | Add a field to a screen tab |
| `remove_field_from_screen.py` | Remove a field from a screen tab |

#### Screen Schemes (Level 2)

| Script | Description |
|--------|-------------|
| `list_screen_schemes.py` | List all screen schemes |
| `get_screen_scheme.py` | Get screen scheme details with operation mappings |

#### Issue Type Screen Schemes (Level 1)

| Script | Description |
|--------|-------------|
| `list_issue_type_screen_schemes.py` | List all issue type screen schemes |
| `get_issue_type_screen_scheme.py` | Get scheme details with issue type mappings |

#### Project Screen Discovery

| Script | Description |
|--------|-------------|
| `get_project_screens.py` | Discover complete screen configuration for a project |

### Screen Management Examples

#### Working with Screens

```bash
# List all screens
python list_screens.py
python list_screens.py --filter "Default"
python list_screens.py --scope PROJECT
python list_screens.py --all --output json

# Get screen details
python get_screen.py 1
python get_screen.py 1 --tabs
python get_screen.py 1 --tabs --fields
python get_screen.py 1 --output json

# List screen tabs
python list_screen_tabs.py 1
python list_screen_tabs.py 1 --field-count
python list_screen_tabs.py 1 --output json

# Get fields on a screen
python get_screen_fields.py 1
python get_screen_fields.py 1 --tab 10000
python get_screen_fields.py 1 --type custom
python get_screen_fields.py 1 --type system
```

#### Modifying Screen Fields

```bash
# Add a field to a screen
python add_field_to_screen.py 1 customfield_10016
python add_field_to_screen.py 1 customfield_10016 --tab 10001
python add_field_to_screen.py 1 customfield_10016 --tab-name "Custom Fields"
python add_field_to_screen.py 1 customfield_10016 --dry-run

# Remove a field from a screen
python remove_field_from_screen.py 1 customfield_10016
python remove_field_from_screen.py 1 customfield_10016 --tab 10001
python remove_field_from_screen.py 1 summary --force
python remove_field_from_screen.py 1 customfield_10016 --dry-run
```

#### Working with Screen Schemes

```bash
# List screen schemes
python list_screen_schemes.py
python list_screen_schemes.py --filter "Default"
python list_screen_schemes.py --show-screens
python list_screen_schemes.py --output json

# Get screen scheme details
python get_screen_scheme.py 1
python get_screen_scheme.py 1 --details
python get_screen_scheme.py 1 --output json
```

#### Working with Issue Type Screen Schemes

```bash
# List issue type screen schemes
python list_issue_type_screen_schemes.py
python list_issue_type_screen_schemes.py --filter "Default"
python list_issue_type_screen_schemes.py --projects
python list_issue_type_screen_schemes.py --output json

# Get issue type screen scheme details
python get_issue_type_screen_scheme.py 10000
python get_issue_type_screen_scheme.py 10000 --mappings
python get_issue_type_screen_scheme.py 10000 --projects
python get_issue_type_screen_scheme.py 10000 --output json
```

#### Project Screen Discovery

```bash
# Discover project screen configuration
python get_project_screens.py PROJ
python get_project_screens.py PROJ --issue-types
python get_project_screens.py PROJ --full
python get_project_screens.py PROJ --full --operation create
python get_project_screens.py PROJ --full --available-fields
python get_project_screens.py PROJ --output json
```

### Common Screen Field Operations

**Adding Custom Fields to Screens:**
```bash
# Add Story Points field to create screen
python add_field_to_screen.py 1 customfield_10016 --tab-name "Field Tab"

# Add Sprint field to edit screen
python add_field_to_screen.py 2 customfield_10020

# Dry run to validate
python add_field_to_screen.py 1 customfield_10016 --dry-run
```

**Removing Unused Fields:**
```bash
# Remove a custom field
python remove_field_from_screen.py 1 customfield_10025

# Force remove a required field (use caution)
python remove_field_from_screen.py 1 summary --force
```

### Screen Management Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| List/view screens | Administer Jira (global) |
| List/view screen schemes | Administer Jira (global) |
| Add field to screen | Administer Jira (global) |
| Remove field from screen | Administer Jira (global) |
| View project screens | Browse Projects + Administer Jira |

### Screen Management Important Notes

1. **Team-managed projects** use a different screen model - these scripts work with company-managed projects
2. **Removing required fields** (summary, issue type) can break issue creation - use --force with caution
3. **Screen changes affect all projects** using that screen scheme
4. **Custom field availability** - A field must be available in the screen context to be added
5. **Dry-run mode** available on add/remove operations to preview changes
6. **Field order** - New fields are added at the end of the tab; reordering requires the JIRA UI

---

## Issue Type Management

### When to Use Issue Type Scripts

Use these scripts when you need to:
- **List all issue types** in your JIRA instance
- **Get details** about a specific issue type
- **Create new issue types** (standard, subtask, or epic)
- **Update existing issue types** (name, description, avatar)
- **Delete issue types** with migration to alternatives

### Understanding Issue Types

Issue types define the nature of work items in JIRA:

| Hierarchy Level | Type | Description |
|-----------------|------|-------------|
| -1 | Subtask | Child issues that must have a parent |
| 0 | Standard | Regular issues (Bug, Task, Story) |
| 1 | Epic | Container issues that group other issues |

### Issue Type Scripts

| Script | Description |
|--------|-------------|
| `list_issue_types.py` | List all issue types with filtering by hierarchy |
| `get_issue_type.py` | Get detailed issue type information |
| `create_issue_type.py` | Create a new issue type |
| `update_issue_type.py` | Update issue type name, description, or avatar |
| `delete_issue_type.py` | Delete an issue type with optional migration |

### Issue Type Examples

#### Listing Issue Types

```bash
# List all issue types
python list_issue_types.py

# List only subtask types
python list_issue_types.py --subtask-only

# List only standard types (no subtasks or epics)
python list_issue_types.py --standard-only

# Filter by hierarchy level
python list_issue_types.py --hierarchy-level 0

# Output as JSON
python list_issue_types.py --format json

# Use specific profile
python list_issue_types.py --profile production
```

#### Getting Issue Type Details

```bash
# Get issue type by ID
python get_issue_type.py 10001

# Get with alternative types (for migration planning)
python get_issue_type.py 10001 --show-alternatives

# Output as JSON
python get_issue_type.py 10001 --format json
```

#### Creating Issue Types

```bash
# Create standard issue type
python create_issue_type.py --name "Feature Request" --description "Customer feature requests"

# Create subtask type
python create_issue_type.py --name "Technical Task" --type subtask --description "Technical implementation task"

# Create with specific hierarchy level
python create_issue_type.py --name "Initiative" --hierarchy-level 1

# Output created type as JSON
python create_issue_type.py --name "Support Issue" --format json
```

#### Updating Issue Types

```bash
# Update name
python update_issue_type.py 10001 --name "Updated Name"

# Update description
python update_issue_type.py 10001 --description "New description"

# Update avatar
python update_issue_type.py 10001 --avatar-id 10204

# Update multiple fields
python update_issue_type.py 10001 --name "Feature" --description "Product feature"
```

#### Deleting Issue Types

```bash
# Delete with confirmation prompt
python delete_issue_type.py 10050

# Delete and migrate existing issues to alternative type
python delete_issue_type.py 10050 --alternative-id 10001

# Force delete without confirmation
python delete_issue_type.py 10050 --force

# Use specific profile
python delete_issue_type.py 10050 --alternative-id 10001 --profile production
```

### Issue Type Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| List/view issue types | Browse projects |
| Get issue type details | Browse projects |
| Create issue type | Administer Jira (global) |
| Update issue type | Administer Jira (global) |
| Delete issue type | Administer Jira (global) |

### Issue Type Important Notes

1. **Issue type names must be unique** and <= 60 characters
2. **Deleting issue types** requires migrating existing issues to an alternative type
3. **System issue types** (Story, Bug, Task, Epic, Subtask) cannot be deleted
4. **Hierarchy levels** determine parent-child relationships (-1=subtask, 0=standard, 1=epic)
5. **Avatar IDs** can be obtained from the JIRA administration UI

---

## Issue Type Scheme Management

### When to Use Issue Type Scheme Scripts

Use these scripts when you need to:
- **List all issue type schemes** in your JIRA instance
- **Get scheme details** including which issue types are included
- **Create new schemes** with specific issue types
- **Update scheme metadata** (name, description, default type)
- **Delete unused schemes**
- **View scheme-to-project mappings**
- **Assign schemes to projects**
- **Add or remove issue types** from schemes
- **Reorder issue types** within schemes

### Understanding Issue Type Schemes

Issue type schemes define which issue types are available in a project:

- **Default Scheme**: Contains all issue types, used when no specific scheme is assigned
- **Custom Schemes**: Tailored collections of issue types for specific project needs
- **Default Issue Type**: The issue type pre-selected when creating new issues
- **Scheme Assignment**: Company-managed projects can have one scheme; team-managed projects manage their own types

### Issue Type Scheme Scripts

#### Scheme CRUD Operations

| Script | Description |
|--------|-------------|
| `list_issue_type_schemes.py` | List all schemes with pagination |
| `get_issue_type_scheme.py` | Get scheme details with issue type list |
| `create_issue_type_scheme.py` | Create a new scheme with issue types |
| `update_issue_type_scheme.py` | Update scheme name, description, or default type |
| `delete_issue_type_scheme.py` | Delete an unused scheme |

#### Scheme Assignment

| Script | Description |
|--------|-------------|
| `get_project_issue_type_scheme.py` | Get the scheme assigned to a project |
| `assign_issue_type_scheme.py` | Assign a scheme to a project |
| `get_issue_type_scheme_mappings.py` | List scheme-to-issue-type mappings |

#### Scheme Issue Type Management

| Script | Description |
|--------|-------------|
| `add_issue_types_to_scheme.py` | Add issue types to an existing scheme |
| `remove_issue_type_from_scheme.py` | Remove an issue type from a scheme |
| `reorder_issue_types_in_scheme.py` | Change the order of issue types in a scheme |

### Issue Type Scheme Examples

#### Listing Schemes

```bash
# List all issue type schemes
python list_issue_type_schemes.py

# With pagination
python list_issue_type_schemes.py --start-at 0 --max-results 100

# Filter by scheme IDs
python list_issue_type_schemes.py --scheme-ids 10000 10001

# Order by name
python list_issue_type_schemes.py --order-by name

# Output as JSON
python list_issue_type_schemes.py --format json
```

#### Getting Scheme Details

```bash
# Get scheme by ID
python get_issue_type_scheme.py 10001

# Include issue type mappings
python get_issue_type_scheme.py 10001 --include-items

# Output as JSON
python get_issue_type_scheme.py 10001 --format json
```

#### Creating Schemes

```bash
# Create with required fields
python create_issue_type_scheme.py \
  --name "Development Scheme" \
  --issue-type-ids 10001 10002 10003

# Create with description and default type
python create_issue_type_scheme.py \
  --name "Support Scheme" \
  --description "Issue types for support projects" \
  --issue-type-ids 10001 10004 10005 \
  --default-issue-type-id 10004

# Output created scheme as JSON
python create_issue_type_scheme.py \
  --name "New Scheme" \
  --issue-type-ids 10001 \
  --format json
```

#### Updating Schemes

```bash
# Update name
python update_issue_type_scheme.py 10001 --name "Updated Scheme Name"

# Update description
python update_issue_type_scheme.py 10001 --description "New description"

# Change default issue type
python update_issue_type_scheme.py 10001 --default-issue-type-id 10002

# Update multiple fields
python update_issue_type_scheme.py 10001 \
  --name "Production Scheme" \
  --description "For production projects" \
  --default-issue-type-id 10003
```

#### Deleting Schemes

```bash
# Delete with confirmation prompt
python delete_issue_type_scheme.py 10050

# Force delete without confirmation
python delete_issue_type_scheme.py 10050 --force

# Use specific profile
python delete_issue_type_scheme.py 10050 --profile production
```

#### Project Scheme Assignment

```bash
# Get scheme for a project
python get_project_issue_type_scheme.py --project-id 10000

# Get for multiple projects
python get_project_issue_type_scheme.py --project-ids 10000 10001 10002

# Output as JSON
python get_project_issue_type_scheme.py --project-id 10000 --format json

# Assign scheme to project
python assign_issue_type_scheme.py --scheme-id 10001 --project-id 10000

# Dry run to preview assignment
python assign_issue_type_scheme.py --scheme-id 10001 --project-id 10000 --dry-run

# Force without confirmation
python assign_issue_type_scheme.py --scheme-id 10001 --project-id 10000 --force
```

#### Scheme Mappings

```bash
# Get all mappings
python get_issue_type_scheme_mappings.py

# Filter by scheme IDs
python get_issue_type_scheme_mappings.py --scheme-ids 10000 10001

# With pagination
python get_issue_type_scheme_mappings.py --start-at 0 --max-results 100

# Output as JSON
python get_issue_type_scheme_mappings.py --format json
```

#### Managing Issue Types in Schemes

```bash
# Add issue types to a scheme
python add_issue_types_to_scheme.py --scheme-id 10001 --issue-type-ids 10003

# Add multiple issue types
python add_issue_types_to_scheme.py --scheme-id 10001 --issue-type-ids 10003 10004 10005

# Remove issue type from scheme (with confirmation)
python remove_issue_type_from_scheme.py --scheme-id 10001 --issue-type-id 10003

# Force remove without confirmation
python remove_issue_type_from_scheme.py --scheme-id 10001 --issue-type-id 10003 --force

# Reorder: move issue type to first position
python reorder_issue_types_in_scheme.py --scheme-id 10001 --issue-type-id 10003

# Reorder: move issue type after another
python reorder_issue_types_in_scheme.py --scheme-id 10001 --issue-type-id 10003 --after 10001
```

### Issue Type Scheme Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| List/view schemes | Administer Jira (global) |
| Get scheme details | Administer Jira (global) |
| Create scheme | Administer Jira (global) |
| Update scheme | Administer Jira (global) |
| Delete scheme | Administer Jira (global) |
| Assign to project | Administer Jira (global) |
| Add/remove issue types | Administer Jira (global) |
| Reorder issue types | Administer Jira (global) |

### Issue Type Scheme Important Notes

1. **Default Issue Type Scheme** cannot be deleted - it's the system fallback
2. **Schemes in use** by projects cannot be deleted - reassign projects first
3. **Cannot remove the default issue type** from a scheme
4. **Cannot remove the last issue type** from a scheme - at least one must remain
5. **Team-managed projects** don't use issue type schemes - they manage types directly
6. **Assigning a scheme may fail** if the project has issues using types not in the new scheme
7. **Issue type order** in the scheme determines display order in the UI

---

## Workflow Management

### When to Use Workflow Management Scripts

Use these scripts when you need to:
- **List and discover workflows** in your JIRA instance
- **Get workflow details** including statuses, transitions, and rules
- **Search workflows** by name, scope, or status
- **List and manage workflow schemes** that map workflows to issue types
- **Assign workflow schemes to projects**
- **List and filter statuses** in your JIRA instance
- **Get workflow information for specific issues**

### Understanding JIRA Workflows

JIRA workflows define the lifecycle of issues:

**Key Concepts:**
- **Workflow**: A set of statuses and transitions that define how issues move through their lifecycle
- **Status**: A state an issue can be in (e.g., "To Do", "In Progress", "Done")
- **Transition**: The movement from one status to another (e.g., "Start Progress")
- **Workflow Scheme**: Maps workflows to issue types for a project
- **Status Category**: Groups statuses into TODO, IN_PROGRESS, or DONE categories

**Important Limitation:** Workflow creation and modification is NOT supported via the JIRA REST API. Workflows must be created and edited through the JIRA administration UI. These scripts provide READ operations and scheme assignment only.

### Workflow Management Scripts

#### Workflow Discovery

| Script | Description |
|--------|-------------|
| `list_workflows.py` | List all workflows with filtering and pagination |
| `get_workflow.py` | Get workflow details including statuses and transitions |
| `search_workflows.py` | Search workflows by name, scope, or status |

#### Workflow Scheme Management

| Script | Description |
|--------|-------------|
| `list_workflow_schemes.py` | List all workflow schemes with mappings |
| `get_workflow_scheme.py` | Get scheme details with issue type mappings |
| `assign_workflow_scheme.py` | Assign a workflow scheme to a project |

#### Status Management

| Script | Description |
|--------|-------------|
| `list_statuses.py` | List all statuses with filtering by category |

#### Issue Workflow Information

| Script | Description |
|--------|-------------|
| `get_workflow_for_issue.py` | Get workflow info for a specific issue |

### Workflow Management Examples

#### Listing Workflows

```bash
# List all workflows
python list_workflows.py
python list_workflows.py --output json

# Filter by name
python list_workflows.py --name "Software Development"
python list_workflows.py --name "Bug"

# Filter by scope
python list_workflows.py --scope global
python list_workflows.py --scope project

# Show usage information
python list_workflows.py --show-usage

# Pagination
python list_workflows.py --page 1 --page-size 20
python list_workflows.py --all
```

#### Getting Workflow Details

```bash
# Get workflow by name
python get_workflow.py --name "Software Development Workflow"

# Get by entity ID
python get_workflow.py --entity-id "c6c7e6b0-19c4-4516-9a47-93f76124d4d4"

# Show statuses
python get_workflow.py --name "Bug Workflow" --show-statuses

# Show transitions with from/to statuses
python get_workflow.py --name "Bug Workflow" --show-transitions

# Show transition rules (conditions, validators, post-functions)
python get_workflow.py --name "Bug Workflow" --show-rules

# Show which schemes use this workflow
python get_workflow.py --name "Bug Workflow" --show-schemes

# Full details
python get_workflow.py --name "Software Development Workflow" \
  --show-statuses --show-transitions --show-rules --show-schemes

# JSON output
python get_workflow.py --name "Bug Workflow" --output json
```

#### Searching Workflows

```bash
# Search by name pattern
python search_workflows.py --name "Development"
python search_workflows.py --name "Bug"

# Search with expansion
python search_workflows.py --name "Dev" --expand transitions
python search_workflows.py --expand statuses,transitions

# Filter by scope
python search_workflows.py --scope global
python search_workflows.py --scope project

# Filter by active/inactive status
python search_workflows.py --active-only
python search_workflows.py --inactive-only

# Order results
python search_workflows.py --order-by name
python search_workflows.py --order-by created

# Combined filters
python search_workflows.py --name "Bug" --scope global --active-only

# JSON output
python search_workflows.py --name "Dev" --output json
```

#### Listing Workflow Schemes

```bash
# List all workflow schemes
python list_workflow_schemes.py
python list_workflow_schemes.py --output json

# Show issue type mappings
python list_workflow_schemes.py --show-mappings

# Show which projects use each scheme
python list_workflow_schemes.py --show-projects

# Pagination
python list_workflow_schemes.py --page 1 --page-size 10
```

#### Getting Workflow Scheme Details

```bash
# Get scheme by ID
python get_workflow_scheme.py --id 10100

# Get by name
python get_workflow_scheme.py --name "Software Development Scheme"

# Show issue type mappings
python get_workflow_scheme.py --id 10100 --show-mappings

# Show projects using this scheme
python get_workflow_scheme.py --id 10100 --show-projects

# Show draft scheme (if exists)
python get_workflow_scheme.py --id 10100 --show-draft

# JSON output
python get_workflow_scheme.py --id 10100 --output json
```

#### Assigning Workflow Schemes

```bash
# Show current scheme for a project
python assign_workflow_scheme.py --project PROJ --show-current

# Dry run - preview what would change
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 --dry-run

# Assign by scheme ID (requires --confirm)
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 --confirm

# Assign by scheme name
python assign_workflow_scheme.py --project PROJ --scheme "Agile Development Scheme" --confirm

# With status migration mappings from file
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 \
  --mappings status_mappings.json --confirm

# Don't wait for completion (async operation)
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 --confirm --no-wait

# JSON output
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 --dry-run --output json
```

#### Listing Statuses

```bash
# List all statuses
python list_statuses.py
python list_statuses.py --output json

# Filter by category
python list_statuses.py --category TODO
python list_statuses.py --category IN_PROGRESS
python list_statuses.py --category DONE

# Filter by workflow
python list_statuses.py --workflow "Software Development Workflow"

# Group by category
python list_statuses.py --group-by category

# Show workflow usage
python list_statuses.py --show-usage

# Search by name
python list_statuses.py --search "Progress"
```

#### Getting Workflow for an Issue

```bash
# Get basic workflow info for an issue
python get_workflow_for_issue.py PROJ-123

# Show available transitions from current status
python get_workflow_for_issue.py PROJ-123 --show-transitions

# Show workflow scheme information
python get_workflow_for_issue.py PROJ-123 --show-scheme

# Show everything
python get_workflow_for_issue.py PROJ-123 --show-transitions --show-scheme

# JSON output
python get_workflow_for_issue.py PROJ-123 --output json
```

### Status Categories

JIRA groups all statuses into three categories:

| Category | Category Key | Description | Examples |
|----------|--------------|-------------|----------|
| TODO | `new` | Work not yet started | To Do, Open, Backlog |
| IN_PROGRESS | `indeterminate` | Work in progress | In Progress, Code Review, Testing |
| DONE | `done` | Work completed | Done, Closed, Resolved |

### Status Migration Mappings

When assigning a new workflow scheme, you may need to provide status migration mappings if issues exist with statuses that don't exist in the new workflow. Create a JSON file with mappings:

```json
[
  {
    "issueTypeId": "10000",
    "statusMigrations": [
      {"oldStatusId": "1", "newStatusId": "10000"},
      {"oldStatusId": "2", "newStatusId": "10001"}
    ]
  },
  {
    "issueTypeId": "10001",
    "statusMigrations": [
      {"oldStatusId": "1", "newStatusId": "10000"}
    ]
  }
]
```

### Workflow Management Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| List/view workflows | Administer Jira (global) |
| Get workflow details | Administer Jira (global) |
| Search workflows | Administer Jira (global) |
| List/view workflow schemes | Administer Jira (global) |
| Get workflow scheme details | Administer Jira (global) |
| Assign workflow scheme to project | Administer Jira (global) |
| List/view statuses | Browse Projects |
| Get workflow for issue | Browse Projects |

### Workflow Management Important Notes

1. **Workflow creation/modification is NOT supported** via REST API - use JIRA admin UI
2. **Workflow scheme assignment is asynchronous** - may take time for large projects
3. **Status migration may be required** when changing workflow schemes
4. **Default workflow scheme** uses the "jira" built-in workflow for all issue types
5. **Draft schemes** exist when a scheme is being edited but not yet published
6. **Global vs Project scope** - global workflows are available instance-wide
7. **Scheme assignment requires confirmation** - use --dry-run to preview changes

---

## Related Skills

This skill works well in combination with:

| Skill | Use Case |
|-------|----------|
| **jira-issue** | Core issue CRUD operations after configuring projects and issue types |
| **jira-lifecycle** | Workflow transitions (uses workflows configured via this skill) |
| **jira-fields** | Custom field management and discovery for screen configuration |
| **jira-agile** | Sprint and board management for Scrum/Kanban projects |
| **jira-jsm** | Service desk configuration (requires JSM projects created here) |
| **jira-bulk** | Bulk operations across projects managed by this skill |
| **jira-search** | JQL queries leveraging issue types and workflows configured here |
