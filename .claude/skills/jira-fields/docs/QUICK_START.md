# JIRA Fields Quick Start Guide

Get started with custom field management in 5 minutes.

---

## Common Scenarios

### 1. Add Story Points to Your Project

**Problem:** Your Scrum board shows "Story Points field not configured" or you cannot estimate issues.

**Solution:**

```bash
# Step 1: Find your instance's Story Points field ID
python list_fields.py --agile

# Step 2: Check if your project can access Agile fields
python check_project_fields.py PROJ --check-agile

# Step 3: Configure Agile fields (company-managed projects only)
python configure_agile_fields.py PROJ --dry-run
python configure_agile_fields.py PROJ
```

**What if it fails?**
- Team-managed projects: Configure fields in Project Settings > Features
- Company-managed projects: Contact your JIRA admin if permission denied

---

### 2. List All Custom Fields

**Problem:** You need to find the field ID for a custom field.

**Solution:**

```bash
# List all custom fields
python list_fields.py

# Filter by name
python list_fields.py --filter "story"

# Output as JSON for scripting
python list_fields.py --output json
```

**Output example:**
```
ID                  NAME            TYPE      SEARCHABLE
customfield_10016   Story Points    float     Yes
customfield_10014   Epic Link       any       Yes
customfield_10020   Sprint          sprint    Yes
```

---

### 3. Check What Fields a Project Has

**Problem:** You want to know which fields are available for creating issues in a project.

**Solution:**

```bash
# Check all available fields
python check_project_fields.py PROJ

# Check specific issue type
python check_project_fields.py PROJ --type Story

# Check Agile field availability
python check_project_fields.py PROJ --check-agile
```

**What you learn:**
- Project type (company-managed vs team-managed)
- Which fields are available for issue creation
- Which Agile fields are configured (Sprint, Story Points, Epic Link)

---

## Script Quick Reference

| Task | Command |
|------|---------|
| List all fields | `python list_fields.py` |
| List Agile fields | `python list_fields.py --agile` |
| Search by name | `python list_fields.py --filter "name"` |
| Check project fields | `python check_project_fields.py PROJ` |
| Check Agile setup | `python check_project_fields.py PROJ --check-agile` |
| Configure Agile (dry-run) | `python configure_agile_fields.py PROJ --dry-run` |
| Configure Agile | `python configure_agile_fields.py PROJ` |
| Create field (admin) | `python create_field.py --name "Name" --type number` |

---

## Common Options

All scripts support:
- `--profile PROFILE` - Use a specific JIRA profile
- `--output json` - Output as JSON
- `--help` - Show help message

---

## Next Steps

- **Setting up Agile boards?** See [Agile Field Guide](AGILE_FIELD_GUIDE.md)
- **Need field type details?** See [Field Types Reference](FIELD_TYPES_REFERENCE.md)
- **Managing many fields?** See [Governance Guide](GOVERNANCE_GUIDE.md)
- **Full documentation:** See [Best Practices](BEST_PRACTICES.md)

---

## Troubleshooting Quick Fixes

| Error | Quick Fix |
|-------|-----------|
| "Field not found" | Run `list_fields.py --agile` to find correct field ID |
| "Permission denied" | Field creation requires JIRA Administrator permission |
| Field not on create screen | For company-managed: run `configure_agile_fields.py PROJ` |
| Team-managed project | Configure fields in JIRA UI: Project Settings > Features |

For detailed troubleshooting, see [SKILL.md](../SKILL.md#troubleshooting).
