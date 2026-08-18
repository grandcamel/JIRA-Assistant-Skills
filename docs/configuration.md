# Configuration Guide

Advanced configuration options for JIRA Assistant Skills.

---

## Configuration Priority

Settings are merged from multiple sources (highest priority first):

1. **Environment variables** — `JIRA_API_TOKEN`, `JIRA_EMAIL`, `JIRA_SITE_URL`
2. **System keychain** — via the `keyring` library, when available
3. **settings.local.json** — Personal credentials (gitignored)
4. **settings.json** — Team defaults (committed)
5. **Hardcoded defaults** — Fallback values

> **Note:** This order applies to credentials. Agile field IDs resolve in the
> opposite direction — settings-file values override the env vars — see
> [Agile Field Mapping](#agile-field-mapping) below.

---

## Settings File

Credentials and defaults live under the `jira` key in
`.claude/settings.local.json` (personal, gitignored) or
`.claude/settings.json` (shared, non-secret values only):

```json
{
  "jira": {
    "credentials": {
      "url": "https://company.atlassian.net",
      "email": "you@company.com",
      "api_token": "your-api-token"
    },
    "default_project": "PROJ",
    "api": {
      "timeout": 30,
      "max_retries": 3,
      "retry_backoff": 2.0
    }
  }
}
```

Only put `api_token` in `settings.local.json` or the keychain — never in the
shared `settings.json`.

### Multiple JIRA Instances

The CLI connects to one instance at a time. To switch instances, change the
environment variables (highest priority), e.g. with per-instance env files or
shell aliases:

```bash
# Staging
export JIRA_SITE_URL="https://company-staging.atlassian.net"

# Production
export JIRA_SITE_URL="https://company.atlassian.net"
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `JIRA_API_TOKEN` | API token from Atlassian |
| `JIRA_EMAIL` | Your Atlassian account email |
| `JIRA_SITE_URL` | JIRA instance URL (https://...) |
| `JIRA_MOCK_MODE` | `true` to use the mock client (no API calls) |
| `JIRA_EPIC_LINK_FIELD` | Override Epic Link field ID |
| `JIRA_STORY_POINTS_FIELD` | Override Story Points field ID |
| `JIRA_EPIC_NAME_FIELD` | Override Epic Name field ID |
| `JIRA_EPIC_COLOR_FIELD` | Override Epic Color field ID |
| `JIRA_SPRINT_FIELD` | Override Sprint field ID |
| `JIRA_ADF_CUSTOM_FIELDS` | Comma-separated custom field IDs to auto-wrap as ADF rich text |

---

## Agile Field Mapping

Custom field IDs differ between JIRA instances (and sometimes between
projects). Resolution order, lowest priority first: built-in defaults,
environment variables, the global `jira.agile_fields` block, then per-project
`jira.projects.<KEY>.agile_fields` overrides:

```json
{
  "jira": {
    "agile_fields": {
      "story_points": "customfield_10016",
      "epic_link": "customfield_10014",
      "sprint": "customfield_10020"
    },
    "projects": {
      "MYAPP": {
        "agile_fields": {
          "story_points": "customfield_10102"
        }
      }
    }
  }
}
```

Use `jira-as fields check-project PROJ --check-agile` to discover the right
IDs for your instance.

---

## See Also

- [Quick Start Guide](quick-start.md)
- [CLI Reference](CLI_REFERENCE.md)
- [Troubleshooting](troubleshooting.md)
