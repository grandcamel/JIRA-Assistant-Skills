# JIRA Admin Quick Reference

One-page command reference for jira-admin scripts. Use Ctrl+F to find what you need.

---

## Projects

```bash
# Create
python create_project.py --key X --name X --type software --template scrum
python create_project.py --key X --name X --type business
python create_project.py --key X --name X --lead email@example.com

# Read
python get_project.py PROJ
python get_project.py PROJ --show-components --show-versions
python list_projects.py
python list_projects.py --type software
python list_projects.py --search "name"
python list_projects.py --include-archived
python list_projects.py --trash
python get_config.py PROJ --show-schemes

# Update
python update_project.py PROJ --name X
python update_project.py PROJ --lead email@example.com
python update_project.py PROJ --description X --url X
python set_project_lead.py PROJ --lead email@example.com
python set_default_assignee.py PROJ --type PROJECT_LEAD
python set_avatar.py PROJ --file path/to/image.png

# Delete/Archive
python delete_project.py PROJ [--yes] [--dry-run]
python archive_project.py PROJ [--yes] [--dry-run]
python restore_project.py PROJ

# Categories
python create_category.py --name X [--description X]
python list_categories.py
python assign_category.py PROJ --category X
python assign_category.py PROJ --remove
```

---

## Automation

```bash
# List/Search
python list_automation_rules.py
python list_automation_rules.py --project PROJ
python list_automation_rules.py --state enabled
python get_automation_rule.py RULE_ID
python get_automation_rule.py --name "Rule Name"
python search_automation_rules.py --trigger issue_created
python search_automation_rules.py --state disabled

# Enable/Disable
python enable_automation_rule.py RULE_ID [--dry-run]
python disable_automation_rule.py RULE_ID [--confirm] [--dry-run]
python toggle_automation_rule.py RULE_ID

# Manual Rules
python list_manual_rules.py [--context issue]
python invoke_manual_rule.py RULE_ID --issue PROJ-123
python invoke_manual_rule.py RULE_ID --issue PROJ-123 --property '{"key": "value"}'

# Templates
python list_automation_templates.py
python list_automation_templates.py --category "Issue Management"
python get_automation_template.py TEMPLATE_ID
python create_rule_from_template.py TEMPLATE_ID --project PROJ [--name X] [--dry-run]
python update_automation_rule.py RULE_ID --name X [--description X]
```

---

## Permissions

```bash
# List/View
python list_permission_schemes.py
python list_permission_schemes.py --show-grants
python list_permission_schemes.py --show-projects
python get_permission_scheme.py 10000
python get_permission_scheme.py "Scheme Name"
python get_permission_scheme.py 10000 --show-projects
python get_permission_scheme.py 10000 --export-template grants.json
python list_permissions.py
python list_permissions.py --type PROJECT
python list_permissions.py --search "issue"

# Create
python create_permission_scheme.py --name X [--description X]
python create_permission_scheme.py --name X --template grants.json
python create_permission_scheme.py --name X --clone 10000
python create_permission_scheme.py --name X --grant "PERMISSION:TYPE[:PARAM]"

# Update
python update_permission_scheme.py 10000 --name X
python update_permission_scheme.py 10000 --add-grant "PERM:TYPE[:PARAM]"
python update_permission_scheme.py 10000 --remove-grant 10103
python update_permission_scheme.py 10000 --remove-grant "PERM:TYPE[:PARAM]"

# Delete
python delete_permission_scheme.py 10050 --confirm
python delete_permission_scheme.py 10050 --check-only
python delete_permission_scheme.py 10050 --force --confirm

# Assign
python assign_permission_scheme.py --project PROJ --scheme 10050
python assign_permission_scheme.py --projects A,B,C --scheme "Name"
python assign_permission_scheme.py --project PROJ --show-current
```

### Permission Grant Format
```
PERMISSION:HOLDER_TYPE[:HOLDER_PARAMETER]

BROWSE_PROJECTS:anyone
CREATE_ISSUES:group:developers
EDIT_ISSUES:projectRole:Developers
ADMINISTER_PROJECTS:projectLead
RESOLVE_ISSUES:user:account-id
```

---

## Users & Groups

```bash
# Users
python search_users.py "query"
python search_users.py "query" --project PROJ --assignable
python search_users.py --me --include-groups
python get_user.py --email X
python get_user.py --account-id X
python get_user.py --me --include-groups

# Groups
python list_groups.py
python list_groups.py --query "name"
python list_groups.py --include-members
python get_group_members.py "group-name"
python get_group_members.py "group-name" --include-inactive
python create_group.py "group-name" [--dry-run]
python delete_group.py "group-name" --confirm
python delete_group.py "group-name" --swap "new-group" --confirm

# Membership
python add_user_to_group.py email@example.com --group "name" [--dry-run]
python add_user_to_group.py --account-id X --group "name"
python remove_user_from_group.py email@example.com --group "name" --confirm
```

---

## Notifications

```bash
# List/View
python list_notification_schemes.py
python list_notification_schemes.py --filter "name"
python list_notification_schemes.py --show-events
python get_notification_scheme.py 10000
python get_notification_scheme.py --name "Name"
python get_notification_scheme.py 10000 --show-projects

# Create
python create_notification_scheme.py --name X [--description X]
python create_notification_scheme.py --name X --event "Event" --notify Type
python create_notification_scheme.py --template template.json

# Update
python update_notification_scheme.py 10000 --name X
python update_notification_scheme.py 10000 --description X

# Add/Remove Notifications
python add_notification.py 10000 --event "Issue created" --notify CurrentAssignee
python add_notification.py 10000 --event "Issue created" --notify Group:developers
python add_notification.py 10000 --event-id 1 --notify Reporter
python remove_notification.py 10000 --notification-id 12
python remove_notification.py 10000 --event "Event" --recipient Type

# Delete
python delete_notification_scheme.py 10050 [--force] [--dry-run]
```

### Notification Recipients
```
CurrentAssignee, Reporter, AllWatchers, ProjectLead, ComponentLead, CurrentUser
Group:group-name
ProjectRole:role-id
User:account-id
```

---

## Screens

```bash
# Screens
python list_screens.py
python list_screens.py --filter "name"
python get_screen.py 1
python get_screen.py 1 --tabs --fields
python list_screen_tabs.py 1
python get_screen_fields.py 1
python get_screen_fields.py 1 --tab 10000

# Add/Remove Fields
python add_field_to_screen.py 1 customfield_10016 [--tab X] [--dry-run]
python add_field_to_screen.py 1 customfield_10016 --tab-name "Tab Name"
python remove_field_from_screen.py 1 customfield_10016 [--force] [--dry-run]

# Screen Schemes
python list_screen_schemes.py
python get_screen_scheme.py 1

# Issue Type Screen Schemes
python list_issue_type_screen_schemes.py
python get_issue_type_screen_scheme.py 10000 --mappings

# Project Discovery
python get_project_screens.py PROJ
python get_project_screens.py PROJ --full
python get_project_screens.py PROJ --full --operation create
```

---

## Issue Types

```bash
# List/View
python list_issue_types.py
python list_issue_types.py --subtask-only
python list_issue_types.py --standard-only
python list_issue_types.py --hierarchy-level 0
python get_issue_type.py 10001
python get_issue_type.py 10001 --show-alternatives

# Create
python create_issue_type.py --name X [--description X]
python create_issue_type.py --name X --type subtask
python create_issue_type.py --name X --hierarchy-level 1

# Update
python update_issue_type.py 10001 --name X
python update_issue_type.py 10001 --description X
python update_issue_type.py 10001 --avatar-id 10204

# Delete
python delete_issue_type.py 10050 [--force]
python delete_issue_type.py 10050 --alternative-id 10001
```

---

## Issue Type Schemes

```bash
# List/View
python list_issue_type_schemes.py
python list_issue_type_schemes.py --order-by name
python get_issue_type_scheme.py 10001
python get_issue_type_scheme.py 10001 --include-items
python get_issue_type_scheme_mappings.py

# Create
python create_issue_type_scheme.py --name X --issue-type-ids 10001 10002
python create_issue_type_scheme.py --name X --issue-type-ids 10001 --default-issue-type-id 10001

# Update
python update_issue_type_scheme.py 10001 --name X
python update_issue_type_scheme.py 10001 --default-issue-type-id 10002

# Delete
python delete_issue_type_scheme.py 10050 [--force]

# Assign
python get_project_issue_type_scheme.py --project-id 10000
python assign_issue_type_scheme.py --scheme-id 10001 --project-id 10000 [--dry-run]

# Manage Types
python add_issue_types_to_scheme.py --scheme-id 10001 --issue-type-ids 10003 10004
python remove_issue_type_from_scheme.py --scheme-id 10001 --issue-type-id 10003 [--force]
python reorder_issue_types_in_scheme.py --scheme-id 10001 --issue-type-id 10003
python reorder_issue_types_in_scheme.py --scheme-id 10001 --issue-type-id 10003 --after 10001
```

---

## Workflows

```bash
# List/View
python list_workflows.py
python list_workflows.py --name "name"
python list_workflows.py --scope global
python list_workflows.py --show-usage
python get_workflow.py --name "Workflow Name"
python get_workflow.py --name "Name" --show-statuses
python get_workflow.py --name "Name" --show-transitions
python get_workflow.py --name "Name" --show-rules
python get_workflow.py --name "Name" --show-schemes
python search_workflows.py --name "pattern"
python search_workflows.py --scope global --active-only

# Workflow Schemes
python list_workflow_schemes.py
python list_workflow_schemes.py --show-mappings
python list_workflow_schemes.py --show-projects
python get_workflow_scheme.py --id 10100
python get_workflow_scheme.py --name "Name"
python get_workflow_scheme.py --id 10100 --show-mappings

# Assign Scheme
python assign_workflow_scheme.py --project PROJ --show-current
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 --dry-run
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 --confirm
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 --mappings file.json --confirm

# Statuses
python list_statuses.py
python list_statuses.py --category TODO
python list_statuses.py --category IN_PROGRESS
python list_statuses.py --category DONE
python list_statuses.py --workflow "Name"
python list_statuses.py --show-usage

# Issue Workflow
python get_workflow_for_issue.py PROJ-123
python get_workflow_for_issue.py PROJ-123 --show-transitions
python get_workflow_for_issue.py PROJ-123 --show-scheme
```

---

## Common Patterns

### Dry-Run First
```bash
python <script>.py <args> --dry-run
# Review output
python <script>.py <args> --confirm  # or --yes
```

### JSON Output
```bash
python <script>.py <args> --output json
python <script>.py <args> --format json
```

### Profile Selection
```bash
python <script>.py <args> --profile development
python <script>.py <args> --profile production
```

### Pagination
```bash
python <script>.py --start-at 0 --max-results 100
python <script>.py --page 1 --page-size 50
python <script>.py --all
```

---

## Magic Numbers

```
# Common custom field IDs (instance-specific!)
Epic Link: customfield_10014
Story Points: customfield_10016
Sprint: customfield_10020

# Notification Event IDs
Issue Created: 1
Issue Updated: 2
Issue Assigned: 3
Issue Resolved: 4
Issue Closed: 5
Issue Commented: 6

# Status Categories
TODO: new
IN_PROGRESS: indeterminate
DONE: done
```

See [VOODOO_CONSTANTS.md](VOODOO_CONSTANTS.md) for complete reference.

---

## Tips

1. **Use `--help`** on any script for full documentation
2. **Use `--dry-run`** before mutating operations
3. **Use `--output json`** for scripting and automation
4. **Use `--profile`** to target specific JIRA instances
5. **Discover custom field IDs** with `get_config.py PROJ`
