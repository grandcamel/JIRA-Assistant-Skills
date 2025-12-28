# Agile Custom Fields Reference

This skill uses JIRA's standard Agile custom fields. Field IDs may vary by instance.

## Default Custom Field IDs

| Field | Default ID | Purpose |
|-------|-----------|---------|
| Epic Name | `customfield_10011` | User-readable epic identifier |
| Epic Color | `customfield_10012` | Visual organization on boards |
| Epic Link | `customfield_10014` | Links issues to parent epics |
| Story Points | `customfield_10016` | Estimation metric for velocity |

## Discovering Your Field IDs

If your JIRA instance uses different field IDs:

### Option 1: Use jira-fields Skill

```bash
python get_agile_fields.py
```

This discovers all Agile-related fields for your instance.

### Option 2: Direct API Query

```bash
curl -u email:token "https://your-domain.atlassian.net/rest/api/3/field" | jq '.[] | select(.name | contains("Epic"))'
```

### Option 3: JIRA Admin UI

1. Go to Settings > Issues > Custom Fields
2. Find the field (Epic Link, Story Points, etc.)
3. Note the field ID from the URL or field details

## Configuring Custom Field IDs

If your instance uses different IDs, you can:

1. **Environment variables** (recommended):
   ```bash
   export JIRA_EPIC_LINK_FIELD=customfield_10100
   export JIRA_STORY_POINTS_FIELD=customfield_10200
   ```

2. **Script parameters**:
   ```bash
   python add_to_epic.py --epic PROJ-100 --issues PROJ-101 \
     --epic-link-field customfield_10100
   ```

3. **Configuration file** (settings.local.json):
   ```json
   {
     "agile_fields": {
       "epic_link": "customfield_10100",
       "story_points": "customfield_10200"
     }
   }
   ```

## Common Field Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Epic Link field not found" | Different field ID | Use jira-fields to discover |
| "Story points not showing" | Field not on screen | Check project screen configuration |
| "Cannot set Epic Name" | Field not editable | Check field configuration |

## See Also

- [jira-fields SKILL.md](../../jira-fields/SKILL.md) - Field discovery tools
- [Troubleshooting](TROUBLESHOOTING.md) - Field-related issues
