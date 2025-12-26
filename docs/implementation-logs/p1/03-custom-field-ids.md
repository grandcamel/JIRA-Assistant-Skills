# P1-03: Fix Hardcoded Custom Field IDs

## Problem Statement

Multiple scripts in `jira-agile` and `jira-issue` had hardcoded custom field IDs that vary by JIRA instance:

```python
EPIC_LINK_FIELD = 'customfield_10014'
STORY_POINTS_FIELD = 'customfield_10016'
EPIC_NAME_FIELD = 'customfield_10011'
EPIC_COLOR_FIELD = 'customfield_10012'
```

These field IDs are instance-specific and can differ between JIRA installations, causing scripts to fail or silently use wrong fields.

## Solution Overview

1. Added `agile_fields` configuration to the profile schema
2. Extended `config_manager.py` with field ID retrieval methods
3. Updated all affected scripts to use configurable field IDs
4. Added environment variable overrides for field IDs

## Files Modified

### Configuration Schema

**`.claude/skills/shared/config/config.schema.json`**

Added `agile_fields` object to profile configuration:

```json
"agile_fields": {
  "type": "object",
  "description": "Custom field IDs for Agile fields (varies by JIRA instance)",
  "properties": {
    "epic_link": {
      "type": "string",
      "pattern": "^customfield_[0-9]+$",
      "description": "Epic Link field ID (e.g., customfield_10014)"
    },
    "story_points": {
      "type": "string",
      "pattern": "^customfield_[0-9]+$",
      "description": "Story Points field ID (e.g., customfield_10016)"
    },
    "epic_name": {
      "type": "string",
      "pattern": "^customfield_[0-9]+$",
      "description": "Epic Name field ID (e.g., customfield_10011)"
    },
    "epic_color": {
      "type": "string",
      "pattern": "^customfield_[0-9]+$",
      "description": "Epic Color field ID (e.g., customfield_10012)"
    },
    "sprint": {
      "type": "string",
      "pattern": "^customfield_[0-9]+$",
      "description": "Sprint field ID (e.g., customfield_10020)"
    }
  }
}
```

### Settings File

**`.claude/settings.json`**

Added `agile_fields` configuration to each profile:

```json
"production": {
  "url": "https://your-company.atlassian.net",
  "project_keys": ["PROD", "OPS"],
  "default_project": "PROD",
  "use_service_management": false,
  "agile_fields": {
    "epic_link": "customfield_10014",
    "story_points": "customfield_10016",
    "epic_name": "customfield_10011",
    "epic_color": "customfield_10012",
    "sprint": "customfield_10020"
  }
}
```

### Config Manager

**`.claude/skills/shared/scripts/lib/config_manager.py`**

Added:

1. `DEFAULT_AGILE_FIELDS` constant with common defaults
2. `ConfigManager.get_agile_fields(profile)` - returns all field IDs
3. `ConfigManager.get_agile_field(field_name, profile)` - returns specific field ID
4. `get_agile_fields()` - convenience function
5. `get_agile_field()` - convenience function

Configuration priority:
1. Environment variables (highest): `JIRA_EPIC_LINK_FIELD`, `JIRA_STORY_POINTS_FIELD`, etc.
2. Profile configuration in `settings.local.json` or `settings.json`
3. Default values in `DEFAULT_AGILE_FIELDS`

### jira-agile Scripts Updated

| Script | Fields Updated |
|--------|----------------|
| `add_to_epic.py` | `epic_link` |
| `create_epic.py` | `epic_name`, `epic_color` |
| `estimate_issue.py` | `story_points` |
| `get_backlog.py` | `epic_link`, `story_points` |
| `get_epic.py` | `story_points`, `epic_name` |
| `get_estimates.py` | `story_points` |
| `get_sprint.py` | `story_points` |

### jira-issue Scripts Updated

| Script | Fields Updated |
|--------|----------------|
| `create_issue.py` | `epic_link`, `story_points` |

## Configuration Examples

### Per-Profile Configuration

```json
{
  "jira": {
    "profiles": {
      "production": {
        "url": "https://company.atlassian.net",
        "agile_fields": {
          "epic_link": "customfield_10014",
          "story_points": "customfield_10016"
        }
      },
      "development": {
        "url": "https://company-dev.atlassian.net",
        "agile_fields": {
          "epic_link": "customfield_10200",
          "story_points": "customfield_10201"
        }
      }
    }
  }
}
```

### Environment Variable Override

```bash
export JIRA_EPIC_LINK_FIELD="customfield_10300"
export JIRA_STORY_POINTS_FIELD="customfield_10301"
export JIRA_EPIC_NAME_FIELD="customfield_10302"
export JIRA_EPIC_COLOR_FIELD="customfield_10303"
export JIRA_SPRINT_FIELD="customfield_10304"
```

## Field Discovery

The `jira-fields` skill provides field discovery capabilities through `configure_agile_fields.py`:

```bash
# Auto-detect and configure Agile fields
python configure_agile_fields.py PROJ --dry-run

# Specify field IDs manually
python configure_agile_fields.py PROJ --story-points customfield_10200
```

The `find_agile_fields()` function in `configure_agile_fields.py` searches for fields by name pattern:
- "story point" -> story_points
- "epic link" -> epic_link
- "sprint" -> sprint
- "epic name" -> epic_name

## Usage Notes

1. **Backward Compatibility**: Scripts continue to work with default field IDs if no configuration is provided.

2. **Profile-Specific**: Different JIRA instances can have different field IDs per profile.

3. **Environment Override**: Environment variables take highest priority, useful for CI/CD pipelines.

4. **Internal State**: Scripts store field IDs in results with `_` prefix (e.g., `_agile_fields`) for use in formatting, stripped from JSON output.

## Testing

To verify field IDs for your instance:

```bash
# List all custom fields
python .claude/skills/jira-fields/scripts/list_fields.py --type custom

# Check project field configuration
python .claude/skills/jira-fields/scripts/check_project_fields.py PROJ
```
