# JIRA Search Script Reference

Complete catalog of all jira-search scripts organized by category.

---

## Quick Selection Guide

| I want to... | Script | Example |
|--------------|--------|---------|
| Find issues by criteria | `jql_search.py` | `python jql_search.py "project = PROJ"` |
| Save a search for reuse | `create_filter.py` | `python create_filter.py "Name" "JQL"` |
| Export results to file | `export_results.py` | `python export_results.py "JQL" -o file.csv` |
| Validate JQL syntax | `jql_validate.py` | `python jql_validate.py "JQL"` |
| Build a query step-by-step | `jql_interactive.py` | `python jql_interactive.py` |
| Export large datasets | `streaming_export.py` | `python streaming_export.py "JQL" -o file.csv` |

---

## JQL Builder/Assistant

Scripts for building and validating JQL queries.

### jql_fields.py
List searchable fields and their operators.

```bash
python jql_fields.py                    # List all fields
python jql_fields.py --filter "status"  # Filter by name
python jql_fields.py --custom-only      # Show only custom fields
```

### jql_functions.py
List JQL functions with examples.

```bash
python jql_functions.py                 # List all functions
python jql_functions.py --filter "day"  # Filter date/time functions
```

### jql_validate.py
Validate JQL syntax before running.

```bash
python jql_validate.py "project = PROJ AND status = Open"
```

### jql_suggest.py
Get autocomplete suggestions for field values.

```bash
python jql_suggest.py status            # List all status values
python jql_suggest.py status --value "In"  # Filter suggestions
python jql_suggest.py priority          # List priority values
```

### jql_build.py
Build JQL queries from templates or clauses.

```bash
python jql_build.py --project PROJ --status Open --type Bug
python jql_build.py --clause "assignee = currentUser()" --clause "status != Done"
```

### jql_interactive.py
Interactive guided query builder.

```bash
python jql_interactive.py               # Start interactive mode
python jql_interactive.py --quick       # Quick mode (common fields only)
python jql_interactive.py --start-with "project = PROJ"
```

---

## Query History

### jql_history.py
Manage local JQL query history.

```bash
# List saved queries
python jql_history.py --list
python jql_history.py --list --top 10 --sort use_count

# Save a query
python jql_history.py --add "project = PROJ" --name my-query
python jql_history.py --add "JQL" --name NAME --description "Description"

# Run a saved query
python jql_history.py --run my-query
python jql_history.py --run my-query --max-results 100

# Delete queries
python jql_history.py --delete my-query
python jql_history.py --clear

# Import/export
python jql_history.py --export history.json
python jql_history.py --import history.json
python jql_history.py --import history.json --replace
```

---

## Search

### jql_search.py
Execute JQL queries and display results.

```bash
# Basic search
python jql_search.py "project = PROJ AND status = Open"

# With options
python jql_search.py "JQL" --max-results 50
python jql_search.py "JQL" --fields key,summary,status
python jql_search.py "JQL" --output json
```

---

## Saved Filters

### create_filter.py
Create a new saved filter.

```bash
python create_filter.py "Filter Name" "JQL query"
python create_filter.py "My Bugs" "type = Bug" --favourite
python create_filter.py "Sprint" "sprint IN openSprints()" --description "Active sprint"
```

### get_filters.py
List saved filters.

```bash
python get_filters.py --mine        # Your filters
python get_filters.py --favourites  # Favourite filters
python get_filters.py --search "sprint"  # Search by name
```

### run_filter.py
Execute a saved filter.

```bash
python run_filter.py --id 10042
python run_filter.py --name "My Open Issues"
python run_filter.py --name "Sprint" --max-results 100
python run_filter.py --id 10042 --output json
```

### update_filter.py
Update filter properties.

```bash
python update_filter.py 10042 --name "New Name"
python update_filter.py 10042 --jql "new JQL query"
python update_filter.py 10042 --description "Updated description"
```

### delete_filter.py
Delete a saved filter.

```bash
python delete_filter.py 10042
python delete_filter.py 10042 --yes  # Skip confirmation
```

### favourite_filter.py
Manage filter favourites.

```bash
python favourite_filter.py 10042 --add     # Add to favourites
python favourite_filter.py 10042 --remove  # Remove from favourites
python favourite_filter.py 10042           # Toggle
```

---

## Filter Sharing & Subscriptions

### share_filter.py
Manage filter sharing permissions.

```bash
# Share with project
python share_filter.py 10042 --project PROJ

# Share with role
python share_filter.py 10042 --project PROJ --role Developers

# Share with group
python share_filter.py 10042 --group engineering

# Share globally
python share_filter.py 10042 --global

# View/remove permissions
python share_filter.py 10042 --list
python share_filter.py 10042 --unshare 456
```

### filter_subscriptions.py
View email subscriptions for a filter.

```bash
python filter_subscriptions.py 10042
```

---

## Export & Bulk Operations

### export_results.py
Export search results to file.

```bash
# Basic export
python export_results.py "project = PROJ" --output report.csv

# Format options
python export_results.py "JQL" --output issues.json --format json
python export_results.py "JQL" --output data.jsonl --format jsonl

# Field selection
python export_results.py "JQL" --output report.csv --fields key,summary,status,priority

# With limits
python export_results.py "JQL" --output report.csv --max-results 5000
```

### streaming_export.py
Streaming export for large datasets (>5000 issues).

```bash
# Basic streaming
python streaming_export.py "project = PROJ" --output report.csv

# With checkpoints (resumable)
python streaming_export.py "JQL" --output report.csv --enable-checkpoint

# Resume interrupted export
python streaming_export.py --resume export-20251226-143022

# List pending exports
python streaming_export.py --list-checkpoints

# Options
python streaming_export.py "JQL" --output report.csv --page-size 200
python streaming_export.py "JQL" --output report.csv --max-results 50000
python streaming_export.py "JQL" --output report.csv --no-progress
```

### bulk_update.py
Bulk update issues from search results.

```bash
python bulk_update.py "project = PROJ AND labels = old" --add-labels "new-label"
```

---

## Common Options

All scripts support these options:

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help and usage examples |
| `--profile` | JIRA profile to use (from settings.json) |
| `--output`, `-o` | Output format: `text` (default), `json` |

### Search/Export Options

| Option | Description |
|--------|-------------|
| `--max-results`, `-m` | Maximum results to return |
| `--fields` | Comma-separated field list |
| `--format`, `-f` | Export format: `csv`, `json`, `jsonl` |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (API, validation) |
| 2 | Invalid arguments |
| 130 | User interrupted (Ctrl+C) |
