# Configuration Guide

Advanced configuration options for JIRA Assistant Skills.

---

## Configuration Priority

Settings are merged from multiple sources (highest priority first):

1. **Environment variables** — `JIRA_API_TOKEN`, `JIRA_EMAIL`, `JIRA_SITE_URL`
2. **settings.local.json** — Personal credentials (gitignored)
3. **settings.json** — Team defaults (committed)
4. **Hardcoded defaults** — Fallback values

---

## Multi-Profile Setup

Manage multiple JIRA instances (dev, staging, production):

```json
{
  "jira": {
    "default_profile": "production",
    "profiles": {
      "production": {
        "url": "https://company.atlassian.net",
        "email": "you@company.com",
        "project_keys": ["PROD", "OPS"],
        "default_project": "PROD"
      },
      "staging": {
        "url": "https://company-staging.atlassian.net",
        "email": "you@company.com",
        "project_keys": ["STG"],
        "default_project": "STG"
      },
      "development": {
        "url": "https://company-dev.atlassian.net",
        "email": "you@company.com",
        "project_keys": ["DEV", "TEST"],
        "default_project": "DEV"
      }
    }
  }
}
```

### Using Profiles

```bash
# Use specific profile
python script.py PROJ-123 --profile development

# Or set environment variable
export JIRA_PROFILE=development
python script.py PROJ-123
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `JIRA_API_TOKEN` | API token from Atlassian |
| `JIRA_EMAIL` | Your Atlassian account email |
| `JIRA_SITE_URL` | JIRA instance URL (https://...) |
| `JIRA_PROFILE` | Profile name to use |

---

## JSM Configuration

For Jira Service Management, add `use_service_management`:

```json
{
  "jira": {
    "profiles": {
      "support": {
        "url": "https://company.atlassian.net",
        "use_service_management": true,
        "default_service_desk_id": 1
      }
    }
  }
}
```

---

## Custom Field Mapping

Map custom field IDs for your JIRA instance:

```json
{
  "jira": {
    "custom_fields": {
      "story_points": "customfield_10016",
      "epic_link": "customfield_10014",
      "epic_name": "customfield_10011"
    }
  }
}
```

---

## See Also

- [Quick Start Guide](quick-start.md)
- [Scripts Reference](scripts-reference.md)
- [Troubleshooting](troubleshooting.md)
