---
name: "JIRA Administration"
description: >
  Complete JIRA project and system administration including projects,
  automation rules, permissions, users, notifications, screens, issue types,
  and workflows. Use when managing project structure, automating work,
  configuring team access, or setting up issue tracking.
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

## 84 Available Scripts

All scripts support `--help` for full documentation. Run `jira <command> --help` for details.

### Project Management (14 scripts)
```
create_project.py     get_project.py      list_projects.py
update_project.py     delete_project.py   archive_project.py
restore_project.py    get_config.py       create_category.py
list_categories.py    assign_category.py  set_avatar.py
set_project_lead.py   set_default_assignee.py
```

### Automation Rules (12 scripts)
```
list_automation_rules.py      get_automation_rule.py
search_automation_rules.py    enable_automation_rule.py
disable_automation_rule.py    toggle_automation_rule.py
list_manual_rules.py          invoke_manual_rule.py
list_automation_templates.py  get_automation_template.py
create_rule_from_template.py  update_automation_rule.py
```

### Permission Schemes (7 scripts)
```
list_permission_schemes.py    get_permission_scheme.py
create_permission_scheme.py   update_permission_scheme.py
delete_permission_scheme.py   assign_permission_scheme.py
list_permissions.py
```

### User & Group Management (8 scripts)
```
search_users.py          get_user.py
list_groups.py           get_group_members.py
create_group.py          delete_group.py
add_user_to_group.py     remove_user_from_group.py
```

### Notification Schemes (7 scripts)
```
list_notification_schemes.py   get_notification_scheme.py
create_notification_scheme.py  update_notification_scheme.py
add_notification.py            remove_notification.py
delete_notification_scheme.py
```

### Screen Management (10 scripts)
```
list_screens.py               get_screen.py
list_screen_tabs.py           get_screen_fields.py
add_field_to_screen.py        remove_field_from_screen.py
list_screen_schemes.py        get_screen_scheme.py
list_issue_type_screen_schemes.py  get_issue_type_screen_scheme.py
get_project_screens.py
```

### Issue Types (5 scripts)
```
list_issue_types.py   get_issue_type.py    create_issue_type.py
update_issue_type.py  delete_issue_type.py
```

### Issue Type Schemes (8 scripts)
```
list_issue_type_schemes.py       get_issue_type_scheme.py
create_issue_type_scheme.py      update_issue_type_scheme.py
delete_issue_type_scheme.py      assign_issue_type_scheme.py
get_project_issue_type_scheme.py get_issue_type_scheme_mappings.py
add_issue_types_to_scheme.py     remove_issue_type_from_scheme.py
reorder_issue_types_in_scheme.py
```

### Workflow Management (9 scripts)
```
list_workflows.py            get_workflow.py
search_workflows.py          list_workflow_schemes.py
get_workflow_scheme.py       assign_workflow_scheme.py
list_statuses.py             get_workflow_for_issue.py
```

---

## Getting Started

### 30-Second Start

```bash
# List all projects
jira admin project list

# See project configuration
jira admin config get PROJ

# Check current user permissions
jira admin user search --me --include-groups
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

### Verify Permissions
```bash
jira admin user search --me --include-groups
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
