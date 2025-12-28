# Common JIRA Administration Workflows

Step-by-step guides for common administration tasks. Each workflow lists the exact commands in order.

---

## Setting Up a New Project (7 Steps)

Complete workflow for creating and configuring a new JIRA project.

### Steps

```bash
# 1. Create the project
python create_project.py --key MOBILE --name "Mobile Application" \
  --type software --template scrum \
  --description "iOS and Android mobile development"

# 2. Assign project lead
python set_project_lead.py MOBILE --lead mobile-lead@example.com

# 3. Configure default assignee
python set_default_assignee.py MOBILE --type PROJECT_LEAD

# 4. Assign to category (if using categories)
python assign_category.py MOBILE --category "Customer Products"

# 5. Assign permission scheme
python assign_permission_scheme.py --project MOBILE --scheme 10050

# 6. View and verify configuration
python get_config.py MOBILE --show-schemes

# 7. (Optional) Set project avatar
python set_avatar.py MOBILE --file /path/to/logo.png
```

### Checklist
- [ ] Project created with appropriate template
- [ ] Lead assigned and notified
- [ ] Permission scheme appropriate for team
- [ ] Category assigned for organization
- [ ] Configuration verified

---

## Configuring Team Access (4 Steps)

Set up access for a new team to a project.

### Steps

```bash
# 1. Create a group for the team (if needed)
python create_group.py "mobile-developers"

# 2. Add team members to the group
python add_user_to_group.py alice@example.com --group "mobile-developers"
python add_user_to_group.py bob@example.com --group "mobile-developers"
python add_user_to_group.py charlie@example.com --group "mobile-developers"

# 3. Create or update permission scheme with group access
python update_permission_scheme.py 10050 \
  --add-grant "BROWSE_PROJECTS:group:mobile-developers" \
  --add-grant "CREATE_ISSUES:group:mobile-developers" \
  --add-grant "EDIT_ISSUES:group:mobile-developers"

# 4. Verify the configuration
python get_permission_scheme.py 10050 --show-projects
```

### Checklist
- [ ] Group created with meaningful name
- [ ] All team members added to group
- [ ] Permission scheme updated with appropriate grants
- [ ] Configuration verified

---

## Configuring Notification Rules for Team (5 Steps)

Set up targeted notifications to avoid email fatigue.

### Steps

```bash
# 1. List existing schemes to find a starting point
python list_notification_schemes.py

# 2. Create new scheme (or clone existing)
python create_notification_scheme.py \
  --name "Mobile Team Notifications" \
  --description "Targeted notifications for mobile development team"

# 3. Add key event notifications
python add_notification.py 10050 \
  --event "Issue created" --notify CurrentAssignee --notify Reporter

python add_notification.py 10050 \
  --event "Issue assigned" --notify CurrentAssignee

python add_notification.py 10050 \
  --event "Issue resolved" --notify Reporter --notify AllWatchers

python add_notification.py 10050 \
  --event "Issue commented" --notify CurrentAssignee --notify Reporter

# 4. Assign scheme to project(s)
# Note: Update project to use new notification scheme via JIRA UI
# (API for notification scheme assignment is limited)

# 5. Verify configuration
python get_notification_scheme.py 10050 --show-projects
```

### Checklist
- [ ] Scheme created with meaningful name
- [ ] Key events configured (created, assigned, resolved, commented)
- [ ] Recipients targeted appropriately (not "everyone")
- [ ] Assigned to relevant projects

---

## Setting Up Permission Tiers (5 Steps)

Create permission schemes for different access levels.

### Steps

```bash
# 1. List current schemes to understand existing patterns
python list_permission_schemes.py --show-grants

# 2. Create restrictive scheme for sensitive projects
python create_permission_scheme.py \
  --name "Confidential Projects" \
  --grant "BROWSE_PROJECTS:projectRole:Administrators" \
  --grant "BROWSE_PROJECTS:projectRole:Developers" \
  --grant "CREATE_ISSUES:projectRole:Developers" \
  --grant "EDIT_ISSUES:currentAssignee" \
  --grant "ADMINISTER_PROJECTS:projectRole:Administrators"

# 3. Create standard scheme for regular projects
python create_permission_scheme.py \
  --name "Standard Development" \
  --clone 10000 \
  --description "Standard permissions for development projects"

# 4. Assign schemes to projects
python assign_permission_scheme.py --project SECRET --scheme "Confidential Projects"
python assign_permission_scheme.py --project NORMAL --scheme "Standard Development"

# 5. Verify assignments
python get_permission_scheme.py "Confidential Projects" --show-projects
python get_permission_scheme.py "Standard Development" --show-projects
```

### Checklist
- [ ] Restrictive scheme for sensitive projects
- [ ] Standard scheme for regular projects
- [ ] Each scheme documented with description
- [ ] Appropriate projects assigned to each scheme

---

## Migrating Project to New Workflow Scheme (6 Steps)

Safely migrate a project to a new workflow scheme.

### Steps

```bash
# 1. View current workflow scheme for project
python assign_workflow_scheme.py --project PROJ --show-current

# 2. Get details on the new workflow scheme
python get_workflow_scheme.py --id 10101 --show-mappings

# 3. List current statuses in project issues
python list_statuses.py --workflow "Current Workflow"

# 4. Dry run to check for migration requirements
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 --dry-run

# 5. Create status mappings file if needed (status_mappings.json)
# See workflow-management-guide.md for mapping format

# 6. Assign new scheme with confirmation
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 \
  --mappings status_mappings.json --confirm
```

### Checklist
- [ ] Current scheme documented
- [ ] New scheme reviewed for compatibility
- [ ] Status mappings created (if needed)
- [ ] Dry run completed without errors
- [ ] Migration executed during low-activity period

---

## Configuring Issue Types for Project (5 Steps)

Set up appropriate issue types for a project.

### Steps

```bash
# 1. List available issue types
python list_issue_types.py

# 2. Create new scheme with desired types
python create_issue_type_scheme.py \
  --name "Mobile Development" \
  --description "Issue types for mobile projects" \
  --issue-type-ids 10001 10002 10003 10005 \
  --default-issue-type-id 10001

# 3. Add additional types if needed
python add_issue_types_to_scheme.py --scheme-id 10050 --issue-type-ids 10004

# 4. Reorder types for better UX
python reorder_issue_types_in_scheme.py --scheme-id 10050 --issue-type-id 10002

# 5. Assign scheme to project
python assign_issue_type_scheme.py --scheme-id 10050 --project-id 10000
```

### Checklist
- [ ] Relevant issue types identified
- [ ] Scheme created with appropriate types
- [ ] Default issue type set correctly
- [ ] Types ordered logically
- [ ] Scheme assigned to project

---

## Adding Custom Field to Screens (4 Steps)

Add a custom field to relevant screens across projects.

### Steps

```bash
# 1. Discover project screen configuration
python get_project_screens.py PROJ --full

# 2. Identify the screens to modify (create, edit, view)
# Note the screen IDs from the output

# 3. Add field to create screen
python add_field_to_screen.py 1 customfield_10016 --tab-name "Custom Fields" --dry-run
python add_field_to_screen.py 1 customfield_10016 --tab-name "Custom Fields"

# 4. Add field to edit screen (if different)
python add_field_to_screen.py 2 customfield_10016 --tab-name "Custom Fields"
```

### Checklist
- [ ] Screen configuration discovered
- [ ] Dry run completed successfully
- [ ] Field added to create screen
- [ ] Field added to edit screen (if needed)
- [ ] Verified field appears in project

---

## Archiving Inactive Project (4 Steps)

Safely archive a project that's no longer active.

### Steps

```bash
# 1. Verify project status and last activity
python get_project.py OLDPROJ

# 2. Preview archive operation
python archive_project.py OLDPROJ --dry-run

# 3. Archive the project
python archive_project.py OLDPROJ --yes

# 4. Verify archive status
python list_projects.py --include-archived --search "OLDPROJ"
```

### Checklist
- [ ] Confirmed no active work in project
- [ ] Stakeholders notified
- [ ] Dry run reviewed
- [ ] Project archived
- [ ] Archive verified

---

## Auditing Group Membership (3 Steps)

Review and clean up group membership.

### Steps

```bash
# 1. List all groups
python list_groups.py --include-members

# 2. Review specific group membership
python get_group_members.py "jira-developers" --include-inactive

# 3. Remove inactive/departed users
python remove_user_from_group.py departed@example.com --group "jira-developers" --confirm
```

### Checklist
- [ ] All groups reviewed
- [ ] Inactive users identified
- [ ] Removed users documented
- [ ] Remaining membership verified

---

## Managing Automation Rules During Bulk Operations (5 Steps)

Safely disable automation during bulk changes.

### Steps

```bash
# 1. List rules that might interfere
python list_automation_rules.py --project PROJ --state enabled

# 2. Document rules to disable
# Note the rule IDs that trigger on issue changes

# 3. Disable relevant rules
python disable_automation_rule.py RULE_ID1 --confirm
python disable_automation_rule.py RULE_ID2 --confirm

# 4. Perform bulk operations
# (Your bulk operations here)

# 5. Re-enable rules
python enable_automation_rule.py RULE_ID1
python enable_automation_rule.py RULE_ID2
```

### Checklist
- [ ] Relevant rules identified
- [ ] Rules disabled before bulk operations
- [ ] Bulk operations completed
- [ ] All rules re-enabled
- [ ] Rule states verified

---

## Quick Reference

| Workflow | Steps | Key Scripts |
|----------|-------|-------------|
| New project setup | 7 | `create_project.py`, `set_project_lead.py`, `get_config.py` |
| Team access | 4 | `create_group.py`, `add_user_to_group.py`, `update_permission_scheme.py` |
| Notifications | 5 | `create_notification_scheme.py`, `add_notification.py` |
| Permission tiers | 5 | `create_permission_scheme.py`, `assign_permission_scheme.py` |
| Workflow migration | 6 | `assign_workflow_scheme.py`, `list_statuses.py` |
| Issue types | 5 | `create_issue_type_scheme.py`, `assign_issue_type_scheme.py` |
| Add screen field | 4 | `get_project_screens.py`, `add_field_to_screen.py` |
| Archive project | 4 | `archive_project.py`, `list_projects.py` |
| Group audit | 3 | `list_groups.py`, `get_group_members.py` |
| Bulk ops safety | 5 | `list_automation_rules.py`, `disable_automation_rule.py` |

---

## Related Documentation

- [DECISION-TREE.md](DECISION-TREE.md) - Find the right script
- [QUICK-REFERENCE.md](QUICK-REFERENCE.md) - Command syntax
- [BEST_PRACTICES.md](BEST_PRACTICES.md) - Detailed best practices
- [Subsystem guides](subsystems/) - Deep-dive documentation
