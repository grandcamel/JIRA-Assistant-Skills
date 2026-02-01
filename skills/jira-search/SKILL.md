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

## Risk Levels

| Operation | Risk | Notes |
|-----------|------|-------|
| Query/search | `-` | Read-only |
| Validate JQL | `-` | Read-only |
| Export results | `-` | Read-only (local file) |
| List filters | `-` | Read-only |
| Create filter | `-` | Easily reversible (can delete) |
| Update filter | `!` | Can be reverted |
| Share filter | `!` | Can be unshared |
| Delete filter | `!!` | Filter lost, but can recreate |
| Bulk update | `!!` | Use --dry-run first; changes reversible but tedious |

**Risk Legend**: `-` Safe, read-only | `!` Caution, modifiable | `!!` Warning, destructive but recoverable | `!!!` Danger, irreversible

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
jira-as search query "assignee = currentUser() AND status != Done"

# Find bugs in a project
jira-as search query "project = PROJ AND type = Bug AND status = Open"

# Export results to CSV
jira-as search export "project = PROJ" --output report.csv

# Save a filter for reuse
jira-as search filter create -n "My Bugs" -j "type = Bug AND assignee = currentUser()" -f
```

For detailed setup, see [docs/QUICK_START.md](docs/QUICK_START.md).

## Available Commands

**IMPORTANT:** Always use the `jira-as` CLI. Never run Python scripts directly.

| Command | Purpose | Example |
|---------|---------|---------|
| `jira-as search query` | Execute JQL queries | `jira-as search query "project = PROJ"` |
| `jira-as search export` | Export to CSV/JSON | `jira-as search export "JQL" -o report.csv` |
| `jira-as search validate` | Check JQL syntax | `jira-as search validate "your query"` |
| `jira-as search build` | Build JQL from clauses | `jira-as search build --clause "project = PROJ" --clause "status = Open"` |
| `jira-as search bulk-update` | Bulk update issues from search | `jira-as search bulk-update "JQL" --add-labels bug --dry-run` |
| `jira-as search suggest` | Get field value suggestions | `jira-as search suggest --field status --no-cache` |
| `jira-as search fields` | List available JQL fields | `jira-as search fields --custom-only` |
| `jira-as search functions` | List available JQL functions | `jira-as search functions --with-examples` |
| `jira-as search filter list` | List saved filters | `jira-as search filter list --favourites` |
| `jira-as search filter create` | Save a reusable filter | `jira-as search filter create --name "Name" --jql "JQL"` |
| `jira-as search filter update` | Update an existing filter | `jira-as search filter update 10042 --name "New Name"` |
| `jira-as search filter run` | Run a saved filter | `jira-as search filter run --id 10042` |
| `jira-as search filter favourite` | Toggle favourite status | `jira-as search filter favourite 10042 --add` |
| `jira-as search filter share` | Share filter with users/groups | `jira-as search filter share 10042 --project PROJ` |
| `jira-as search filter delete` | Delete a saved filter | `jira-as search filter delete 10042 --yes` |

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
| `--help`, `-h` | Show help message and usage |
| `--output`, `-o` | Output format: `text` (default), `json` |
| `--max-results`, `-m` | Maximum results to return |
| `--fields` | Comma-separated list of fields |
| `--show-links`, `-l` | Show issue links in output |
| `--show-time`, `-t` | Show time tracking info |
| `--show-agile`, `-a` | Show agile fields (story points, sprint) |
| `--page-token`, `-p` | Pagination token for large results |

## Examples by Category

### Search

```bash
# Basic search
jira-as search query "project = PROJ AND status = Open"

# With field selection
jira-as search query "project = PROJ" --fields key,summary,status,assignee

# With result limit
jira-as search query "project = PROJ" --max-results 50
```

### JQL Building

```bash
# Validate syntax (--show-structure shows parse tree, --output for format)
jira-as search validate "project = PROJ AND status = Open"
jira-as search validate "project = PROJ" --show-structure
jira-as search validate "project = PROJ" --output json

# Build JQL from clauses (--operator selects AND or OR between clauses)
jira-as search build --clause "project = PROJ" --clause "status = Open" --validate
jira-as search build --clause "status = Open" --clause "status = Closed" --operator OR
jira-as search build --clause "assignee = currentUser()" --order-by created --desc
jira-as search build --template sprint-backlog  # Use a predefined template
jira-as search build --list-templates           # List available templates

# Get field suggestions
jira-as search suggest --field status
jira-as search suggest --field status --prefix "In"
jira-as search suggest --field assignee --prefix "john"
jira-as search suggest --field priority --no-cache   # Skip cache
jira-as search suggest --field status --refresh      # Refresh cached values

# List available fields and operators
jira-as search fields
jira-as search fields --custom-only             # Only custom fields
jira-as search fields --system-only             # Only system fields
jira-as search fields --filter priority         # Filter by name

# List available JQL functions (-t is short for --type)
jira-as search functions
jira-as search functions -t list                # Only list-returning functions
jira-as search functions --list-only            # Only list-returning functions
jira-as search functions --with-examples        # Include usage examples
```

### Saved Filters

```bash
# Create filter (use -n and -j options, or long forms --name and --jql)
jira-as search filter create -n "Sprint Issues" -j "sprint IN openSprints()" -f
jira-as search filter create -n "Team Filter" -j "project = PROJ" -d "Team issues" --share-project PROJ

# List filters
jira-as search filter list --favourites          # Your favourite filters
jira-as search filter list --my                  # Your own filters
jira-as search filter list --search "Sprint"     # Search by name
jira-as search filter list --owner "john@co.com" # By owner
jira-as search filter list --project PROJ        # By project scope
jira-as search filter list --id 10042            # Get specific filter by ID

# Run filter (use --id or --name option)
jira-as search filter run --id 10042
jira-as search filter run --name "Sprint Issues"
jira-as search filter run --id 10042 --max-results 50  # Limit results

# Update filter
jira-as search filter update 10042 --name "New Name" --jql "updated JQL"
jira-as search filter update 10042 --description "New description"

# Toggle favourite status
jira-as search filter favourite 10042 --add
jira-as search filter favourite 10042 --remove

# Share filter
jira-as search filter share 10042 --project PROJ
jira-as search filter share 10042 --project PROJ --role Developers
jira-as search filter share 10042 --group jira-users
jira-as search filter share 10042 --global
jira-as search filter share 10042 --list         # View current permissions
jira-as search filter share 10042 --unshare 10100  # Remove permission by ID (use --list first)

# Delete filter (use --yes to skip confirmation, --dry-run to preview)
jira-as search filter delete 10042 --dry-run     # Preview deletion
jira-as search filter delete 10042 --yes         # Skip confirmation
```

### Bulk Update

```bash
# Add labels to all matching issues (dry-run first!)
jira-as search bulk-update "project = PROJ AND status = Open" --add-labels needs-review --dry-run
jira-as search bulk-update "project = PROJ AND status = Open" --add-labels needs-review --yes

# Remove labels
jira-as search bulk-update "type = Bug AND labels = stale" --remove-labels stale --dry-run

# Change priority
jira-as search bulk-update "project = PROJ AND priority = Low" --priority Medium --dry-run

# Limit number of issues updated
jira-as search bulk-update "project = PROJ" --add-labels batch1 --max-issues 50 --dry-run
```

### Export

```bash
# CSV export
jira-as search export "project = PROJ" -o report.csv

# JSON export
jira-as search export "project = PROJ" -o data.json --format json

# Export specific fields
jira-as search export "project = PROJ" -o report.csv --fields key,summary,status,assignee

# Limit results
jira-as search export "project = PROJ" -o report.csv --max-results 500
```

### Using Filters in Queries

```bash
# Run a query using a saved filter ID
jira-as search query --filter 10042

# Combine filter with additional criteria
jira-as search query --filter 10042 --max-results 100

# Save search results as a new filter
jira-as search query "project = PROJ" --save-as "My New Filter"
```

## Exporting Large Datasets

For large exports, optimize your query and field selection:

| Result Size | Recommendation |
|-------------|----------------|
| < 1000 | `jira-as search export "JQL" -o file.csv` |
| 1000-5000 | `jira-as search export "JQL" -o file.csv --fields key,summary,status` |
| > 5000 | Split by date ranges using created/updated filters |

```bash
# Large export with minimal fields for speed
jira-as search export "project = PROJ" -o report.csv --fields key,summary,status,assignee

# Split by time periods for very large datasets
jira-as search export "project = PROJ AND created >= -30d" -o recent.csv
jira-as search export "project = PROJ AND created >= -60d AND created < -30d" -o older.csv
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
jira-as search validate "your query"     # Check syntax
jira-as search fields                    # List available fields
jira-as search suggest --field status    # Get valid values for a field
jira-as search functions                 # List available JQL functions
```

For detailed troubleshooting, see [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md).

## Configuration

Requires JIRA credentials via environment variables (`JIRA_SITE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`).

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/QUICK_START.md](docs/QUICK_START.md) | Get started in 5 minutes |
| [references/jql_reference.md](references/jql_reference.md) | JQL syntax reference |
| [references/BEST_PRACTICES.md](references/BEST_PRACTICES.md) | Expert guide |
| [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) | Error solutions |
| [assets/QUICK_REFERENCE.txt](assets/QUICK_REFERENCE.txt) | Printable cheat sheet |

## Templates

Pre-configured JQL templates:
- `assets/templates/jql_templates.json` - Common search patterns
- `assets/ERROR_SOLUTIONS.json` - Error catalog

## Related skills

- **jira-issue**: For creating and updating individual issues
- **jira-lifecycle**: For transitioning issues found in searches
- **jira-collaborate**: For bulk commenting on search results
- **jira-agile**: For sprint and board operations
- **jira-relationships**: For issue linking and dependencies
- **jira-bulk**: For large-scale bulk operations
