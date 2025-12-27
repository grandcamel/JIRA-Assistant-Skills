# JIRA Administration Best Practices

Comprehensive guide to JIRA project and system administration, covering project management, permission schemes, automation rules, notification schemes, screen management, issue types, workflows, and user/group management.

---

## Table of Contents

1. [Project Management](#project-management)
2. [Permission Schemes](#permission-schemes)
3. [Automation Rules](#automation-rules)
4. [Notification Schemes](#notification-schemes)
5. [Screen Management](#screen-management)
6. [Issue Types & Schemes](#issue-types--schemes)
7. [Workflow Management](#workflow-management)
8. [User & Group Management](#user--group-management)
9. [Security Considerations](#security-considerations)
10. [Performance Tips](#performance-tips)
11. [Common Pitfalls](#common-pitfalls)
12. [Quick Reference Card](#quick-reference-card)

---

## Project Management

### Project Naming Conventions

**Project Keys:**
- Use 2-10 uppercase letters
- Start with a letter, not a number
- Make it memorable and intuitive: `MOBILE`, `API`, `WEB`
- Avoid generic keys: `PROJ1`, `TEST`, `MISC`
- Consider department prefixes for large organizations: `ENG-MOBILE`, `HR-RECRUIT`

**Project Names:**
- Be descriptive but concise
- Include team or product context when helpful
- Use consistent naming patterns across the organization

| Bad Key | Good Key | Reason |
|---------|----------|--------|
| `PRJ1` | `MOBILE` | Descriptive and memorable |
| `TEST` | `QATEST` | Distinguishes from production |
| `ABC` | `BILLING` | Self-documenting |
| `12345` | `INFRA` | Cannot start with numbers anyway |

### Project Creation Best Practices

**Do:**
```bash
# Create with meaningful settings
python create_project.py --key MOBILE --name "Mobile Application" \
  --type software --template scrum \
  --lead mobile-lead@example.com \
  --description "iOS and Android mobile application development"
```

**Don't:**
- Create projects without a designated lead
- Use generic descriptions like "A project"
- Create duplicate projects for the same initiative
- Forget to assign the correct permission scheme

### Project Lifecycle Management

**Active Projects:**
- Assign a project lead who actively monitors the project
- Set up appropriate permission schemes before inviting users
- Configure notification schemes to avoid spam
- Define issue types relevant to the project's workflow

**Archiving Projects:**
```bash
# Preview before archiving
python archive_project.py OLDPROJ --dry-run

# Archive with confirmation
python archive_project.py OLDPROJ --yes
```

**When to Archive:**
- Project completed with no ongoing maintenance
- No activity for 6+ months
- Team disbanded or reorganized
- Replaced by a new project

**Don't Delete Prematurely:**
- Deleted projects go to trash for 60 days
- Use archiving for read-only access
- Archived projects preserve all history
- Deletion loses all issue links and references

### Project Category Organization

**Category Strategies:**

| Strategy | Example Categories | Best For |
|----------|-------------------|----------|
| **By Department** | Engineering, Marketing, Sales, HR | Enterprise organizations |
| **By Product** | Platform, Mobile, Web, API | Product companies |
| **By Team** | Team Alpha, Team Beta, Platform | Agile organizations |
| **By Status** | Active, Maintenance, Archive | Project portfolio management |

```bash
# Create meaningful categories
python create_category.py --name "Customer Products" \
  --description "All customer-facing product development"

# Assign projects to categories
python assign_category.py MOBILE --category "Customer Products"
```

### Configuration Management

**Document your configuration:**
- Export project configuration regularly
- Track changes to schemes in version control
- Maintain a runbook for common configuration tasks

```bash
# View complete project configuration
python get_config.py PROJ --show-schemes

# Export for documentation
python get_config.py PROJ --show-schemes --output json > proj-config.json
```

---

## Permission Schemes

### Principle of Least Privilege

**Core Principle:** Grant only the permissions necessary for users to perform their roles.

**Do:**
- Start with minimal permissions and add as needed
- Use project roles instead of individual users
- Review permissions quarterly
- Document permission decisions

**Don't:**
- Grant "Administer Projects" to all developers
- Use "Anyone" for sensitive permissions
- Copy production permissions to test projects without review
- Forget to remove permissions when roles change

### Permission Scheme Design

**Standard Permission Patterns:**

| Permission | Recommended Holders | Notes |
|------------|---------------------|-------|
| `BROWSE_PROJECTS` | `projectRole:Users` | All project members |
| `CREATE_ISSUES` | `projectRole:Users` | Regular team members |
| `EDIT_ISSUES` | `projectRole:Developers`, `currentAssignee` | Restrict to relevant users |
| `DELETE_ISSUES` | `projectRole:Administrators` | Highly restricted |
| `ADMINISTER_PROJECTS` | `projectRole:Administrators` | Project admins only |
| `MANAGE_SPRINTS` | `projectRole:Developers` | Scrum masters/team leads |
| `ASSIGN_ISSUES` | `projectRole:Developers` | Those who can delegate work |

### Creating Permission Schemes

**Start from Templates:**
```bash
# Clone an existing scheme
python create_permission_scheme.py --name "Mobile Team Permissions" \
  --clone 10000 \
  --description "Based on default scheme, customized for mobile team"

# Or use a grant template file
python create_permission_scheme.py --name "API Team Permissions" \
  --template api_permissions.json
```

**Build Incrementally:**
```bash
# Create minimal scheme
python create_permission_scheme.py --name "New Team Scheme" \
  --grant "BROWSE_PROJECTS:projectRole:Users" \
  --grant "CREATE_ISSUES:projectRole:Users"

# Add permissions as needed
python update_permission_scheme.py 10050 \
  --add-grant "EDIT_ISSUES:projectRole:Developers"
```

### Scheme Assignment Strategy

**Before Assigning:**
1. Review all grants in the scheme
2. Verify project roles are populated
3. Test with a pilot project
4. Document the change

```bash
# Preview current scheme
python assign_permission_scheme.py --project PROJ --show-current

# Dry run to see what will change
python assign_permission_scheme.py --project PROJ --scheme 10050 --dry-run

# Apply with confirmation
python assign_permission_scheme.py --project PROJ --scheme 10050
```

### Permission Holder Types Reference

| Holder Type | When to Use | Example |
|-------------|-------------|---------|
| `anyone` | Public projects only | Public documentation |
| `group:name` | Cross-project permissions | `group:jira-developers` |
| `projectRole:name` | Project-specific access | `projectRole:Developers` |
| `projectLead` | Lead-only actions | Approvals, releases |
| `currentAssignee` | Issue owner actions | Edit own assigned issues |
| `reporter` | Original creator | Edit own reported issues |
| `user:accountId` | Specific user (avoid) | Temporary access |

---

## Automation Rules

### Rule Design Principles

**Keep Rules Simple:**
- One trigger, one action is ideal
- Complex logic should be split into multiple rules
- Use descriptive rule names
- Document the purpose in rule description

**Naming Conventions:**
```
[Trigger] - [Action] - [Scope]

Examples:
- Issue Created - Auto Assign to Component Lead - All Projects
- Sprint Started - Send Slack Notification - Team Alpha
- Status Changed - Update Due Date - PROJ Only
```

### Common Automation Patterns

**Auto-Assignment:**
```
WHEN: Issue created
IF: Component = "Backend"
THEN: Assign to component lead
```

**Status-Based Actions:**
```
WHEN: Status changed TO "In Progress"
IF: Assignee IS EMPTY
THEN: Assign to current user
```

**Due Date Management:**
```
WHEN: Sprint started
THEN: Set due date to sprint end date
```

**Notification Patterns:**
```
WHEN: Issue priority changed TO Highest
THEN:
  - Add comment "Escalated to P0"
  - Send Slack notification to #critical-issues
```

### Template-Based Rule Creation

**Use templates for consistency:**
```bash
# List available templates
python list_automation_templates.py

# View template details
python get_automation_template.py TEMPLATE_ID

# Create from template
python create_rule_from_template.py TEMPLATE_ID --project PROJ \
  --name "My Custom Rule" --dry-run
```

### Rule State Management

**Enable/Disable Safely:**
```bash
# Always preview first
python disable_automation_rule.py RULE_ID --dry-run

# Disable with confirmation
python disable_automation_rule.py RULE_ID --confirm
```

**When to Disable Rules:**
- During bulk operations to prevent cascading actions
- When debugging unexpected behavior
- During migrations or major changes
- Temporarily for performance testing

### Manual Rule Invocation

**Use Cases:**
- One-time cleanup operations
- Ad-hoc bulk updates
- Testing rule logic
- Retroactive fixes

```bash
# List manual rules
python list_manual_rules.py --context issue

# Invoke on specific issue
python invoke_manual_rule.py RULE_ID --issue PROJ-123

# With custom properties
python invoke_manual_rule.py RULE_ID --issue PROJ-123 \
  --property '{"target_status": "Done"}'
```

---

## Notification Schemes

### Notification Design Principles

**Minimize Noise:**
- Don't notify everyone about everything
- Use role-based notifications
- Consider notification fatigue
- Test with a small group first

**Target the Right Recipients:**

| Event | Recommended Recipients | Avoid |
|-------|----------------------|-------|
| Issue Created | Reporter, Component Lead | All watchers |
| Issue Assigned | Assignee, Previous Assignee | Project Lead |
| Issue Resolved | Reporter, Watchers | Everyone |
| Comment Added | Assignee, Reporter, @mentioned | All watchers |
| Work Logged | Assignee only | Anyone else |

### Scheme Structure

**Minimal Scheme (Recommended Start):**
```bash
python create_notification_scheme.py --name "Minimal Notifications" \
  --event "Issue created" --notify Reporter \
  --event "Issue assigned" --notify CurrentAssignee
```

**Expanded Scheme:**
```bash
python create_notification_scheme.py --name "Team Notifications" \
  --event "Issue created" --notify Reporter --notify ComponentLead \
  --event "Issue assigned" --notify CurrentAssignee \
  --event "Issue resolved" --notify Reporter --notify AllWatchers \
  --event "Issue commented" --notify CurrentAssignee --notify Reporter
```

### Notification Scheme Assignment

**Before Assigning:**
1. Audit current notification patterns
2. Gather feedback on notification fatigue
3. Start with minimal notifications
4. Add more only when requested

```bash
# View scheme details
python get_notification_scheme.py 10000 --show-projects

# Test with one project first
python update_notification_scheme.py 10050 --name "Test - Team Notifications"
# Assign to test project, gather feedback, then expand
```

### Recipient Types Reference

| Recipient | Description | Use Case |
|-----------|-------------|----------|
| `CurrentAssignee` | Currently assigned user | Primary work owner |
| `Reporter` | Issue creator | Status updates, resolution |
| `ProjectLead` | Project lead | Escalations, critical issues |
| `ComponentLead` | Component lead | Area-specific issues |
| `AllWatchers` | All watchers | Issue subscribers |
| `Group:name` | Group members | Team-wide notifications |
| `ProjectRole:id` | Role members | Role-based routing |
| `CurrentUser` | Action performer | Confirmation of own actions |

---

## Screen Management

### Understanding the 3-Tier Hierarchy

```
Project
    |
    +-- Issue Type Screen Scheme (project-level)
            |
            +-- Screen Scheme (per issue type)
                    |
                    +-- Screen (per operation: create/edit/view)
                            |
                            +-- Tabs
                                    |
                                    +-- Fields
```

**Key Insight:** Changes to a screen affect ALL projects using that screen scheme.

### Screen Design Best Practices

**Create vs Edit vs View:**

| Screen Type | Should Include | Should Exclude |
|-------------|----------------|----------------|
| **Create** | Required fields, essential context | Rarely-used fields, workflow fields |
| **Edit** | All editable fields, workflow fields | System fields (created, updated) |
| **View** | All relevant fields | Nothing (show everything) |

**Field Organization:**
- Group related fields on the same tab
- Order fields by importance/frequency of use
- Put required fields at the top
- Create custom tabs for specialized fields

### Adding Fields to Screens

**Before Adding:**
1. Verify the field exists in your instance
2. Check if it's already on the screen
3. Consider which tab is most appropriate
4. Use dry-run to preview

```bash
# Preview the change
python add_field_to_screen.py 1 customfield_10016 --dry-run

# Add to specific tab
python add_field_to_screen.py 1 customfield_10016 --tab-name "Custom Fields"
```

### Removing Fields from Screens

**Caution:** Removing required system fields can break issue creation.

```bash
# Safe removal (custom field)
python remove_field_from_screen.py 1 customfield_10025

# Force removal (use caution with required fields)
python remove_field_from_screen.py 1 summary --force --dry-run
```

**Fields You Should NOT Remove:**
- `summary` (required for issue creation)
- `issuetype` (required for issue creation)
- `project` (set by context)

### Project Screen Discovery

**Before Making Changes:**
```bash
# Understand current configuration
python get_project_screens.py PROJ --full

# See all issue types and their screens
python get_project_screens.py PROJ --issue-types

# Check specific operation
python get_project_screens.py PROJ --full --operation create
```

---

## Issue Types & Schemes

### Issue Type Design

**Standard Issue Types:**

| Type | Hierarchy | Purpose | Example |
|------|-----------|---------|---------|
| Epic | 1 | Large features, initiatives | "User Authentication System" |
| Story | 0 | User-facing functionality | "User can reset password" |
| Task | 0 | Technical work items | "Set up CI pipeline" |
| Bug | 0 | Defects, issues | "Login fails on Safari" |
| Subtask | -1 | Breakdown of parent issues | "Write unit tests" |

**Custom Issue Types - When to Create:**
- Distinct workflow required
- Different fields needed
- Separate reporting requirements
- Compliance or process mandates

### Issue Type Naming

**Do:**
- Use nouns or noun phrases: "Bug", "Feature Request", "Support Ticket"
- Keep names under 60 characters
- Use clear, universally understood terms
- Maintain consistency across projects

**Don't:**
- Use verbs: "Fix Bug" (should be "Bug")
- Use abbreviations: "FR" (should be "Feature Request")
- Use project-specific jargon
- Create types that overlap in purpose

### Issue Type Scheme Design

**Scheme Strategies:**

| Strategy | Schemes | Best For |
|----------|---------|----------|
| **One-size-fits-all** | 1 default scheme | Small organizations |
| **By project type** | Software, Support, Business | Mixed project types |
| **By team** | Per team customization | Large organizations |
| **By workflow** | Agile, Kanban, Support | Process-driven |

```bash
# Create focused scheme
python create_issue_type_scheme.py \
  --name "Development Team Scheme" \
  --description "Standard development issue types" \
  --issue-type-ids 10001 10002 10003 10005 \
  --default-issue-type-id 10001
```

### Managing Issue Types in Schemes

**Adding Issue Types:**
```bash
# Add single type
python add_issue_types_to_scheme.py --scheme-id 10001 --issue-type-ids 10003

# Add multiple types
python add_issue_types_to_scheme.py --scheme-id 10001 --issue-type-ids 10003 10004 10005
```

**Removing Issue Types:**
```bash
# Cannot remove default type or last type
python remove_issue_type_from_scheme.py --scheme-id 10001 --issue-type-id 10003
```

**Reordering:**
```bash
# Move to first position
python reorder_issue_types_in_scheme.py --scheme-id 10001 --issue-type-id 10003

# Move after another type
python reorder_issue_types_in_scheme.py --scheme-id 10001 --issue-type-id 10003 --after 10001
```

---

## Workflow Management

### Workflow Discovery

**Understanding Your Workflows:**
```bash
# List all workflows
python list_workflows.py --show-usage

# Get workflow details
python get_workflow.py --name "Software Development Workflow" \
  --show-statuses --show-transitions --show-rules

# Find workflows for a project
python get_workflow_for_issue.py PROJ-123 --show-scheme
```

### Workflow Scheme Assignment

**Important:** Workflow creation/modification is NOT supported via REST API. Use JIRA admin UI for workflow design.

**Scheme Assignment is Asynchronous:**
```bash
# Always preview first
python assign_workflow_scheme.py --project PROJ --show-current

# Dry run to check for migration requirements
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 --dry-run

# Execute with confirmation
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 --confirm
```

### Status Migration

**When Changing Workflow Schemes:**
- Issues may have statuses not in the new workflow
- Migration mappings are required
- Plan migration before assignment

```json
// status_mappings.json
[
  {
    "issueTypeId": "10000",
    "statusMigrations": [
      {"oldStatusId": "1", "newStatusId": "10000"},
      {"oldStatusId": "2", "newStatusId": "10001"}
    ]
  }
]
```

```bash
python assign_workflow_scheme.py --project PROJ --scheme-id 10101 \
  --mappings status_mappings.json --confirm
```

### Status Categories

**All Statuses Map to Categories:**

| Category | Color | Purpose | Examples |
|----------|-------|---------|----------|
| TODO | Blue | Not started | To Do, Open, Backlog |
| IN_PROGRESS | Yellow | Active work | In Progress, In Review |
| DONE | Green | Completed | Done, Closed, Resolved |

```bash
# List statuses by category
python list_statuses.py --category TODO
python list_statuses.py --category IN_PROGRESS
python list_statuses.py --category DONE
```

---

## User & Group Management

### User Discovery

**Finding Users:**
```bash
# Search by name or email
python search_users.py "john"
python search_users.py "john.doe@example.com"

# Find assignable users for a project
python search_users.py "john" --project PROJ --assignable

# Get current user details
python get_user.py --me --include-groups
```

### Group Management Best Practices

**Group Naming Conventions:**
```
[prefix]-[scope]-[role]

Examples:
- jira-developers (system group)
- proj-mobile-team (project team)
- dept-engineering-leads (department role)
```

**Do:**
- Use consistent naming conventions
- Document group purposes
- Review membership regularly
- Use groups for permissions, not individual users

**Don't:**
- Create groups for single users
- Use vague names like "team1"
- Forget to remove departing members
- Grant admin access via groups without review

### Group Operations

```bash
# Create group
python create_group.py "mobile-developers"

# List groups
python list_groups.py --query "developers"

# View members
python get_group_members.py "jira-developers"

# Add user to group
python add_user_to_group.py john@example.com --group "mobile-developers"

# Remove user from group
python remove_user_from_group.py john@example.com --group "old-team" --confirm
```

### GDPR Considerations

**Privacy-First Approach:**
- Use `accountId` for all user references (not username/email)
- Handle privacy-restricted fields gracefully
- Respect user privacy settings
- Handle "unknown" accounts for deleted users

**System Limitations:**
- User creation/deactivation requires Cloud Admin API (not standard JIRA API)
- System groups cannot be deleted
- Email lookup may fail if user has privacy controls enabled

---

## Security Considerations

### API Token Security

**Do:**
- Use environment variables for tokens: `JIRA_API_TOKEN`
- Rotate tokens regularly (every 90 days)
- Use minimal required scopes
- Store tokens in secure credential managers

**Don't:**
- Commit tokens to version control
- Share tokens between environments
- Use personal tokens for automated systems
- Log tokens in application logs

### Permission Security

**Audit Regularly:**
```bash
# Review permission scheme grants
python get_permission_scheme.py 10000 --show-projects

# List all schemes and their usage
python list_permission_schemes.py --show-projects
```

**Security Review Checklist:**
- [ ] No "anyone" permissions on sensitive actions
- [ ] Delete permissions restricted to admins
- [ ] Admin permissions use named groups/roles
- [ ] Project permissions match project sensitivity
- [ ] Regular review of group membership

### Scheme Protection

**Before Deleting Schemes:**
```bash
# Check if scheme is in use
python get_permission_scheme.py 10050 --show-projects

# Check-only mode (safe)
python delete_permission_scheme.py 10050 --check-only
```

**Never Delete:**
- Default schemes (system fallbacks)
- Schemes assigned to active projects
- Schemes without understanding their purpose

---

## Performance Tips

### Efficient API Usage

**Batch Operations:**
```bash
# Use bulk operations for multiple changes
python list_projects.py --type software --output json > projects.json
# Process offline, then apply changes
```

**Pagination:**
```bash
# Use pagination for large result sets
python list_issue_type_schemes.py --start-at 0 --max-results 100
```

### Cache Considerations

**From jira-ops skill:**
```bash
# Warm cache before bulk operations
python warm_cache.py --type projects

# Clear cache after configuration changes
python manage_cache.py --clear --type all
```

### Large-Scale Operations

**For Bulk Changes:**
1. Always use `--dry-run` first
2. Process in batches (50-100 items)
3. Add delays between batches
4. Monitor API rate limits
5. Have rollback plan

```bash
# Example: Disable automation during bulk operations
python disable_automation_rule.py RULE_ID --confirm
# ... perform bulk operations ...
python enable_automation_rule.py RULE_ID
```

---

## Common Pitfalls

### Project Management Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **No project lead** | No ownership, issues pile up | Always assign a lead |
| **Duplicate projects** | Confusion, split data | Search before creating |
| **Generic keys** | Hard to remember | Use meaningful keys |
| **Never archiving** | 100+ active projects | Regular cleanup |
| **Deleting vs archiving** | Lost history | Archive first, delete later |

### Permission Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Too permissive** | Security risk | Start minimal, add as needed |
| **Individual users** | Maintenance nightmare | Use groups and roles |
| **Copying prod to dev** | Security mismatch | Review after copying |
| **No documentation** | Unclear decisions | Document permission rationale |
| **Forgotten access** | Ex-employees have access | Regular access reviews |

### Automation Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Complex rules** | Hard to debug | Split into simple rules |
| **No naming convention** | Can't find rules | Use consistent names |
| **No dry-run** | Unexpected changes | Always preview first |
| **Cascading rules** | Infinite loops | Design rule boundaries |
| **No disable plan** | Can't stop bad automation | Document how to disable |

### Notification Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Notify everyone** | Email fatigue | Target specific recipients |
| **All events** | Too much noise | Select key events only |
| **No testing** | Unexpected spam | Test with pilot group |
| **Duplicate schemes** | Inconsistency | Standardize and consolidate |
| **Never updating** | Stale configurations | Regular scheme reviews |

### Screen Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Too many fields** | User overwhelm | Minimal create screen |
| **Missing fields** | Data not captured | Review periodically |
| **Wrong tabs** | Hard to find fields | Logical grouping |
| **Removing required fields** | Breaks creation | Never remove summary/type |
| **No discovery** | Unknown configuration | Use get_project_screens.py |

### Issue Type Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Too many types** | Confusion | Consolidate similar types |
| **Overlapping types** | Inconsistent usage | Clear definitions |
| **No documentation** | Wrong type selection | Document when to use each |
| **Deleting without migration** | Orphaned issues | Always specify alternative |
| **Scheme sprawl** | Hard to manage | Standardize schemes |

### Workflow Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **API modification attempts** | Not supported | Use JIRA admin UI |
| **No status mapping** | Migration fails | Plan migrations |
| **Ignoring async** | Premature verification | Wait for completion |
| **Multiple scheme changes** | Confusion | One change at a time |
| **No preview** | Unexpected impact | Always dry-run |

### User/Group Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Using usernames** | GDPR non-compliant | Use accountId |
| **Individual permissions** | Hard to manage | Use groups |
| **System group deletion** | Not allowed | Skip system groups |
| **No cleanup** | Departed users remain | Regular audits |
| **Vague group names** | Unclear purpose | Naming conventions |

---

## Quick Reference Card

### Essential Commands by Area

**Project Management:**
```bash
# Create project
python create_project.py --key PROJ --name "Project Name" --type software

# View configuration
python get_config.py PROJ --show-schemes

# Archive project
python archive_project.py PROJ --yes
```

**Permission Schemes:**
```bash
# List schemes
python list_permission_schemes.py --show-grants

# Create scheme
python create_permission_scheme.py --name "New Scheme" --clone 10000

# Assign to project
python assign_permission_scheme.py --project PROJ --scheme 10050
```

**Automation Rules:**
```bash
# List rules
python list_automation_rules.py --state enabled

# Enable/disable rule
python enable_automation_rule.py RULE_ID
python disable_automation_rule.py RULE_ID --confirm
```

**Notification Schemes:**
```bash
# View scheme
python get_notification_scheme.py 10000

# Add notification
python add_notification.py 10000 --event "Issue created" --notify CurrentAssignee
```

**Screen Management:**
```bash
# Discover project screens
python get_project_screens.py PROJ --full

# Add field
python add_field_to_screen.py 1 customfield_10016 --dry-run
```

**Issue Types:**
```bash
# List types
python list_issue_types.py

# Create type
python create_issue_type.py --name "Feature Request" --type standard
```

**Workflows:**
```bash
# View workflow
python get_workflow.py --name "Workflow Name" --show-statuses --show-transitions

# List statuses
python list_statuses.py --category TODO
```

**User/Group Management:**
```bash
# Search users
python search_users.py "john" --assignable --project PROJ

# Manage groups
python list_groups.py
python add_user_to_group.py user@example.com --group "group-name"
```

### Required Permissions Reference

| Operation Area | Required Permission |
|----------------|---------------------|
| Project CRUD | Administer Jira (global) |
| Permission Schemes | Administer Jira (global) |
| Automation Rules | Administer Jira (global) or Project Admin |
| Notification Schemes | Administer Jira (global) |
| Screen Management | Administer Jira (global) |
| Issue Types | Administer Jira (global) |
| Workflows (view) | Administer Jira (global) |
| User/Group (write) | Site Administration |
| User/Group (read) | Browse Users and Groups |

### Dry-Run Pattern

Always preview changes before applying:
```bash
# Step 1: Dry run
python <script>.py <args> --dry-run

# Step 2: Review output

# Step 3: Execute (if safe)
python <script>.py <args> --confirm  # or --yes
```

### Safety Checklist

Before making administrative changes:
- [ ] Understand current state
- [ ] Use dry-run to preview
- [ ] Document the change
- [ ] Have rollback plan
- [ ] Test in non-production first
- [ ] Get approval if required
- [ ] Execute during low-activity period
- [ ] Verify after completion

---

*Last updated: December 2025*
