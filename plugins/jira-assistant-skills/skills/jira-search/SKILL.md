---
name: "jira-search-jql"
description: "Find issues by criteria (status, assignee, priority, etc.) using JQL. Create filters, export results to CSV/JSON, bulk update. Ideal for reporting and automation."
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# jira-search

Query and discovery operations for JIRA issues using JQL (JIRA Query Language).

## When to use this skill

### Perfect for:
- **Search by criteria:** "Find all bugs assigned to me in the current sprint"
- **Reporting:** Export sprint results or metrics to CSV/JSON
- **Bulk operations:** Update labels, priority, or assignee on 50+ issues at once
- **Automation:** Create saved filters for monitoring or dashboards

### Not ideal for:
- Single issue operations - Use **jira-issue** skill
- Workflow transitions on many issues - Use **jira-lifecycle** skill
- Complex issue relationships - Use **jira-relationships** skill
- Sprint/board management - Use **jira-agile** skill

## Quick Start

```bash
# Find your open issues
jira search query "assignee = currentUser() AND status != Done"

# Find bugs in a project
jira search query "project = PROJ AND type = Bug AND status = Open"

# Export results to CSV
jira search export "project = PROJ" --output report.csv

# Save a filter for reuse
jira search filter create "My Bugs" "type = Bug AND assignee = currentUser()" --favourite
```

For detailed setup, see [docs/QUICK_START.md](docs/QUICK_START.md).

## Available Commands

**IMPORTANT:** Always use the `jira` CLI. Never run Python scripts directly.

| Command | Purpose | Example |
|---------|---------|---------|
| `jira search query` | Execute JQL queries | `jira search query "project = PROJ"` |
| `jira search export` | Export to CSV/JSON | `jira search export "JQL" -o report.csv` |
| `jira search validate` | Check JQL syntax | `jira search validate "your query"` |
| `jira search build` | Build JQL from options | `jira search build --project PROJ --status Open` |
| `jira search suggest` | Get field value suggestions | `jira search suggest --field status` |
| `jira search fields` | List available JQL fields | `jira search fields` |
| `jira search functions` | List available JQL functions | `jira search functions` |
| `jira search filter list` | List saved filters | `jira search filter list --favourite` |
| `jira search filter create` | Save a reusable filter | `jira search filter create "Name" "JQL"` |
| `jira search filter run` | Run a saved filter | `jira search filter run 10042` |
| `jira search filter share` | Share filter with users/groups | `jira search filter share 10042 --project PROJ` |
| `jira search filter delete` | Delete a saved filter | `jira search filter delete 10042 --force` |

All commands support `--help` for full documentation.

## What this skill does

1. **JQL Search**: Execute custom queries with sorting, pagination, field selection
2. **JQL Builder**: Build and validate queries interactively
3. **Query History**: Save queries locally for quick reuse
4. **Saved Filters**: Full CRUD on JIRA filters with sharing
5. **Filter Subscriptions**: View email subscriptions on filters
6. **Export Results**: CSV, JSON, JSON Lines with streaming for large datasets
7. **Bulk Updates**: Update multiple issues from search results

## Common Options

| Option | Description |
|--------|-------------|
| `--profile` | JIRA profile to use (from settings.json) |
| `--help`, `-h` | Show help message and usage |
| `--output`, `-o` | Output format: `text` (default), `json` |
| `--max-results`, `-m` | Maximum results to return |
| `--fields` | Comma-separated list of fields |

## Examples by Category

### Search

```bash
# Basic search
jira search query "project = PROJ AND status = Open"

# With field selection
jira search query "project = PROJ" --fields key,summary,status,assignee

# With result limit
jira search query "project = PROJ" --max-results 50
```

### JQL Building

```bash
# Validate syntax
jira search validate "project = PROJ AND status = Open"

# Build JQL from options
jira search build --project PROJ --status Open --assignee currentUser()

# Get field suggestions
jira search suggest --field status
jira search suggest --field status --prefix "In"
jira search suggest --field assignee --prefix "john"

# List available fields and operators
jira search fields

# List available JQL functions
jira search functions
```

### Saved Filters

```bash
# Create filter
jira search filter create "Sprint Issues" "sprint IN openSprints()" --favourite

# List filters
jira search filter list --favourite

# Run filter (by filter ID)
jira search filter run 10042

# Share filter
jira search filter share 10042 --project PROJ

# Delete filter
jira search filter delete 10042 --force
```

### Export

```bash
# CSV export
jira search export "project = PROJ" -o report.csv

# JSON export
jira search export "project = PROJ" -o data.json --format json

# Export specific fields
jira search export "project = PROJ" -o report.csv --fields key,summary,status,assignee

# Limit results
jira search export "project = PROJ" -o report.csv --max-results 500
```

### Using Filters in Queries

```bash
# Run a query using a saved filter ID
jira search query --filter 10042

# Combine filter with additional criteria
jira search query --filter 10042 --max-results 100

# Save search results as a new filter
jira search query "project = PROJ" --save-as "My New Filter"
```

## Exporting Large Datasets

For large exports, optimize your query and field selection:

| Result Size | Recommendation |
|-------------|----------------|
| < 1000 | `jira search export "JQL" -o file.csv` |
| 1000-5000 | `jira search export "JQL" -o file.csv --fields key,summary,status` |
| > 5000 | Split by date ranges using created/updated filters |

```bash
# Large export with minimal fields for speed
jira search export "project = PROJ" -o report.csv --fields key,summary,status,assignee

# Split by time periods for very large datasets
jira search export "project = PROJ AND created >= -30d" -o recent.csv
jira search export "project = PROJ AND created >= -60d AND created < -30d" -o older.csv
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (API, validation) |
| 2 | Invalid arguments |
| 130 | User interrupted (Ctrl+C) |

## Troubleshooting

**Quick diagnostics:**
```bash
jira search validate "your query"     # Check syntax
jira search fields                    # List available fields
jira search suggest --field status    # Get valid values for a field
jira search functions                 # List available JQL functions
```

For detailed troubleshooting, see [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md).

## Configuration

Requires JIRA credentials via environment variables (`JIRA_SITE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`).

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/QUICK_START.md](docs/QUICK_START.md) | Get started in 5 minutes |
| [docs/SCRIPT_REFERENCE.md](docs/SCRIPT_REFERENCE.md) | All scripts with examples |
| [references/jql_reference.md](references/jql_reference.md) | JQL syntax reference |
| [references/BEST_PRACTICES.md](references/BEST_PRACTICES.md) | Expert guide |
| [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) | Error solutions |
| [assets/QUICK_REFERENCE.txt](assets/QUICK_REFERENCE.txt) | Printable cheat sheet |

## Templates

Pre-configured JQL templates:
- `assets/templates/jql_templates.json` - Common search patterns
- `assets/SCRIPT_SELECTOR.json` - Script selection guide
- `assets/ERROR_SOLUTIONS.json` - Error catalog

## Related skills

- **jira-issue**: For creating and updating individual issues
- **jira-lifecycle**: For transitioning issues found in searches
- **jira-collaborate**: For bulk commenting on search results
- **jira-agile**: For sprint and board operations
- **jira-relationships**: For issue linking and dependencies
- **jira-bulk**: For large-scale bulk operations
