---
name: "jira-custom-fields"
description: "Custom field discovery and configuration. TRIGGERS: 'field ID for', 'what's the field ID', 'what is the field ID', 'list custom fields', 'what fields are available', 'what custom fields', 'show custom fields', 'customfield_', 'find field', 'agile fields', 'configure agile fields', 'story points field'. Use for JIRA field metadata and discovery. NOT FOR: setting field values on issues (use jira-issue), setting story points (use jira-agile), searching by field values (use jira-search)."
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
| `-o, --output [text\|json]` | Output format: `text` (default) or `json` |
| `--help` | Show help message and exit |

## Available Commands

All commands support `--help` for full documentation.

| Command | Description |
|---------|-------------|
| `jira-as fields list` | List available fields (instance-wide, or scoped to a project's create screen) |
| `jira-as fields check-project` | Check field availability for a specific project |
| `jira-as fields configure-agile` | Configure Agile fields for a company-managed project |
| `jira-as fields create` | Create a new custom field (requires admin) |

### List Fields
```bash
# List all custom fields
jira-as fields list

# Filter by name pattern
jira-as fields list -f "story"
jira-as fields list --filter "story"

# Show only Agile-related fields
jira-as fields list --agile

# Show all fields (including system fields)
jira-as fields list --all

# Scope to the fields on a project's create screen (-p is short for --project)
jira-as fields list --project PROJ
jira-as fields list -p PROJ

# Scope further to one issue type (-t is short for --issue-type; requires --project)
jira-as fields list --project PROJ --issue-type Bug
jira-as fields list -p PROJ -t Bug
```

Without `--project`, `fields list` shows the whole instance field catalogue.
With `--project` (and optionally `--issue-type`), it lists only the fields you
can actually set when creating an issue there.

### Check Project Fields
```bash
# Check what fields are available for issue creation
jira-as fields check-project PROJ

# Check fields for a specific issue type
jira-as fields check-project PROJ --type Story

# Check Agile field availability (-a is short for --check-agile)
jira-as fields check-project PROJ -a
jira-as fields check-project PROJ --check-agile

# Output as JSON (-o is short for --output)
jira-as fields check-project PROJ -o json
jira-as fields check-project PROJ --output json
```

### Configure Agile Fields
```bash
# Configure default Agile fields for a project
jira-as fields configure-agile PROJ

# Preview changes without applying (dry run)
jira-as fields configure-agile PROJ -n
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

### Supported Field Types

The `fields create` command supports the following 12 field types:

| Type | Description | Example Use Case |
|------|-------------|------------------|
| `text` | Single-line text input | Short identifiers, codes |
| `textarea` | Multi-line text input | Detailed descriptions, notes |
| `number` | Numeric value | Story Points, Effort hours |
| `date` | Date picker (no time) | Due dates, target dates |
| `datetime` | Date and time picker | Scheduled start/end times |
| `select` | Single-choice dropdown | Priority, Category |
| `multiselect` | Multiple-choice dropdown | Labels, Components |
| `checkbox` | Boolean true/false | Flags, toggles |
| `radio` | Radio button group | Exclusive options |
| `url` | URL/hyperlink field | Documentation links |
| `user` | User picker | Reviewers, Approvers |
| `labels` | Tag/label field | Classification tags |

```bash
# Examples for each field type
jira-as fields create --name "External ID" --type text
jira-as fields create --name "Notes" --type textarea
jira-as fields create --name "Complexity" --type number
jira-as fields create --name "Target Date" --type date
jira-as fields create --name "Meeting Time" --type datetime
jira-as fields create --name "Category" --type select
jira-as fields create --name "Affected Teams" --type multiselect
jira-as fields create --name "Approved" --type checkbox
jira-as fields create --name "Environment" --type radio
jira-as fields create --name "Documentation" --type url
jira-as fields create --name "Reviewer" --type user
jira-as fields create --name "Tags" --type labels
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
- Use `jira-as fields check-project PROJ` to detect project type

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

# List only the fields settable on the project's create screen
jira-as fields list --project PROJ --issue-type Story

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
