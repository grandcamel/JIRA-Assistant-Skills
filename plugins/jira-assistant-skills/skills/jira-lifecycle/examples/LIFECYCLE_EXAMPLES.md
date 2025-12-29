# JIRA Lifecycle Management Examples

**Use this guide when:** You need copy-paste examples for common lifecycle operations.

**Prerequisites:** JIRA credentials configured via environment variables or settings files.

---

## Workflow Transitions

```bash
# View available transitions for an issue
python get_transitions.py PROJ-123

# Transition by name (case-insensitive, partial match supported)
python transition_issue.py PROJ-123 --name "In Progress"

# Transition with sprint assignment
python transition_issue.py PROJ-123 --name "In Progress" --sprint 42

# Transition by ID (useful when names are ambiguous)
python transition_issue.py PROJ-123 --id 31

# Transition with custom fields
python transition_issue.py PROJ-123 --name "Done" --fields '{"customfield_10001": "value"}'
```

## Issue Assignment

```bash
# Assign to specific user by email
python assign_issue.py PROJ-123 --user user@example.com

# Assign to specific user by account ID
python assign_issue.py PROJ-123 --user 5b10ac8d82e05b22cc7d4ef5

# Assign to yourself
python assign_issue.py PROJ-123 --self

# Remove assignment
python assign_issue.py PROJ-123 --unassign
```

## Issue Resolution

```bash
# Resolve with standard resolution
python resolve_issue.py PROJ-123 --resolution Fixed

# Resolve with comment
python resolve_issue.py PROJ-123 --resolution "Won't Fix" --comment "Working as designed"

# Resolve as duplicate
python resolve_issue.py PROJ-123 --resolution Duplicate --comment "See PROJ-100"
```

## Reopening Issues

```bash
# Basic reopen
python reopen_issue.py PROJ-123

# Reopen with explanation
python reopen_issue.py PROJ-123 --comment "Regression found in v2.1"
```

## Version Management

### Creating Versions

```bash
# Create version with dates
python create_version.py PROJ --name "v1.0.0" --start-date 2025-01-01 --release-date 2025-03-01

# Create version with description
python create_version.py PROJ --name "v2.0.0" \
  --description "Major release with new dashboard" \
  --start-date 2025-04-01 --release-date 2025-06-30
```

### Viewing Versions

```bash
# List all versions (table format)
python get_versions.py PROJ --format table

# List released versions only
python get_versions.py PROJ --released --format json

# List unreleased versions
python get_versions.py PROJ --unreleased

# Export to CSV
python get_versions.py PROJ --format csv --output versions.csv
```

### Releasing and Archiving

```bash
# Release a version
python release_version.py PROJ --name "v1.0.0" --date 2025-03-15

# Release with description
python release_version.py PROJ --name "v1.0.0" --date 2025-03-15 \
  --description "Initial public release"

# Archive old version
python archive_version.py PROJ --name "v0.9.0"
```

### Moving Issues Between Versions

```bash
# Preview move (dry-run)
python move_issues_version.py --jql "fixVersion = v1.0.0 AND status != Done" \
  --target "v1.1.0" --dry-run

# Execute move after review
python move_issues_version.py --jql "fixVersion = v1.0.0 AND status != Done" \
  --target "v1.1.0"

# Move all completed issues to a version
python move_issues_version.py --jql "project = PROJ AND status = Done AND fixVersion IS EMPTY" \
  --target "v1.0.0" --dry-run
```

## Component Management

### Creating Components

```bash
# Create basic component
python create_component.py PROJ --name "Backend API" \
  --description "Server-side components"

# Create with lead and auto-assignment
python create_component.py PROJ --name "Mobile App" \
  --lead mobile-lead@example.com --assignee-type COMPONENT_LEAD

# Create with project lead assignment
python create_component.py PROJ --name "Documentation" \
  --assignee-type PROJECT_LEAD
```

### Viewing Components

```bash
# List all components
python get_components.py PROJ --format table

# Get specific component by ID
python get_components.py PROJ --id 10000

# Export components
python get_components.py PROJ --format json --output components.json
```

### Updating and Deleting

```bash
# Update component details
python update_component.py --id 10000 --name "New Name" --description "Updated description"

# Change component lead
python update_component.py --id 10000 --lead new-lead@example.com

# Preview deletion
python delete_component.py --id 10000 --dry-run

# Delete and migrate issues to another component
python delete_component.py --id 10000 --move-to 10001
```

## Using Profiles

```bash
# Use production profile
python transition_issue.py PROJ-123 --name "Done" --profile production

# Use development profile
python get_versions.py PROJ --profile development --format json

# Use staging profile
python create_component.py PROJ --name "Test Component" --profile staging
```

## Output Formats

```bash
# Table format (default, human-readable)
python get_versions.py PROJ --format table

# JSON format (for scripting)
python get_components.py PROJ --format json

# CSV format (for spreadsheets)
python get_versions.py PROJ --format csv --output versions.csv
```

## Workflow Patterns

### Start Work on Issue

```bash
# Claim and start work
python assign_issue.py PROJ-123 --self
python transition_issue.py PROJ-123 --name "In Progress"
```

### Complete Work on Issue

```bash
# Transition through review
python transition_issue.py PROJ-123 --name "In Review" \
  --comment "Ready for code review"

# Mark as done
python resolve_issue.py PROJ-123 --resolution Fixed \
  --comment "Implemented and tested"
```

### Handle Bug Report

```bash
# Investigate
python transition_issue.py BUG-456 --name "Investigating"
python assign_issue.py BUG-456 --self

# Cannot reproduce
python resolve_issue.py BUG-456 --resolution "Cannot Reproduce" \
  --comment "Unable to reproduce with provided steps"

# Or fix
python resolve_issue.py BUG-456 --resolution Fixed \
  --comment "Fixed null pointer exception in user service"
```

### Release Management

```bash
# 1. Create version for upcoming release
python create_version.py PROJ --name "v2.0.0" \
  --start-date 2025-01-01 --release-date 2025-03-31

# 2. Move incomplete items to next version
python move_issues_version.py \
  --jql "fixVersion = v2.0.0 AND status != Done" \
  --target "v2.1.0" --dry-run

# 3. Release the version
python release_version.py PROJ --name "v2.0.0" --date 2025-03-31

# 4. Archive old versions
python archive_version.py PROJ --name "v1.0.0"
```

---

*For more detailed guidance, see the [Best Practices Guide](../docs/BEST_PRACTICES.md).*
