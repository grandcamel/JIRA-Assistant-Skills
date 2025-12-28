# Automation Rules Guide

Deep-dive reference for JIRA automation rule management including discovery, state management, manual invocation, and template-based creation.

---

## When to Use Automation Scripts

Use these scripts when you need to:
- List all automation rules with filtering by project, state
- Get detailed rule configuration including triggers and actions
- Search rules by trigger type, enabled/disabled state, or project scope
- Enable or disable automation rules
- Toggle rule state (enabled <-> disabled)
- List manually-triggered automation rules
- Invoke manual rules on specific issues
- List available automation templates
- Create rules from templates with custom configuration
- Update existing rule name, description, and configuration

---

## Understanding Automation Rules

### Key Concepts

- **Trigger**: What starts the rule (issue created, status changed, scheduled, manual)
- **Condition**: Optional filters that must be true for the rule to execute
- **Action**: What the rule does (assign, transition, comment, send notification)
- **Rule State**: Enabled (active) or Disabled (inactive)
- **Rule Scope**: Global (all projects) or Project-specific

### Common Trigger Types

| Trigger | Use Case |
|---------|----------|
| `jira.issue.event.trigger:created` | Issue created |
| `jira.issue.event.trigger:updated` | Issue updated |
| `jira.issue.event.trigger:assigned` | Issue assigned |
| `jira.issue.event.trigger:transitioned` | Status changed |
| `jira.scheduled.trigger` | Scheduled/recurring |
| `jira.manual.trigger` | Manual invocation |

---

## Scripts Reference

### Rule Discovery

| Script | Description |
|--------|-------------|
| `list_automation_rules.py` | List all automation rules with filtering |
| `get_automation_rule.py` | Get detailed rule configuration |
| `search_automation_rules.py` | Search rules by trigger, state, scope |

### Rule State Management

| Script | Description |
|--------|-------------|
| `enable_automation_rule.py` | Enable a disabled rule |
| `disable_automation_rule.py` | Disable an active rule |
| `toggle_automation_rule.py` | Toggle rule state |

### Manual Rules

| Script | Description |
|--------|-------------|
| `list_manual_rules.py` | List manually-triggered rules |
| `invoke_manual_rule.py` | Trigger a manual rule on an issue |

### Templates & Creation

| Script | Description |
|--------|-------------|
| `list_automation_templates.py` | List available templates |
| `get_automation_template.py` | Get template details |
| `create_rule_from_template.py` | Create rule from template |
| `update_automation_rule.py` | Update rule configuration |

---

## Examples

### List and Inspect Rules

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
```

### Enable/Disable Rules

```bash
# Enable/Disable rules
python enable_automation_rule.py RULE_ID
python enable_automation_rule.py --name "Auto-assign to lead"
python disable_automation_rule.py RULE_ID --confirm
python toggle_automation_rule.py RULE_ID

# Dry run mode
python enable_automation_rule.py RULE_ID --dry-run
python disable_automation_rule.py RULE_ID --dry-run
```

### Manual Rules

```bash
# List manual rules
python list_manual_rules.py --context issue

# Invoke on specific issue
python invoke_manual_rule.py RULE_ID --issue PROJ-123
python invoke_manual_rule.py RULE_ID --issue PROJ-123 --property '{"priority": "High"}'
```

### Templates & Creation

```bash
# List templates
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

---

## API Requirements

### Authentication
- JIRA API token with appropriate scopes
- Jira Administrator permissions (for full rule management)
- Project Administrator permissions (for project-scoped rules only)

### Required API Token Scopes
- `manage:jira-automation` - For create/update/delete operations
- `read:jira-work` - For list/get operations

### Cloud ID Requirement
All Automation API calls require the Atlassian Cloud ID, which is automatically retrieved from the JIRA instance using the tenant info endpoint (`/_edge/tenant_info`).

---

## Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| List/view rules | Administer Jira (global) or Project Admin |
| Enable/disable rules | Administer Jira (global) or Project Admin |
| Create rules | Administer Jira (global) or Project Admin |
| Update rules | Administer Jira (global) or Project Admin |
| Invoke manual rules | Administer Jira (global) or Project Admin |
| List templates | Administer Jira (global) |

---

## Important Notes

1. **Complex Rule Creation**: Very complex rules with nested conditions may require the UI
2. **Execution History**: No API for viewing rule execution logs (UI only)
3. **Bulk Operations**: No dedicated bulk enable/disable endpoint (must process sequentially)
4. **Analytics**: No API for rule performance metrics
5. **Audit Trail**: Limited audit information in API responses

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| **403 Forbidden** | Insufficient permissions | Verify Administer Jira or Project Admin permission |
| **404 Not Found** | Rule doesn't exist | Check rule ID spelling |
| **400 Bad Request** | Invalid configuration | Validate rule config JSON format |
| **Cloud ID Error** | Cannot retrieve Cloud ID | Check API token scopes |

---

## Related Guides

- [BEST_PRACTICES.md](../BEST_PRACTICES.md#automation-rules) - Automation best practices
- [DECISION-TREE.md](../DECISION-TREE.md#i-want-to-configure-automation) - Quick script finder
- [QUICK-REFERENCE.md](../QUICK-REFERENCE.md#automation) - Command syntax reference
