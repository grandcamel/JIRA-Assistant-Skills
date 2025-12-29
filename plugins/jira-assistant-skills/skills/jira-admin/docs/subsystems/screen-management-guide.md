# Screen Management Guide

Deep-dive reference for JIRA screen management including screens, tabs, fields, and the 3-tier screen hierarchy.

---

## When to Use Screen Management Scripts

Use these scripts when you need to:
- **View and manage screens** - List, inspect, and modify screens
- **Configure screen tabs and fields** - Add or remove fields from screen tabs
- **Manage screen schemes** - View screen schemes and their operation mappings
- **Manage issue type screen schemes** - View project-level screen configurations
- **Discover project screen configuration** - See which screens a project uses

---

## Understanding JIRA's 3-Tier Screen Hierarchy

JIRA uses a hierarchical system for screen configuration:

```
Project
    |
    +-- Issue Type Screen Scheme (project-level assignment)
            |
            +-- Screen Scheme (per issue type: Bug, Story, Task, etc.)
                    |
                    +-- Screens (per operation: create, edit, view)
                            |
                            +-- Tabs
                                    |
                                    +-- Fields
```

### Hierarchy Levels

| Level | Component | Description |
|-------|-----------|-------------|
| **Level 1** | Issue Type Screen Scheme | Assigned to a project, maps issue types to screen schemes |
| **Level 2** | Screen Scheme | Maps operations (create/edit/view) to screens |
| **Level 3** | Screen | Contains tabs and fields that users see when performing operations |

---

## Scripts Reference

### Screen Operations (Level 3)

| Script | Description |
|--------|-------------|
| `list_screens.py` | List all screens with filtering |
| `get_screen.py` | Get screen details with tabs and fields |
| `list_screen_tabs.py` | List tabs for a specific screen |
| `get_screen_fields.py` | Get all fields on a screen or specific tab |
| `add_field_to_screen.py` | Add a field to a screen tab |
| `remove_field_from_screen.py` | Remove a field from a screen tab |

### Screen Schemes (Level 2)

| Script | Description |
|--------|-------------|
| `list_screen_schemes.py` | List all screen schemes |
| `get_screen_scheme.py` | Get screen scheme details with operation mappings |

### Issue Type Screen Schemes (Level 1)

| Script | Description |
|--------|-------------|
| `list_issue_type_screen_schemes.py` | List all issue type screen schemes |
| `get_issue_type_screen_scheme.py` | Get scheme details with issue type mappings |

### Project Screen Discovery

| Script | Description |
|--------|-------------|
| `get_project_screens.py` | Discover complete screen configuration for a project |

---

## Examples

### Working with Screens

```bash
# List all screens
python list_screens.py
python list_screens.py --filter "Default"
python list_screens.py --scope PROJECT
python list_screens.py --all --output json

# Get screen details
python get_screen.py 1
python get_screen.py 1 --tabs
python get_screen.py 1 --tabs --fields
python get_screen.py 1 --output json

# List screen tabs
python list_screen_tabs.py 1
python list_screen_tabs.py 1 --field-count
python list_screen_tabs.py 1 --output json

# Get fields on a screen
python get_screen_fields.py 1
python get_screen_fields.py 1 --tab 10000
python get_screen_fields.py 1 --type custom
python get_screen_fields.py 1 --type system
```

### Modifying Screen Fields

```bash
# Add a field to a screen
python add_field_to_screen.py 1 customfield_10016
python add_field_to_screen.py 1 customfield_10016 --tab 10001
python add_field_to_screen.py 1 customfield_10016 --tab-name "Custom Fields"
python add_field_to_screen.py 1 customfield_10016 --dry-run

# Remove a field from a screen
python remove_field_from_screen.py 1 customfield_10016
python remove_field_from_screen.py 1 customfield_10016 --tab 10001
python remove_field_from_screen.py 1 summary --force
python remove_field_from_screen.py 1 customfield_10016 --dry-run
```

### Working with Screen Schemes

```bash
# List screen schemes
python list_screen_schemes.py
python list_screen_schemes.py --filter "Default"
python list_screen_schemes.py --show-screens
python list_screen_schemes.py --output json

# Get screen scheme details
python get_screen_scheme.py 1
python get_screen_scheme.py 1 --details
python get_screen_scheme.py 1 --output json
```

### Working with Issue Type Screen Schemes

```bash
# List issue type screen schemes
python list_issue_type_screen_schemes.py
python list_issue_type_screen_schemes.py --filter "Default"
python list_issue_type_screen_schemes.py --projects
python list_issue_type_screen_schemes.py --output json

# Get issue type screen scheme details
python get_issue_type_screen_scheme.py 10000
python get_issue_type_screen_scheme.py 10000 --mappings
python get_issue_type_screen_scheme.py 10000 --projects
python get_issue_type_screen_scheme.py 10000 --output json
```

### Project Screen Discovery

```bash
# Discover project screen configuration
python get_project_screens.py PROJ
python get_project_screens.py PROJ --issue-types
python get_project_screens.py PROJ --full
python get_project_screens.py PROJ --full --operation create
python get_project_screens.py PROJ --full --available-fields
python get_project_screens.py PROJ --output json
```

---

## Common Screen Field Operations

### Adding Custom Fields to Screens

```bash
# Add Story Points field to create screen
python add_field_to_screen.py 1 customfield_10016 --tab-name "Field Tab"

# Add Sprint field to edit screen
python add_field_to_screen.py 2 customfield_10020

# Dry run to validate
python add_field_to_screen.py 1 customfield_10016 --dry-run
```

### Removing Unused Fields

```bash
# Remove a custom field
python remove_field_from_screen.py 1 customfield_10025

# Force remove a required field (use caution)
python remove_field_from_screen.py 1 summary --force
```

---

## Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| List/view screens | Administer Jira (global) |
| List/view screen schemes | Administer Jira (global) |
| Add field to screen | Administer Jira (global) |
| Remove field from screen | Administer Jira (global) |
| View project screens | Browse Projects + Administer Jira |

---

## Important Notes

1. **Team-managed projects** use a different screen model - these scripts work with company-managed projects
2. **Removing required fields** (summary, issue type) can break issue creation - use --force with caution
3. **Screen changes affect all projects** using that screen scheme
4. **Custom field availability** - A field must be available in the screen context to be added
5. **Dry-run mode** available on add/remove operations to preview changes
6. **Field order** - New fields are added at the end of the tab; reordering requires the JIRA UI

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| **403 Forbidden** | Insufficient permissions | Verify Administer Jira permission |
| **404 Not Found** | Screen or field doesn't exist | Check screen ID and field ID |
| **400 Bad Request** | Field already on screen | Field may already exist on the screen |
| **Cannot Remove** | Required field | Use --force flag with caution |

---

## Related Guides

- [BEST_PRACTICES.md](../BEST_PRACTICES.md#screen-management) - Screen best practices
- [DECISION-TREE.md](../DECISION-TREE.md#i-want-to-manage-screens) - Quick script finder
- [QUICK-REFERENCE.md](../QUICK-REFERENCE.md#screens) - Command syntax reference
- [VOODOO_CONSTANTS.md](../VOODOO_CONSTANTS.md#common-custom-field-ids) - Field ID reference
