---
name: "jira-custom-fields"
description: "Custom field management and configuration - list fields, check project fields, configure Agile fields. Use when discovering custom fields, checking Agile field availability, or configuring project fields."
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# jira-fields: JIRA Custom Field Management

Manage custom fields and screen configurations in JIRA for Agile and other workflows.

## Risk Levels

| Operation | Risk | Notes |
|-----------|------|-------|
| List fields | `-` | Read-only |
| Check project fields | `-` | Read-only |
| Configure agile (dry-run) | `-` | Preview only |
| Configure agile | `!` | Can be reconfigured |
| Create field | `!` | Requires admin; can be deleted |

**Risk Legend**: `-` Safe, read-only | `!` Caution, modifiable | `!!` Warning, destructive but recoverable | `!!!` Danger, irreversible

## When to use this skill

**Use when you need to:**
- List available custom fields in a JIRA instance
- Check Agile field availability for a specific project
- Create custom fields (requires admin permissions)
- Configure projects for Agile workflows (Story Points, Epic Link, Sprint)
- Diagnose field configuration issues when fields aren't visible

**Use when troubleshooting:**
- "Field not found" or "field not available" errors
- Agile board shows "Story Points field not configured"
- Missing fields on issue create screen
- Setting up Scrum in a company-managed project
- Understanding why team-managed projects behave differently

**Use when planning:**
- Migrating from team-managed to company-managed projects
- Setting up a new Scrum/Kanban board
- Discovering instance field configuration
- Auditing or cleaning up custom fields

## What this skill does

**IMPORTANT:** Always use the `jira-as` CLI. Never run Python scripts directly.

### Field Discovery
- List all custom fields in the JIRA instance
- Find Agile-specific fields (Story Points, Epic Link, Sprint, Rank)
- Check which fields are available for a specific project
- Identify field IDs for use in other scripts

### Field Management (Admin)
- Create new custom fields
- Configure field contexts for projects
- Note: Screen configuration requires JIRA admin UI

### Project Type Detection
- Detect if a project is team-managed (next-gen) or company-managed (classic)
- Provide guidance on field configuration approach based on project type

## Common Options

All scripts support these common options:

| Option | Description |
|--------|-------------|
| `--output FORMAT` | Output format: `text` (default) or `json` |
| `--help` | Show help message and exit |

## Available Commands

All commands support `--help` for full documentation.

| Command | Description |
|---------|-------------|
| `jira-as fields list` | List all custom fields in the JIRA instance |
| `jira-as fields check-project` | Check field availability for a specific project |
| `jira-as fields configure-agile` | Configure Agile fields for a company-managed project |
| `jira-as fields create` | Create a new custom field (requires admin) |

### List Fields
```bash
# List all custom fields
jira-as fields list

# Filter by name pattern
jira-as fields list --filter "story"

# Show only Agile-related fields
jira-as fields list --agile

# Show all fields (including system fields)
jira-as fields list --all
```

### Check Project Fields
```bash
# Check what fields are available for issue creation
jira-as fields check-project PROJ

# Check fields for a specific issue type
jira-as fields check-project PROJ --type Story

# Check Agile field availability
jira-as fields check-project PROJ --check-agile
```

### Configure Agile Fields
```bash
# Configure default Agile fields for a project
jira-as fields configure-agile PROJ

# Preview changes without applying (dry run)
jira-as fields configure-agile PROJ --dry-run

# Specify custom field IDs
jira-as fields configure-agile PROJ --story-points customfield_10016 --epic-link customfield_10014

# Configure all Agile field IDs
jira-as fields configure-agile PROJ --story-points customfield_10016 --epic-link customfield_10014 --sprint customfield_10020
```

### Create Field
```bash
# Create Story Points field
jira-as fields create --name "Story Points" --type number

# Create Epic Link field
jira-as fields create --name "Epic Link" --type select

# Create with description
jira-as fields create --name "Effort" --type number --description "Effort in hours"
```

## Searching for Agile Fields

To find Agile-specific fields in your instance:

```bash
# List all Agile-related fields
jira-as fields list --agile

# Filter for Story Points field
jira-as fields list --filter "story"

# Filter for Epic fields
jira-as fields list --filter "epic"

# Filter for Sprint field
jira-as fields list --filter "sprint"
```

JSON output includes:
- `jira-as fields list`: Array of field objects with `id`, `name`, `type`, `custom`, `searcherKey`
- `jira-as fields check-project`: Object with `project`, `projectType`, `issueType`, `fields`, `agileFields`
- `jira-as fields create`: Created field object with `id`, `name`, `type`
- `jira-as fields configure-agile`: Configuration result with `configured`, `skipped`, `errors`

## Exit Codes

All scripts use consistent exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (API failure, validation error, invalid input) |

## Important Notes

### Project Types

**Company-managed (classic) projects:**
- Full API support for field configuration
- Fields can be added to screens via API
- Custom fields need to be associated with project via field configuration

**Team-managed (next-gen) projects:**
- Limited API support for field configuration
- Fields are managed per-project in the UI
- Some operations require manual UI configuration
- Use `check_project_fields.py` to detect project type

### Required Permissions

- **List fields**: Browse Projects permission
- **Create fields**: JIRA Administrator permission
- **Modify screens**: JIRA Administrator permission

### Common Agile Field IDs

See [Agile Field IDs Reference](assets/agile-field-ids.md) for the complete list.

Always run `jira-as fields list --agile` to verify IDs for your instance.

## Examples

### Setting up Agile for a new project
```bash
# 1. Check what fields are available in the project
jira-as fields check-project NEWPROJ --check-agile

# 2. Find Agile field IDs in your instance
jira-as fields list --agile

# 3. Preview configuration changes (dry run)
jira-as fields configure-agile NEWPROJ --dry-run

# 4. Configure Agile fields with correct IDs
jira-as fields configure-agile NEWPROJ --story-points customfield_10016 --epic-link customfield_10014
```

### Creating a company-managed Scrum project
```bash
# Create project with Scrum template (includes Agile fields)
# Use the JIRA UI or:
# POST /rest/api/3/project with:
#   projectTemplateKey: com.pyxis.greenhopper.jira:gh-scrum-template
```

### Diagnosing missing fields
```bash
# Filter for fields by name
jira-as fields list --filter "story"

# Check what's available for the project
jira-as fields check-project PROJ

# Check Agile field availability
jira-as fields check-project PROJ --check-agile
```

## Troubleshooting

### "Field not found" errors

**Symptom**: Script reports field ID doesn't exist or field not available.

**Solutions**:
1. Run `jira-as fields list --filter "field name"` to find correct field IDs for your instance
2. Field IDs vary between JIRA instances - never assume default IDs
3. Check if the field exists: `jira-as fields list --filter "field name"`

### "Permission denied" when creating fields

**Symptom**: Exit code 1 when running `jira-as fields create` with permission error.

**Solutions**:
1. Field creation requires JIRA Administrator permission
2. Contact your JIRA admin to create the field or grant permissions
3. For team-managed projects, use the project settings UI instead

### Fields not appearing on issue create screen

**Symptom**: Field exists but not shown when creating issues.

**Solutions**:
1. Check project type: `jira-as fields check-project PROJ`
2. For company-managed projects, fields must be added to the appropriate screen
3. For team-managed projects, configure fields in Project Settings > Features
4. Run `jira-as fields configure-agile PROJ --story-points customfield_10016` for Agile fields (company-managed only)

### Team-managed project limitations

**Symptom**: API operations fail or fields behave differently.

**Solutions**:
1. Detect project type: `jira-as fields check-project PROJ`
2. Team-managed projects have limited API support for field configuration
3. Most field configuration must be done through the JIRA UI
4. Consider converting to company-managed if full API control is needed

### Agile fields have wrong values

**Symptom**: Story Points or Sprint fields show unexpected data.

**Solutions**:
1. Verify field IDs match your instance: `jira-as fields list --agile` or `jira-as fields list --filter "story"`
2. Check field is configured for the correct issue types
3. Ensure the board is configured to use the correct Story Points field
4. For Sprint issues, verify the board includes your project

### Authentication failures

**Symptom**: Exit code 1 with "401 Unauthorized" errors.

**Solutions**:
1. Verify JIRA_API_TOKEN is set correctly (not expired)
2. Check JIRA_EMAIL matches the account that created the token
3. Generate a new API token at https://id.atlassian.com/manage-profile/security/api-tokens

## Documentation

| Guide | Purpose |
|-------|---------|
| [Quick Start](docs/QUICK_START.md) | Get started in 5 minutes |
| [Field Types Reference](docs/FIELD_TYPES_REFERENCE.md) | Complete field type guide |
| [Agile Field Guide](docs/AGILE_FIELD_GUIDE.md) | Agile board configuration |
| [Governance Guide](docs/GOVERNANCE_GUIDE.md) | Field management at scale |
| [Best Practices](docs/BEST_PRACTICES.md) | Design principles and guidelines |
| [Agile Field IDs](assets/agile-field-ids.md) | Field ID lookup reference |
