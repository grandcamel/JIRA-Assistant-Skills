# Which Script Should I Use?

Quick-reference decision tree for finding the right jira-admin script. Use Ctrl+F to search for your task.

---

## I want to manage PROJECTS

| Task | Script | Example |
|------|--------|---------|
| Create a new project | `create_project.py` | `python create_project.py --key MOBILE --name "Mobile App" --type software` |
| View project details | `get_project.py` | `python get_project.py PROJ` |
| List all projects | `list_projects.py` | `python list_projects.py` |
| Update project name/lead | `update_project.py` | `python update_project.py PROJ --name "New Name"` |
| Delete a project | `delete_project.py` | `python delete_project.py PROJ --yes` |
| Archive inactive project | `archive_project.py` | `python archive_project.py PROJ --yes` |
| Restore deleted project | `restore_project.py` | `python restore_project.py PROJ` |
| View complete configuration | `get_config.py` | `python get_config.py PROJ --show-schemes` |
| Create project category | `create_category.py` | `python create_category.py --name "Development"` |
| List categories | `list_categories.py` | `python list_categories.py` |
| Assign category to project | `assign_category.py` | `python assign_category.py PROJ --category "Development"` |
| Set project avatar | `set_avatar.py` | `python set_avatar.py PROJ --file logo.png` |
| Change project lead | `set_project_lead.py` | `python set_project_lead.py PROJ --lead alice@example.com` |
| Set default assignee | `set_default_assignee.py` | `python set_default_assignee.py PROJ --type PROJECT_LEAD` |

**Detailed Guide:** [subsystems/project-management-guide.md](subsystems/project-management-guide.md)

---

## I want to configure AUTOMATION

| Task | Script | Example |
|------|--------|---------|
| List automation rules | `list_automation_rules.py` | `python list_automation_rules.py --project PROJ` |
| Get rule details | `get_automation_rule.py` | `python get_automation_rule.py RULE_ID` |
| Search rules | `search_automation_rules.py` | `python search_automation_rules.py --state enabled` |
| Enable a rule | `enable_automation_rule.py` | `python enable_automation_rule.py RULE_ID` |
| Disable a rule | `disable_automation_rule.py` | `python disable_automation_rule.py RULE_ID --confirm` |
| Toggle rule state | `toggle_automation_rule.py` | `python toggle_automation_rule.py RULE_ID` |
| List manual rules | `list_manual_rules.py` | `python list_manual_rules.py --context issue` |
| Invoke manual rule | `invoke_manual_rule.py` | `python invoke_manual_rule.py RULE_ID --issue PROJ-123` |
| List templates | `list_automation_templates.py` | `python list_automation_templates.py` |
| Get template details | `get_automation_template.py` | `python get_automation_template.py TEMPLATE_ID` |
| Create from template | `create_rule_from_template.py` | `python create_rule_from_template.py TEMPLATE_ID --project PROJ` |
| Update rule config | `update_automation_rule.py` | `python update_automation_rule.py RULE_ID --name "New Name"` |

**Detailed Guide:** [subsystems/automation-rules-guide.md](subsystems/automation-rules-guide.md)

---

## I want to configure PERMISSIONS

| Task | Script | Example |
|------|--------|---------|
| List permission schemes | `list_permission_schemes.py` | `python list_permission_schemes.py` |
| View scheme details | `get_permission_scheme.py` | `python get_permission_scheme.py 10000` |
| Create permission scheme | `create_permission_scheme.py` | `python create_permission_scheme.py --name "New Scheme" --clone 10000` |
| Add permission grants | `update_permission_scheme.py` | `python update_permission_scheme.py 10000 --add-grant "EDIT_ISSUES:group:devs"` |
| Remove grants | `update_permission_scheme.py` | `python update_permission_scheme.py 10000 --remove-grant 10103` |
| Delete scheme | `delete_permission_scheme.py` | `python delete_permission_scheme.py 10050 --confirm` |
| Assign to projects | `assign_permission_scheme.py` | `python assign_permission_scheme.py --project PROJ --scheme 10050` |
| List all permissions | `list_permissions.py` | `python list_permissions.py` |

**Detailed Guide:** [subsystems/permission-schemes-guide.md](subsystems/permission-schemes-guide.md)

---

## I want to manage USERS & GROUPS

| Task | Script | Example |
|------|--------|---------|
| Search for users | `search_users.py` | `python search_users.py "john"` |
| Find assignable users | `search_users.py` | `python search_users.py "john" --project PROJ --assignable` |
| Get current user | `search_users.py` | `python search_users.py --me --include-groups` |
| Get user details | `get_user.py` | `python get_user.py --email john@example.com` |
| List groups | `list_groups.py` | `python list_groups.py` |
| Get group members | `get_group_members.py` | `python get_group_members.py "jira-developers"` |
| Create group | `create_group.py` | `python create_group.py "mobile-team"` |
| Delete group | `delete_group.py` | `python delete_group.py "old-team" --confirm` |
| Add user to group | `add_user_to_group.py` | `python add_user_to_group.py user@email --group "group-name"` |
| Remove user from group | `remove_user_from_group.py` | `python remove_user_from_group.py user@email --group "group-name" --confirm` |

**Detailed Guide:** [subsystems/user-group-guide.md](subsystems/user-group-guide.md)

---

## I want to set up NOTIFICATIONS

| Task | Script | Example |
|------|--------|---------|
| List notification schemes | `list_notification_schemes.py` | `python list_notification_schemes.py` |
| View scheme details | `get_notification_scheme.py` | `python get_notification_scheme.py 10000` |
| Create new scheme | `create_notification_scheme.py` | `python create_notification_scheme.py --name "Team Notifications"` |
| Update scheme metadata | `update_notification_scheme.py` | `python update_notification_scheme.py 10000 --name "Renamed"` |
| Add event notifications | `add_notification.py` | `python add_notification.py 10000 --event "Issue created" --notify Reporter` |
| Remove notifications | `remove_notification.py` | `python remove_notification.py 10000 --notification-id 12` |
| Delete scheme | `delete_notification_scheme.py` | `python delete_notification_scheme.py 10050 --force` |

**Detailed Guide:** [subsystems/notification-schemes-guide.md](subsystems/notification-schemes-guide.md)

---

## I want to manage SCREENS

| Task | Script | Example |
|------|--------|---------|
| List all screens | `list_screens.py` | `python list_screens.py` |
| View screen details | `get_screen.py` | `python get_screen.py 1 --tabs --fields` |
| List screen tabs | `list_screen_tabs.py` | `python list_screen_tabs.py 1` |
| Get screen fields | `get_screen_fields.py` | `python get_screen_fields.py 1` |
| Add field to screen | `add_field_to_screen.py` | `python add_field_to_screen.py 1 customfield_10016` |
| Remove field from screen | `remove_field_from_screen.py` | `python remove_field_from_screen.py 1 customfield_10016` |
| List screen schemes | `list_screen_schemes.py` | `python list_screen_schemes.py` |
| Get screen scheme | `get_screen_scheme.py` | `python get_screen_scheme.py 1` |
| List issue type screen schemes | `list_issue_type_screen_schemes.py` | `python list_issue_type_screen_schemes.py` |
| Get issue type screen scheme | `get_issue_type_screen_scheme.py` | `python get_issue_type_screen_scheme.py 10000` |
| View project screens | `get_project_screens.py` | `python get_project_screens.py PROJ --full` |

**Detailed Guide:** [subsystems/screen-management-guide.md](subsystems/screen-management-guide.md)

---

## I want to manage ISSUE TYPES

| Task | Script | Example |
|------|--------|---------|
| List all issue types | `list_issue_types.py` | `python list_issue_types.py` |
| List subtask types only | `list_issue_types.py` | `python list_issue_types.py --subtask-only` |
| List standard types only | `list_issue_types.py` | `python list_issue_types.py --standard-only` |
| View type details | `get_issue_type.py` | `python get_issue_type.py 10001` |
| Create new type | `create_issue_type.py` | `python create_issue_type.py --name "Feature Request"` |
| Create subtask type | `create_issue_type.py` | `python create_issue_type.py --name "Task" --type subtask` |
| Update type properties | `update_issue_type.py` | `python update_issue_type.py 10001 --name "New Name"` |
| Delete issue type | `delete_issue_type.py` | `python delete_issue_type.py 10050 --alternative-id 10001` |

**Detailed Guide:** [subsystems/issue-types-guide.md](subsystems/issue-types-guide.md)

---

## I want to configure ISSUE TYPE SCHEMES

| Task | Script | Example |
|------|--------|---------|
| List all schemes | `list_issue_type_schemes.py` | `python list_issue_type_schemes.py` |
| View scheme details | `get_issue_type_scheme.py` | `python get_issue_type_scheme.py 10001` |
| Create new scheme | `create_issue_type_scheme.py` | `python create_issue_type_scheme.py --name "Dev Scheme" --issue-type-ids 10001 10002` |
| Update scheme | `update_issue_type_scheme.py` | `python update_issue_type_scheme.py 10001 --name "Updated"` |
| Delete scheme | `delete_issue_type_scheme.py` | `python delete_issue_type_scheme.py 10050` |
| Get project's scheme | `get_project_issue_type_scheme.py` | `python get_project_issue_type_scheme.py --project-id 10000` |
| Assign scheme to project | `assign_issue_type_scheme.py` | `python assign_issue_type_scheme.py --scheme-id 10001 --project-id 10000` |
| Get scheme mappings | `get_issue_type_scheme_mappings.py` | `python get_issue_type_scheme_mappings.py` |
| Add types to scheme | `add_issue_types_to_scheme.py` | `python add_issue_types_to_scheme.py --scheme-id 10001 --issue-type-ids 10003` |
| Remove type from scheme | `remove_issue_type_from_scheme.py` | `python remove_issue_type_from_scheme.py --scheme-id 10001 --issue-type-id 10003` |
| Reorder types in scheme | `reorder_issue_types_in_scheme.py` | `python reorder_issue_types_in_scheme.py --scheme-id 10001 --issue-type-id 10003` |

**Detailed Guide:** [subsystems/issue-type-schemes-guide.md](subsystems/issue-type-schemes-guide.md)

---

## I want to configure WORKFLOWS

| Task | Script | Example |
|------|--------|---------|
| List workflows | `list_workflows.py` | `python list_workflows.py` |
| View workflow details | `get_workflow.py` | `python get_workflow.py --name "Dev Workflow" --show-statuses` |
| Search workflows | `search_workflows.py` | `python search_workflows.py --name "Bug" --scope global` |
| List workflow schemes | `list_workflow_schemes.py` | `python list_workflow_schemes.py --show-mappings` |
| View workflow scheme | `get_workflow_scheme.py` | `python get_workflow_scheme.py --id 10100` |
| Assign scheme to project | `assign_workflow_scheme.py` | `python assign_workflow_scheme.py --project PROJ --scheme-id 10101 --confirm` |
| List all statuses | `list_statuses.py` | `python list_statuses.py` |
| Filter statuses by category | `list_statuses.py` | `python list_statuses.py --category TODO` |
| Get issue's workflow | `get_workflow_for_issue.py` | `python get_workflow_for_issue.py PROJ-123 --show-transitions` |

**Note:** Workflow creation/editing requires JIRA UI (not available via REST API)

**Detailed Guide:** [subsystems/workflow-management-guide.md](subsystems/workflow-management-guide.md)

---

## Quick Tips

### Need to preview changes first?
Add `--dry-run` to any mutating command:
```bash
python delete_project.py PROJ --dry-run
python assign_permission_scheme.py --project PROJ --scheme 10050 --dry-run
```

### Need JSON output for scripting?
Add `--output json` to any command:
```bash
python list_projects.py --output json
python get_workflow.py --name "Workflow" --output json
```

### Working with multiple profiles?
Add `--profile PROFILE_NAME` to any command:
```bash
python list_projects.py --profile production
python get_project.py PROJ --profile development
```

---

## Still Can't Find It?

1. **Search this page** with Ctrl+F
2. **Check subsystem guides** in [docs/subsystems/](subsystems/)
3. **See command syntax** in [QUICK-REFERENCE.md](QUICK-REFERENCE.md)
4. **Read best practices** in [BEST_PRACTICES.md](BEST_PRACTICES.md)
5. **Run `script.py --help`** for full documentation
