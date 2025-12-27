---
name: "JIRA Custom Fields"
description: "Custom field management and configuration - list fields, check project fields, configure Agile fields. Use when discovering custom fields, checking Agile field availability, or configuring project fields."
---

# jira-fields: JIRA Custom Field Management

Manage custom fields and screen configurations in JIRA for Agile and other workflows.

## When to use this skill

Use this skill when you need to:
- **List available custom fields** in a JIRA instance
- **Check Agile field availability** for a specific project
- **Create custom fields** (requires admin permissions)
- **Configure projects for Agile** workflows (Story Points, Epic Link, Sprint)
- **Diagnose field configuration issues** when fields aren't visible

## What this skill does

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
| `--profile PROFILE` | Use a specific JIRA profile from settings.json |
| `--output FORMAT` | Output format: `table` (default), `json`, or `csv` |
| `--help` | Show help message and exit |

## Available scripts

### list_fields.py
List all custom fields in the JIRA instance.
```bash
# List all custom fields
python list_fields.py

# Filter by name pattern
python list_fields.py --filter "epic"

# Show Agile fields only
python list_fields.py --agile

# Output as JSON
python list_fields.py --output json

# Use specific profile
python list_fields.py --profile production
```

### check_project_fields.py
Check field availability for a specific project.
```bash
# Check what fields are available for issue creation
python check_project_fields.py PROJ

# Check specific issue type
python check_project_fields.py PROJ --type Story

# Check Agile field availability
python check_project_fields.py PROJ --check-agile

# Output as JSON for programmatic use
python check_project_fields.py PROJ --output json
```

### configure_agile_fields.py
Configure Agile fields for a company-managed project.
```bash
# Add Agile fields to a project's screens
python configure_agile_fields.py PROJ

# Check what would be done without making changes
python configure_agile_fields.py PROJ --dry-run

# Specify custom field IDs
python configure_agile_fields.py PROJ --story-points customfield_10016
```

### create_field.py
Create a new custom field (requires admin permissions).
```bash
# Create Story Points field
python create_field.py --name "Story Points" --type number

# Create Epic Link field
python create_field.py --name "Epic Link" --type select

# Create with description
python create_field.py --name "Effort" --type number --description "Effort in hours"

# Output created field as JSON
python create_field.py --name "Priority Score" --type number --output json
```

## JSON Output Support

All scripts support `--output json` for programmatic integration:

```bash
# Get field list as JSON
python list_fields.py --agile --output json

# Parse with jq
python list_fields.py --output json | jq '.[] | select(.name | contains("Story"))'

# Check project fields as JSON
python check_project_fields.py PROJ --check-agile --output json
```

JSON output includes:
- `list_fields.py`: Array of field objects with `id`, `name`, `type`, `custom`, `searcherKey`
- `check_project_fields.py`: Object with `project`, `projectType`, `issueType`, `fields`, `agileFields`
- `create_field.py`: Created field object with `id`, `name`, `type`
- `configure_agile_fields.py`: Configuration result with `configured`, `skipped`, `errors`

## Exit Codes

All scripts use consistent exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (API failure, invalid input) |
| 2 | Authentication error (invalid token or email) |
| 3 | Permission denied (insufficient JIRA permissions) |
| 4 | Resource not found (project, field, or issue type doesn't exist) |
| 5 | Validation error (invalid field name, type, or configuration) |

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

These are typical IDs but may vary by instance:
- **Sprint**: `customfield_10020`
- **Story Points**: `customfield_10016` or `customfield_10040`
- **Epic Link**: `customfield_10014`
- **Epic Name**: `customfield_10011`
- **Rank**: `customfield_10019`

Always use `list_fields.py --agile` to find the correct IDs for your instance.

## Examples

### Setting up Agile for a new project
```bash
# 1. Check project type
python check_project_fields.py NEWPROJ --check-agile

# 2. If company-managed, configure Agile fields
python configure_agile_fields.py NEWPROJ --dry-run
python configure_agile_fields.py NEWPROJ

# 3. Verify configuration
python check_project_fields.py NEWPROJ --type Story
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
# List all Agile fields in instance
python list_fields.py --agile

# Check what's available for the project
python check_project_fields.py PROJ --check-agile

# Compare to identify missing fields
```

## Troubleshooting

### "Field not found" errors

**Symptom**: Script reports field ID doesn't exist or field not available.

**Solutions**:
1. Run `python list_fields.py --agile` to find correct field IDs for your instance
2. Field IDs vary between JIRA instances - never assume default IDs
3. Check if the field exists: `python list_fields.py --filter "field name"`

### "Permission denied" when creating fields

**Symptom**: Exit code 3 when running `create_field.py`.

**Solutions**:
1. Field creation requires JIRA Administrator permission
2. Contact your JIRA admin to create the field or grant permissions
3. For team-managed projects, use the project settings UI instead

### Fields not appearing on issue create screen

**Symptom**: Field exists but not shown when creating issues.

**Solutions**:
1. Check project type: `python check_project_fields.py PROJ --check-agile`
2. For company-managed projects, fields must be added to the appropriate screen
3. For team-managed projects, configure fields in Project Settings > Features
4. Run `python configure_agile_fields.py PROJ` for Agile fields (company-managed only)

### Team-managed project limitations

**Symptom**: API operations fail or fields behave differently.

**Solutions**:
1. Detect project type: `python check_project_fields.py PROJ`
2. Team-managed projects have limited API support for field configuration
3. Most field configuration must be done through the JIRA UI
4. Consider converting to company-managed if full API control is needed

### Agile fields have wrong values

**Symptom**: Story Points or Sprint fields show unexpected data.

**Solutions**:
1. Verify field IDs match your instance: `python list_fields.py --agile`
2. Check field is configured for the correct issue types
3. Ensure the board is configured to use the correct Story Points field
4. For Sprint issues, verify the board includes your project

### Authentication failures

**Symptom**: Exit code 2, "401 Unauthorized" errors.

**Solutions**:
1. Verify JIRA_API_TOKEN is set correctly (not expired)
2. Check JIRA_EMAIL matches the account that created the token
3. Generate a new API token at https://id.atlassian.com/manage-profile/security/api-tokens
4. Try a different profile: `--profile development`

## Best Practices

For comprehensive guidance on custom field management, Agile field configuration, and project field strategies, see [Best Practices Guide](docs/BEST_PRACTICES.md).
