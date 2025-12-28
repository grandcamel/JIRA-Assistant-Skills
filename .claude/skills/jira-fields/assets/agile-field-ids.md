# Agile Field IDs Reference

Single source of truth for Agile field identifiers.

---

## Important Note

Field IDs vary by JIRA instance. **Always verify with:**

```bash
python list_fields.py --agile
```

---

## Typical JIRA Cloud Field IDs

| Field | Typical ID | Alternative IDs |
|-------|------------|-----------------|
| **Sprint** | `customfield_10020` | varies |
| **Story Points** | `customfield_10016` | `customfield_10040` |
| **Epic Link** | `customfield_10014` | varies |
| **Epic Name** | `customfield_10011` | varies |
| **Epic Color** | `customfield_10012` | varies |
| **Rank** | `customfield_10019` | varies |

---

## Field Descriptions

### Sprint (`customfield_10020`)
- **Type:** Sprint
- **Purpose:** Assign issues to sprints
- **Managed by:** Scrum boards
- **Note:** Cannot be edited directly; use board operations

### Story Points (`customfield_10016`)
- **Type:** Number (float)
- **Purpose:** Effort estimation using Fibonacci scale
- **Values:** 1, 2, 3, 5, 8, 13, 21 (recommended)
- **Used by:** Velocity tracking, sprint planning

### Epic Link (`customfield_10014`)
- **Type:** Epic Link
- **Purpose:** Link Story/Task/Bug to parent Epic
- **Constraint:** Issue can only belong to one Epic
- **Note:** Team-managed projects use built-in parent link instead

### Epic Name (`customfield_10011`)
- **Type:** Text (255 chars)
- **Purpose:** Display name for Epic on boards and backlogs
- **Required:** Yes, when creating Epics

### Epic Color (`customfield_10012`)
- **Type:** Select
- **Purpose:** Visual identification on boards
- **Values:** color_1 through color_9

### Rank (`customfield_10019`)
- **Type:** Rank
- **Purpose:** Global backlog ordering
- **Managed by:** Drag-and-drop on backlogs
- **Note:** Read-only in most contexts

---

## JIRA Server/Data Center Notes

Field IDs on Server/Data Center installations may differ significantly:
- IDs are assigned sequentially during installation
- Plugin installations may shift IDs
- Always use `list_fields.py --agile` to discover IDs

---

## Finding Fields Programmatically

```bash
# List all Agile fields
python list_fields.py --agile

# Check specific project
python check_project_fields.py PROJ --check-agile

# Search by partial name
python list_fields.py --filter "sprint"
python list_fields.py --filter "story"
python list_fields.py --filter "epic"
```

---

## Cross-References

- [Agile Field Guide](../docs/AGILE_FIELD_GUIDE.md) - Configuration workflows
- [Field Types Reference](../docs/FIELD_TYPES_REFERENCE.md) - All field types
- [SKILL.md](../SKILL.md) - Script documentation
