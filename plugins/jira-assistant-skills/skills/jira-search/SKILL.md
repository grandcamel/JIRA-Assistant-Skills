---
name: "JIRA Search & JQL"
description: "Find issues by criteria (status, assignee, priority, etc.) using JQL. Create filters, export results to CSV/JSON, bulk update. Ideal for reporting and automation."
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
python jql_search.py "assignee = currentUser() AND status != Done"

# Find bugs in a project
python jql_search.py "project = PROJ AND type = Bug AND status = Open"

# Export results to CSV
python export_results.py "project = PROJ" --output report.csv

# Save a filter for reuse
python create_filter.py "My Bugs" "type = Bug AND assignee = currentUser()" --favourite
```

For detailed setup, see [docs/QUICK_START.md](docs/QUICK_START.md).

## Most Common Scripts

| Script | Purpose | Example |
|--------|---------|---------|
| `jql_search.py` | Execute JQL queries | `python jql_search.py "project = PROJ"` |
| `export_results.py` | Export to CSV/JSON | `python export_results.py "JQL" -o report.csv` |
| `create_filter.py` | Save a reusable filter | `python create_filter.py "Name" "JQL"` |
| `jql_validate.py` | Check JQL syntax | `python jql_validate.py "your query"` |
| `run_filter.py` | Run a saved filter | `python run_filter.py --name "Filter"` |

For all 18 scripts, see [docs/SCRIPT_REFERENCE.md](docs/SCRIPT_REFERENCE.md).

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
python jql_search.py "project = PROJ AND status = Open"

# With field selection
python jql_search.py "project = PROJ" --fields key,summary,status,assignee

# With result limit
python jql_search.py "project = PROJ" --max-results 50
```

### JQL Building

```bash
# Validate syntax
python jql_validate.py "project = PROJ AND status = Open"

# Interactive builder
python jql_interactive.py

# Get field suggestions
python jql_suggest.py status
```

### Saved Filters

```bash
# Create filter
python create_filter.py "Sprint Issues" "sprint IN openSprints()" --favourite

# List filters
python get_filters.py --mine

# Run filter
python run_filter.py --name "Sprint Issues"

# Share filter
python share_filter.py 10042 --project PROJ
```

### Export

```bash
# CSV export
python export_results.py "project = PROJ" --output report.csv

# JSON export
python export_results.py "project = PROJ" --output data.json --format json

# Large export (>5000 issues)
python streaming_export.py "project = PROJ" --output report.csv --enable-checkpoint
```

### Query History

```bash
# Save query locally
python jql_history.py --add "project = PROJ" --name my-query

# List saved queries
python jql_history.py --list

# Run saved query
python jql_history.py --run my-query
```

## Streaming Export for Large Datasets

For exports >5000 issues, use `streaming_export.py`:

| Result Size | Recommendation |
|-------------|----------------|
| < 1000 | `export_results.py` |
| 1000-5000 | `export_results.py --fields key,summary,status` |
| 5000-50000 | `streaming_export.py --enable-checkpoint` |
| > 50000 | Split by date ranges |

```bash
# Resumable export
python streaming_export.py "project = PROJ" --output report.csv --enable-checkpoint

# Resume if interrupted
python streaming_export.py --resume export-20251226-143022
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
python jql_validate.py "your query"  # Check syntax
python jql_fields.py                 # List fields
python jql_suggest.py status         # Get values
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
