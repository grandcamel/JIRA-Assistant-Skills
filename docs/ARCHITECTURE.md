# Architecture

This document covers the technical architecture of the JIRA Assistant Skills plugin.

## Shared Library Pattern

All skills depend on the `jira-as` PyPI package:

```bash
pip install jira-as>=0.2.0
```

### Core Modules

| Module | Purpose |
|--------|---------|
| `JiraClient` | HTTP client with automatic retry (3 attempts, exponential backoff on 429/5xx) |
| `ConfigManager` | Multi-source config merging (env vars > settings.local.json > settings.json > defaults) |
| `validators` | Input validation (issue keys: `^[A-Z][A-Z0-9]*-[0-9]+$`, URLs: HTTPS-only) |
| `formatters` | Output formatting (tables via tabulate, JSON, CSV export) |
| `adf_helper` | Markdown to Atlassian Document Format conversion |

### Config Helpers

- `get_agile_fields()` / `get_agile_field()` - Agile field IDs
- `get_project_defaults()` - Issue defaults per project

### Utilities

| Utility | Purpose |
|---------|---------|
| `JiraCache`, `get_cache` | SQLite-based caching with TTL support |
| `RequestBatcher`, `batch_fetch_issues` | Concurrent API requests |
| `BatchProcessor`, `BatchConfig` | Large-scale operations with checkpoints |
| `ProjectContext`, `get_project_context` | Project metadata and defaults |
| `find_transition_by_name`, `find_transition_by_keywords` | Fuzzy transition matching |
| `resolve_user_to_account_id`, `get_user_display_info` | User resolution |
| `parse_time_string`, `format_seconds` | Time parsing and formatting |

**Import pattern**: `from jira_as import ...`

## Configuration System

Configuration is loaded from environment variables (recommended):

| Variable | Purpose |
|----------|---------|
| `JIRA_API_TOKEN` | API token from id.atlassian.com/manage-profile/security/api-tokens |
| `JIRA_EMAIL` | Atlassian account email |
| `JIRA_SITE_URL` | JIRA instance URL (e.g., https://company.atlassian.net) |
| `JIRA_PROFILE` | Optional profile name for multi-instance support |

See `config/settings.example.json` for profile-based configuration.

## Error Handling Strategy

4-layer approach:

1. **Pre-validation**: validators.py catches bad input before API calls
2. **API errors**: error_handler.handle_jira_error() maps status codes to exceptions with troubleshooting hints
3. **Retry logic**: JiraClient retries on [429, 500, 502, 503, 504] with exponential backoff
4. **User messages**: Exceptions include contextual help (e.g., AuthenticationError suggests checking token at specific URL)

## ADF Conversion

JIRA Cloud requires Atlassian Document Format for rich text:

| Function | Purpose |
|----------|---------|
| `text_to_adf()` | Plain text → ADF paragraphs |
| `markdown_to_adf()` | Markdown → ADF (headings, bold, italic, code, lists, links) |
| `adf_to_text()` | ADF → plain text extraction |

CLI commands accept `--format` flag: text (default), markdown, or adf (raw JSON).

## Common API Patterns

### Agile Custom Fields

Story point and epic link fields vary by JIRA instance. Default field IDs:

| Field | Default ID |
|-------|------------|
| Epic Link | `customfield_10014` |
| Story Points | `customfield_10016` |
| Epic Name | `customfield_10011` |
| Epic Color | `customfield_10012` |

### Sprint Operations

Use the Agile API (`/rest/agile/1.0/`) for sprint and board operations. Sprints require board context for creation.

### Issue Linking

Use the Issue Link API (`/rest/api/3/issueLink`) for creating relationships:

- Link types: Blocks, Cloners, Duplicate, Relates (names may vary by instance)
- Direction: inward (is blocked by) vs outward (blocks)
- Blocker chains: Traverse recursively with visited set to detect cycles

### Issue Cloning

Use `jira_client.clone_issue()` for copying issues:

- Copies: summary, description, priority, labels, components, fixVersions
- Creates "Cloners" link between clone and original
- Optional flags: `clone_subtasks=True`, `clone_links=True`

### Time Tracking

Use the Worklog API (`/rest/api/3/issue/{key}/worklog`) for time management:

- Time format: JIRA accepts human-readable formats like '2h', '1d 4h', '30m', '1w'
- Estimate adjustment: Use `adjustEstimate` parameter (auto, leave, new, manual)
- Known bug JRACLOUD-67539: Always set both originalEstimate and remainingEstimate together

### JQL and Advanced Search

| API | Purpose |
|-----|---------|
| `/rest/api/3/jql/autocompletedata` | Fields, operators, functions |
| `/rest/api/3/jql/parse` | Validation with error suggestions |
| `/rest/api/3/jql/autocompletedata/suggestions` | Field value completion |
| `/rest/api/3/filter` | Filter CRUD |
| `/rest/api/3/filter/{id}/permission` | Filter sharing |

**Default search fields**: `key, summary, status, priority, issuetype, assignee, reporter`

### JQL Query Patterns

```jql
# User-based
assignee = currentUser()
assignee in membersOf("developers")

# Time-based
created >= startOfDay(-7d)
updated >= startOfWeek() AND updated <= endOfWeek()

# Status-based
status = "In Progress"
status changed FROM "In Progress" TO Done DURING (startOfDay(-1d), now())

# Combined
project = PROJ AND type = Bug AND priority in (High, Highest) ORDER BY created DESC
```
