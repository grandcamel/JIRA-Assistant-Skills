---
name: "jira-administration"
description: >
  Complete JIRA project and system administration including projects,
  automation rules, permissions, users, notifications, screens, issue types,
  and workflows. Use when managing project structure, automating work,
  configuring team access, or setting up issue tracking.
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# JIRA Admin Skill

Comprehensive administration tools for JIRA Cloud covering 8 major subsystems.

## Risk Levels

| Operation | Risk | Notes |
|-----------|------|-------|
| List/get (any resource) | `-` | Read-only |
| Search users | `-` | Read-only |
| Check permissions | `-` | Read-only |
| Create project | `-` | Easily reversible (can delete) |
| Create group | `-` | Easily reversible (can delete) |
| Create permission/notification scheme | `-` | Can delete |
| Create issue type | `-` | Can delete |
| Update project settings | `!` | Can be undone |
| Update permission scheme | `!` | Can be modified |
| Enable/disable automation | `!` | Can toggle back |
| Invoke automation rule | `!` | Rule executes; effects vary |
| Add user to group/role | `!` | Can remove |
| Remove user from group/role | `!` | Can re-add |
| Assign scheme to project | `!` | Can reassign |
| Archive project | `!` | Can restore |
| Add/remove screen fields | `!` | Can reverse |
| Delete issue type | `!!` | Issues lose type |
| Delete group | `!!` | Members lose group access |
| Delete permission scheme | `!!` | Projects lose permissions |
| Delete project | `!!!` | **IRREVERSIBLE** - all issues lost |

**Risk Legend**: `-` Safe, read-only | `!` Caution, modifiable | `!!` Warning, destructive but recoverable | `!!!` Danger, irreversible

**CRITICAL**: Project deletion is irreversible. Always use `--dry-run` when available.

---

## What This Skill Does

**8 Major Administration Areas:**

| Area | Key Operations |
|------|----------------|
| **Project Management** | Create, configure, archive, restore projects and categories |
| **Automation Rules** | Discover, manage, invoke automation rules and templates |
| **Permission Schemes** | Control who can do what across projects |
| **Permission Diagnostics** | Check permissions, diagnose 403 errors |
| **User & Group Management** | Find users, create groups, manage membership |
| **Notification Schemes** | Configure who receives what notifications |
| **Screen Management** | Control which fields appear in issue workflows |
| **Issue Types & Schemes** | Define work item types and their availability |
| **Workflow Management** | Explore and assign issue lifecycle workflows |

---

## Quick Navigation

**In a hurry? Use these:**

### Common Tasks
- [Setting up a new project](docs/WORKFLOWS.md#setting-up-a-new-project-7-steps) - 7 steps
- [Configuring team access](docs/WORKFLOWS.md#configuring-team-access-4-steps) - 4 steps
- [Setting up notifications](docs/WORKFLOWS.md#configuring-notification-rules-for-team-5-steps) - 5 steps

### Choose Your Task
- [I want to do X, find the command](docs/DECISION-TREE.md) - Quick decision tree
- [I need command syntax](docs/QUICK-REFERENCE.md) - One-page cheat sheet
- [I'm learning JIRA admin](docs/BEST_PRACTICES.md) - Comprehensive best practices
- [I need detailed guides](docs/subsystems/) - Per-subsystem deep dives

---

## When to Use This Skill

Reach for this skill when you need to:

**Setting up projects:**
- Create new JIRA projects with appropriate templates
- Configure project settings (lead, default assignee, avatar)
- Archive inactive projects or restore deleted ones
- Organize projects with categories

**Configuring access:**
- Define who can view, create, or edit issues
- Create and manage permission schemes
- Assign schemes to projects

**Diagnosing permission issues:**
- Check which permissions you have on a project
- Identify why a 403 Forbidden error occurred

**Automating work:**
- List, enable, disable, or invoke automation rules
- Create rules from templates
- Manage rule states during bulk operations

**Managing users:**
- Search for users by name or email
- Create and manage groups
- Add/remove users from groups

**Setting up notifications:**
- Configure who gets notified about issue changes
- Create targeted notification schemes
- Minimize notification noise

**Configuring screens:**
- Add or remove fields from screens
- Discover project screen configurations
- Understand the 3-tier screen hierarchy

**Organizing issue types:**
- Create custom issue types
- Manage issue type schemes
- Assign schemes to projects

**Managing workflows:**
- View workflows and their transitions
- Assign workflow schemes to projects
- List and filter statuses

---

## Available Commands

**IMPORTANT:** Always use the `jira-as` CLI. Never run Python scripts directly.

All commands support `--help` for full documentation.

### Project Management
```bash
jira-as admin project list                    # List all projects
jira-as admin project get PROJ                # Get project details
jira-as admin project create                  # Create a new project
jira-as admin project update PROJ             # Update project settings
jira-as admin project delete PROJ             # Delete a project
jira-as admin project archive PROJ            # Archive a project
jira-as admin project restore PROJ            # Restore archived project
jira-as admin config get PROJ                 # Get project configuration
jira-as admin category list                   # List project categories
jira-as admin category create                 # Create a category
jira-as admin category assign PROJ            # Assign category to project
```

### Automation Rules
```bash
jira-as admin automation list --project PROJ  # List automation rules
jira-as admin automation list --state enabled # Filter by state (enabled, disabled)
jira-as admin automation list --project PROJ --state enabled  # Combined filters
jira-as admin automation get RULE_ID          # Get rule details
jira-as admin automation search --query "term"  # Search automation rules
jira-as admin automation enable RULE_ID       # Enable a rule
jira-as admin automation disable RULE_ID      # Disable a rule
jira-as admin automation toggle RULE_ID       # Toggle rule enabled state
jira-as admin automation invoke RULE_ID       # Invoke manual rule
jira-as admin automation-template list        # List rule templates
jira-as admin automation-template get TEMPLATE_ID  # Get template details
```

### Permission Schemes
```bash
jira-as admin permission-scheme list          # List permission schemes
jira-as admin permission-scheme get ID        # Get scheme details
jira-as admin permission-scheme create        # Create new scheme
jira-as admin permission-scheme assign        # Assign scheme to project
jira-as admin permission list                 # List available permissions
```

### Permission Diagnostics
```bash
# Check your permissions on a project
jira-as admin permission check --project DEMO
```

### User & Group Management
```bash
# User search with filtering options
jira-as admin user search "name"              # Search for users by name or email
jira-as admin user search "john" -g           # Include group memberships in output (-g/--include-groups)
jira-as admin user search "" -p PROJ -a       # Find users assignable to project (-a/--assignable)
jira-as admin user search "" --all            # Include inactive users (--all, no short form)
jira-as admin user search "" --all --max-results 100  # Limit results
jira-as admin user get ACCOUNT_ID             # Get user details

# Group management
jira-as admin group list                      # List all groups
jira-as admin group members GROUP_NAME        # Get group members
jira-as admin group create GROUP_NAME         # Create a group
jira-as admin group delete GROUP_NAME -y      # Delete with confirmation (-y/--confirm)
jira-as admin group delete GROUP_NAME --dry-run  # Preview deletion
jira-as admin group add-user GROUP_NAME --user EMAIL  # Add user to group
jira-as admin group remove-user GROUP_NAME --user EMAIL -y  # Remove user (-y/--confirm)
```

### Notification Schemes
```bash
jira-as admin notification-scheme list        # List notification schemes
jira-as admin notification-scheme get ID      # Get scheme details
jira-as admin notification-scheme create      # Create new scheme
jira-as admin notification add                # Add notification to scheme
jira-as admin notification remove             # Remove notification
```

### Screen Management
```bash
jira-as admin screen list                     # List screens
jira-as admin screen get ID                   # Get screen details
jira-as admin screen tabs ID                  # List screen tabs
jira-as admin screen fields ID                # Get fields on screen
jira-as admin screen add-field SCREEN_ID FIELD_ID  # Add field to screen
jira-as admin screen remove-field SCREEN_ID FIELD_ID  # Remove field from screen
jira-as admin screen-scheme list              # List screen schemes
jira-as admin screen-scheme get SCHEME_ID     # Get screen scheme details
```

### Issue Types
```bash
jira-as admin issue-type list                 # List issue types
jira-as admin issue-type get ID               # Get issue type details
jira-as admin issue-type create               # Create issue type
jira-as admin issue-type update ID            # Update issue type
jira-as admin issue-type delete ID            # Delete issue type
```

### Issue Type Schemes
```bash
jira-as admin issue-type-scheme list          # List schemes
jira-as admin issue-type-scheme get ID        # Get scheme details
jira-as admin issue-type-scheme create        # Create new scheme
jira-as admin issue-type-scheme assign        # Assign to project
jira-as admin issue-type-scheme project       # Get project's scheme
```

### Workflow Management
```bash
jira-as admin workflow list                   # List workflows
jira-as admin workflow get --name "Name"      # Get workflow details
jira-as admin workflow search --query "term"  # Search workflows
jira-as admin workflow for-issue ISSUE_KEY    # Get workflow for specific issue
jira-as admin workflow-scheme list            # List workflow schemes
jira-as admin workflow-scheme get --id ID     # Get scheme details
jira-as admin workflow-scheme assign          # Assign to project
jira-as admin status list                     # List all statuses
```

---

## Getting Started

### 30-Second Start

```bash
# List all projects
jira-as admin project list

# See project configuration
jira-as admin config get PROJ

# Search for users
jira-as admin user search "john" --include-groups
```

### Next Steps

1. **For detailed examples:** See [docs/subsystems/](docs/subsystems/)
2. **For step-by-step workflows:** See [docs/WORKFLOWS.md](docs/WORKFLOWS.md)
3. **For command reference:** See [docs/QUICK-REFERENCE.md](docs/QUICK-REFERENCE.md)
4. **For best practices:** See [docs/BEST_PRACTICES.md](docs/BEST_PRACTICES.md)
5. **To find the right script:** See [docs/DECISION-TREE.md](docs/DECISION-TREE.md)

---

## Common Patterns

### Preview Before Changing
```bash
jira-as admin project delete PROJ --dry-run
jira-as admin group delete GROUP_NAME --dry-run
jira-as admin permission-scheme assign --project PROJ --scheme 10050 --dry-run
```

### JSON Output for Scripting
```bash
jira-as admin project list --output json
jira-as admin workflow get --name "Workflow" --output json
```

### Profile Selection
```bash
```

---

## Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| Project CRUD | Administer Jira (global) |
| Permission Schemes | Administer Jira (global) |
| Automation Rules | Administer Jira or Project Admin |
| Notification Schemes | Administer Jira (global) |
| Screen Management | Administer Jira (global) |
| Issue Types | Administer Jira (global) |
| Workflows (view) | Administer Jira (global) |
| User/Group (write) | Site Administration |
| User/Group (read) | Browse Users and Groups |

---

## Common Errors

| Error | Solution |
|-------|----------|
| 403 Forbidden | Verify you have "Administer Jira" permission |
| 404 Not Found | Check project key, scheme ID, or resource spelling |
| 409 Conflict | Resource exists - choose different name/key |
| 400 Bad Request | Validate input format (see script --help) |

---

## Troubleshooting

### Diagnose 403 Forbidden Errors
```bash
# Check what permissions you have on a project
jira-as admin permission check --project DEMO
```

### Verify Permissions
```bash
jira-as admin user search "your.name" --include-groups
jira-as admin project list --type software
```

### Check Configuration
```bash
jira-as admin config get PROJ --show-schemes
jira-as admin issue-type-scheme project --project-id 10000
```

### Debug Scheme Assignments
```bash
jira-as admin permission-scheme get 10000 --show-projects
jira-as admin workflow-scheme get --id 10100 --show-projects
```

---

## Template Files

JSON templates for common operations are available in `assets/templates/`:

| Template | Purpose |
|----------|---------|
| `notification_scheme_minimal.json` | Minimal notifications |
| `notification_scheme_basic.json` | Common event-recipient mappings |
| `notification_scheme_comprehensive.json` | Full notifications |

---

## Subsystem Guides

Detailed documentation for each administration area:

| Guide | Content |
|-------|---------|
| [project-management-guide.md](docs/subsystems/project-management-guide.md) | Projects, categories, configuration |
| [automation-rules-guide.md](docs/subsystems/automation-rules-guide.md) | Rules, templates, state management |
| [permission-schemes-guide.md](docs/subsystems/permission-schemes-guide.md) | Permissions, grants, assignment |
| [user-group-guide.md](docs/subsystems/user-group-guide.md) | Users, groups, membership |
| [notification-schemes-guide.md](docs/subsystems/notification-schemes-guide.md) | Events, recipients, schemes |
| [screen-management-guide.md](docs/subsystems/screen-management-guide.md) | Screens, tabs, fields |
| [issue-types-guide.md](docs/subsystems/issue-types-guide.md) | Issue type CRUD |
| [issue-type-schemes-guide.md](docs/subsystems/issue-type-schemes-guide.md) | Scheme management |
| [workflow-management-guide.md](docs/subsystems/workflow-management-guide.md) | Workflows, statuses, schemes |

---

## Related Skills

This skill works well in combination with:

| Skill | Use Case |
|-------|----------|
| **jira-issue** | Core issue CRUD operations (uses projects created here) |
| **jira-lifecycle** | Workflow transitions (uses workflows configured here) |
| **jira-fields** | Custom field discovery (integrates with screens) |
| **jira-agile** | Sprint and board management (uses projects created here) |
| **jira-jsm** | Service desk configuration (requires JSM projects) |
| **jira-bulk** | Bulk operations (uses permission schemes) |
| **jira-search** | JQL queries (uses issue types configured here) |
| **jira-ops** | Cache management (optimizes admin operations) |

---

## Best Practices

For comprehensive guidance on JIRA administration, see [docs/BEST_PRACTICES.md](docs/BEST_PRACTICES.md), which covers:

- Project naming conventions and lifecycle management
- Permission scheme design patterns
- Automation rule design principles
- Notification scheme optimization
- Screen management hierarchy
- Issue type and scheme strategies
- Workflow discovery and assignment
- Security considerations
- Performance optimization
- Common pitfalls and solutions

---

## Documentation Structure

```
jira-admin/
├── SKILL.md                 # This file - skill overview (discovery)
├── docs/
│   ├── BEST_PRACTICES.md    # Comprehensive best practices
│   ├── DECISION-TREE.md     # Find the right command
│   ├── WORKFLOWS.md         # Step-by-step workflows
│   ├── QUICK-REFERENCE.md   # Command syntax reference
│   ├── VOODOO_CONSTANTS.md  # Field IDs, event IDs, constants
│   └── subsystems/          # Detailed per-area guides
│       ├── project-management-guide.md
│       ├── automation-rules-guide.md
│       ├── permission-schemes-guide.md
│       ├── user-group-guide.md
│       ├── notification-schemes-guide.md
│       ├── screen-management-guide.md
│       ├── issue-types-guide.md
│       ├── issue-type-schemes-guide.md
│       └── workflow-management-guide.md
└── assets/templates/        # JSON templates
```
