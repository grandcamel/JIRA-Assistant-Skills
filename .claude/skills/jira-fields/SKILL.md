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
```

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
