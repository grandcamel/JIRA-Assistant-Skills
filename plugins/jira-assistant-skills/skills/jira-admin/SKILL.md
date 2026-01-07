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

Comprehensive administration tools for JIRA Cloud covering 8 major subsystems with 84+ scripts.

---

## What This Skill Does

**8 Major Administration Areas:**

| Area | Scripts | Key Operations |
|------|---------|----------------|
| **Project Management** | 14 | Create, configure, archive, restore projects and categories |
| **Automation Rules** | 12 | Discover, manage, invoke automation rules and templates |
| **Permission Schemes** | 7 | Control who can do what across projects |
| **Permission Diagnostics** | 4 | Check permissions, diagnose 403 errors, manage project roles |
| **User & Group Management** | 8 | Find users, create groups, manage membership |
| **Notification Schemes** | 7 | Configure who receives what notifications |
| **Screen Management** | 10 | Control which fields appear in issue workflows |
| **Issue Types & Schemes** | 13 | Define work item types and their availability |
| **Workflow Management** | 9 | Explore and assign issue lifecycle workflows |

---

## Quick Navigation

**In a hurry? Use these:**

### Common Tasks
- [Setting up a new project](docs/WORKFLOWS.md#setting-up-a-new-project-7-steps) - 7 steps
- [Configuring team access](docs/WORKFLOWS.md#configuring-team-access-4-steps) - 4 steps
- [Setting up notifications](docs/WORKFLOWS.md#configuring-notification-rules-for-team-5-steps) - 5 steps

### Choose Your Task
- [I want to do X, find the script](docs/DECISION-TREE.md) - Quick decision tree
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
- List project role memberships
- Add or remove users from project roles

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

**IMPORTANT:** Always use the `jira` CLI. Never run Python scripts directly.

All commands support `--help` for full documentation.

### Project Management
```bash
jira admin project list                    # List all projects
jira admin project get PROJ                # Get project details
jira admin project create                  # Create a new project
jira admin project update PROJ             # Update project settings
jira admin project delete PROJ             # Delete a project
jira admin project archive PROJ            # Archive a project
jira admin project restore PROJ            # Restore archived project
jira admin config get PROJ                 # Get project configuration
jira admin category list                   # List project categories
jira admin category create                 # Create a category
jira admin category assign PROJ            # Assign category to project
```

### Automation Rules
```bash
jira admin automation list --project PROJ  # List automation rules
jira admin automation get RULE_ID          # Get rule details
jira admin automation enable RULE_ID       # Enable a rule
jira admin automation disable RULE_ID      # Disable a rule
jira admin automation invoke RULE_ID       # Invoke manual rule
jira admin automation-template list        # List rule templates
```

### Permission Schemes
```bash
jira admin permission-scheme list          # List permission schemes
jira admin permission-scheme get ID        # Get scheme details
jira admin permission-scheme create        # Create new scheme
jira admin permission-scheme assign        # Assign scheme to project
jira admin permission list                 # List available permissions
```

### Permission Diagnostics
```bash
# Check your permissions on a project
jira admin permissions check --project DEMO
jira admin permissions check --project DEMO --permission DELETE_ISSUES
jira admin permissions check --project DEMO --only-missing

# List project role memberships
jira admin project roles --project DEMO
jira admin project roles --project DEMO --role Administrators

# Manage project role membership
jira admin project role add --project DEMO --role Administrators --user user@example.com
jira admin project role remove --project DEMO --role Administrators --user user@example.com
```

### User & Group Management
```bash
jira admin user search "name"              # Search for users by name or email
jira admin user get ACCOUNT_ID             # Get user details
jira admin group list                      # List all groups
jira admin group members GROUP_NAME        # Get group members
jira admin group create GROUP_NAME         # Create a group
jira admin group delete GROUP_NAME --confirm  # Delete a group
jira admin group add-user GROUP_NAME --user EMAIL  # Add user to group
jira admin group remove-user GROUP_NAME --user EMAIL --confirm  # Remove user from group
```

### Notification Schemes
```bash
jira admin notification-scheme list        # List notification schemes
jira admin notification-scheme get ID      # Get scheme details
jira admin notification-scheme create      # Create new scheme
jira admin notification add                # Add notification to scheme
jira admin notification remove             # Remove notification
```

### Screen Management
```bash
jira admin screen list                     # List screens
jira admin screen get ID                   # Get screen details
jira admin screen tabs ID                  # List screen tabs
jira admin screen fields ID                # Get fields on screen
jira admin screen add-field SCREEN_ID FIELD_ID  # Add field to screen
jira admin screen remove-field SCREEN_ID FIELD_ID  # Remove field from screen
jira admin screen-scheme list              # List screen schemes
```

### Issue Types
```bash
jira admin issue-type list                 # List issue types
jira admin issue-type get ID               # Get issue type details
jira admin issue-type create               # Create issue type
jira admin issue-type update ID            # Update issue type
jira admin issue-type delete ID            # Delete issue type
```

### Issue Type Schemes
```bash
jira admin issue-type-scheme list          # List schemes
jira admin issue-type-scheme get ID        # Get scheme details
jira admin issue-type-scheme create        # Create new scheme
jira admin issue-type-scheme assign        # Assign to project
jira admin issue-type-scheme project       # Get project's scheme
```

### Workflow Management
```bash
jira admin workflow list                   # List workflows
jira admin workflow get --name "Name"      # Get workflow details
jira admin workflow search --query "term"  # Search workflows
jira admin workflow-scheme list            # List workflow schemes
jira admin workflow-scheme get --id ID     # Get scheme details
jira admin workflow-scheme assign          # Assign to project
jira admin status list                     # List all statuses
```

---

## Getting Started

### 30-Second Start

```bash
# List all projects
jira admin project list

# See project configuration
jira admin config get PROJ

# Search for users
jira admin user search "john" --include-groups
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
jira admin project delete PROJ --dry-run
jira admin group delete GROUP_NAME --dry-run
jira admin permission-scheme assign --project PROJ --scheme 10050 --dry-run
```

### JSON Output for Scripting
```bash
jira admin project list --output json
jira admin workflow get --name "Workflow" --output json
```

### Profile Selection
```bash
jira admin project list --profile production
jira admin project get PROJ --profile development
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
jira admin permissions check --project DEMO

# Show only permissions you're missing
jira admin permissions check --project DEMO --only-missing

# Check specific permission (e.g., DELETE_ISSUES)
jira admin permissions check --project DEMO --permission DELETE_ISSUES

# See who has access via project roles
jira admin project roles --project DEMO

# Add yourself to Administrators role if needed
jira admin project role add --project DEMO --role Administrators --user your@email.com
```

### Verify Permissions
```bash
jira admin user search "your.name" --include-groups
jira admin project list --type software
```

### Check Configuration
```bash
jira admin config get PROJ --show-schemes
jira admin issue-type-scheme project --project-id 10000
```

### Debug Scheme Assignments
```bash
jira admin permission-scheme get 10000 --show-projects
jira admin workflow-scheme get --id 10100 --show-projects
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
│   ├── DECISION-TREE.md     # Find the right script
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
├── assets/templates/        # JSON templates
└── scripts/                 # All 84+ Python scripts
```
