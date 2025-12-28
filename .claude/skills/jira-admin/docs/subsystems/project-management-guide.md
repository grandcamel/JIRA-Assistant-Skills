# Project Management Guide

Deep-dive reference for JIRA project administration including creation, configuration, archiving, and category management.

---

## When to Use Project Management Scripts

Use these scripts when you need to:
- Create, configure, or delete JIRA projects
- Manage project categories (group projects by department, type, etc.)
- Update project settings (lead, default assignee, avatar, URL)
- Archive or restore projects for compliance or cleanup
- List and search projects across your JIRA instance
- View detailed project configuration (schemes, issue types, etc.)

---

## Understanding JIRA Projects

### Project Types

| Type | License Required | Use Case |
|------|-----------------|----------|
| `software` | Jira Software | Development teams (Scrum/Kanban) |
| `business` | Jira Core/Work Management | Business teams (Marketing, HR) |
| `service_desk` | Jira Service Management | IT/Support teams |

### Project Templates

| Shortcut | Full Template Key | Description |
|----------|-------------------|-------------|
| `scrum` | `com.pyxis.greenhopper.jira:gh-scrum-template` | Scrum board with sprints |
| `kanban` | `com.pyxis.greenhopper.jira:gh-kanban-template` | Kanban continuous flow |
| `basic` | `com.pyxis.greenhopper.jira:gh-simplified-basic` | Basic software project |

---

## Scripts Reference

### Project CRUD Operations

| Script | Description |
|--------|-------------|
| `create_project.py` | Create a new JIRA project |
| `get_project.py` | Get detailed project information |
| `list_projects.py` | List and search projects |
| `update_project.py` | Update project properties |
| `delete_project.py` | Delete a project (moves to trash) |

### Project Categories

| Script | Description |
|--------|-------------|
| `create_category.py` | Create a project category |
| `list_categories.py` | List all project categories |
| `assign_category.py` | Assign a project to a category |

### Project Configuration

| Script | Description |
|--------|-------------|
| `set_avatar.py` | Set project avatar from file or system |
| `set_project_lead.py` | Change project lead |
| `set_default_assignee.py` | Configure default issue assignee |
| `get_config.py` | View full project configuration |

### Archive/Restore

| Script | Description |
|--------|-------------|
| `archive_project.py` | Archive a project (read-only) |
| `restore_project.py` | Restore archived/trashed project |
| `list_projects.py --trash` | List deleted projects in trash |

---

## Examples

### Create a New Scrum Project

```bash
# Create with Scrum template
python create_project.py --key MOBILE --name "Mobile App" --type software --template scrum

# Create with lead and description
python create_project.py --key WEBAPP --name "Web Application" \
  --type software --template kanban \
  --lead alice@example.com \
  --description "Customer-facing web application"

# Create business project
python create_project.py --key MKTG --name "Marketing" --type business
```

### Get Project Information

```bash
# Get basic info
python get_project.py PROJ

# Get with components and versions
python get_project.py PROJ --show-components --show-versions

# JSON output
python get_project.py PROJ --output json
```

### List Projects

```bash
# List all projects
python list_projects.py

# Filter by type
python list_projects.py --type software

# Search by name
python list_projects.py --search "mobile"

# Include archived projects
python list_projects.py --include-archived

# Export to CSV
python list_projects.py --output csv > projects.csv
```

### Update Project

```bash
# Update name
python update_project.py PROJ --name "New Project Name"

# Update lead
python update_project.py PROJ --lead bob@example.com

# Update multiple fields
python update_project.py PROJ --name "Updated" --description "New desc" --url https://example.com
```

### Delete Project

```bash
# Delete with confirmation prompt
python delete_project.py PROJ

# Skip confirmation
python delete_project.py PROJ --yes

# Dry run to preview
python delete_project.py PROJ --dry-run
```

### Manage Categories

```bash
# Create a category
python create_category.py --name "Development" --description "All dev projects"

# List categories
python list_categories.py

# Assign project to category
python assign_category.py PROJ --category "Development"

# Remove category from project
python assign_category.py PROJ --remove
```

### Project Configuration

```bash
# Set avatar from file
python set_avatar.py PROJ --file /path/to/logo.png

# List available system avatars
python set_avatar.py PROJ --list

# Change project lead
python set_project_lead.py PROJ --lead alice@example.com

# Set default assignee
python set_default_assignee.py PROJ --type PROJECT_LEAD

# View full configuration
python get_config.py PROJ --show-schemes
```

### Archive and Restore

```bash
# Archive inactive project
python archive_project.py OLDPROJ --yes

# List trashed projects
python list_projects.py --trash

# Restore from trash/archive
python restore_project.py OLDPROJ

# Dry-run archive to preview
python archive_project.py OLDPROJ --dry-run
```

---

## Permission Requirements

| Operation | Required Permission |
|-----------|---------------------|
| Create project | Administer Jira (global) |
| Update project (general) | Administer Projects |
| Update project key/schemes | Administer Jira (global) |
| Delete project | Administer Jira (global) |
| Archive/restore project | Administer Jira (global) |
| Create category | Administer Jira (global) |
| Browse projects | Browse Projects |

---

## Important Notes

1. **Deleted projects remain in trash for 60 days** before permanent deletion
2. **Project keys cannot be changed** after creation without Administer Jira permission
3. **Project type cannot be changed** after creation (API limitation)
4. **Templates are only used during creation** and don't persist
5. **Archived projects are read-only** but can be browsed and restored

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| **403 Permission Denied** | Insufficient permissions | Contact JIRA administrator for Administer Jira permission |
| **409 Conflict** | Project key already exists | Choose a different key |
| **400 Invalid Key** | Keys must be uppercase, 2-10 characters, start with a letter | Fix key format |
| **404 Not Found** | Project doesn't exist | Check the key spelling |

---

## Related Guides

- [BEST_PRACTICES.md](../BEST_PRACTICES.md#project-management) - Project management best practices
- [DECISION-TREE.md](../DECISION-TREE.md#i-want-to-manage-projects) - Quick script finder
- [QUICK-REFERENCE.md](../QUICK-REFERENCE.md#projects) - Command syntax reference
