# Configuration Guide

Cache configuration and settings.

## Cache Location

Cache is stored in `~/.jira-skills/cache/` as a SQLite database.

## TTL Defaults

| Category | TTL | Description |
|----------|-----|-------------|
| `issue` | 5 minutes | Issue data (frequently updated) |
| `project` | 1 hour | Project metadata |
| `user` | 1 hour | User information |
| `field` | 1 day | Field definitions |
| `search` | 1 minute | Search results |

## Custom TTL

Override TTL programmatically:

```python
from datetime import timedelta
from cache import JiraCache

cache = JiraCache()
cache.set(key, value, category="custom", ttl=timedelta(minutes=30))
```

## Profile Configuration

Use profiles for different JIRA instances:

```bash
# Development instance
python cache_warm.py --all --profile development

# Production instance
python cache_warm.py --all --profile production
```

Profile configuration is stored in `.claude/settings.json`:

```json
{
  "profiles": {
    "development": {
      "url": "https://dev.atlassian.net",
      "default_project": "DEV"
    },
    "production": {
      "url": "https://prod.atlassian.net",
      "default_project": "PROD"
    }
  }
}
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `JIRA_API_TOKEN` | API token from id.atlassian.com |
| `JIRA_EMAIL` | Atlassian account email |
| `JIRA_SITE_URL` | JIRA instance URL |
| `JIRA_PROFILE` | Default profile name |
