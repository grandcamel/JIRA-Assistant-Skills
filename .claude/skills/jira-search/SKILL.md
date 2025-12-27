---
name: "JIRA Search & JQL"
description: "Query and discovery operations using JQL - search, filters, export, bulk operations. Use when searching issues, building JQL queries, managing saved filters, or exporting results."
---

# jira-search

Query and discovery operations for JIRA issues using JQL (JIRA Query Language).

## When to use this skill

Use this skill when you need to:
- Search for issues using JQL queries
- Find issues by project, status, assignee, or other criteria
- Build and validate JQL queries
- Manage saved filters (create, update, delete, share)
- Execute saved filters
- Export search results to CSV or JSON
- Perform bulk operations on search results
- Generate reports on issue sets
- Track and reuse JQL query history
- Build JQL queries interactively with guidance

## What this skill does

This skill provides powerful search and query capabilities:

1. **JQL Search**: Execute custom JQL queries
   - Search by any field or combination of fields
   - Sort and order results
   - Pagination support for large result sets
   - Field selection to optimize performance

2. **JQL Builder/Assistant**: Build and validate JQL queries
   - List available fields and their operators
   - List JQL functions with examples
   - Validate JQL syntax with error suggestions
   - Get autocomplete suggestions for field values
   - Build queries from templates or clauses
   - Interactive guided query building

3. **Query History**: Local query management
   - Save queries with names for quick reuse
   - Track query usage statistics
   - Import/export query collections
   - Run saved queries directly

4. **Saved Filters**: Full CRUD operations on saved filters
   - Create new filters from JQL
   - List your filters and favourites
   - Update filter name, JQL, or description
   - Delete filters you own
   - Manage favourite filters
   - Run saved filters by ID or name

5. **Filter Sharing**: Share filters with teams
   - Share with project members
   - Share with specific project roles
   - Share with groups
   - Share with individual users
   - Share globally (all authenticated users)

6. **Filter Subscriptions**: View email subscriptions
   - List users subscribed to a filter
   - View subscription details

7. **Export Results**: Export search results
   - Export to CSV format
   - Export to JSON format
   - Export to JSON Lines format (for large datasets)
   - Select specific fields to export
   - Format for reporting or analysis
   - Streaming export for large result sets (>10k issues)
   - Checkpoint/resume support for interrupted exports

8. **Bulk Updates**: Update multiple issues at once
   - Apply changes to search results
   - Bulk assign, label, or prioritize
   - Mass transitions (with caution)

## Available scripts

### JQL Builder/Assistant
- `jql_fields.py` - List searchable fields and their operators
- `jql_functions.py` - List JQL functions with examples
- `jql_validate.py` - Validate JQL syntax
- `jql_suggest.py` - Get autocomplete suggestions for field values
- `jql_build.py` - Build JQL queries from templates or clauses
- `jql_interactive.py` - Interactive JQL query builder with guided prompts

### Query History
- `jql_history.py` - Manage local JQL query history (save, list, run, delete)

### Search
- `jql_search.py` - Execute JQL queries

### Saved Filters
- `create_filter.py` - Create a new saved filter
- `get_filters.py` - List saved filters (my filters, favourites, search)
- `run_filter.py` - Run a saved filter by ID or name
- `update_filter.py` - Update filter properties
- `delete_filter.py` - Delete a saved filter
- `favourite_filter.py` - Add/remove filter from favourites

### Filter Sharing & Subscriptions
- `share_filter.py` - Manage filter sharing permissions
- `filter_subscriptions.py` - View filter subscriptions

### Export & Bulk Operations
- `export_results.py` - Export search results to file
- `streaming_export.py` - Streaming export with checkpoints for large datasets (>10k issues)
- `bulk_update.py` - Bulk update issues from search

## Common Options

All scripts support these common options:

| Option | Description |
|--------|-------------|
| `--profile` | JIRA profile to use (from settings.json) |
| `--help`, `-h` | Show help message and usage examples |
| `--output`, `-o` | Output format: `text` (default), `json` |

### Search/Export Options

| Option | Description |
|--------|-------------|
| `--max-results`, `-m` | Maximum number of results to return |
| `--fields` | Comma-separated list of fields to include |
| `--format`, `-f` | Export format: `csv`, `json`, `jsonl` |

## Templates

Pre-configured JQL templates for common queries:
- `jql_templates.json` - Common search patterns

## Examples

### JQL Builder/Assistant

```bash
# List all searchable fields
python jql_fields.py

# Filter fields by name
python jql_fields.py --filter "status"

# Show only custom fields
python jql_fields.py --custom-only

# List JQL functions
python jql_functions.py

# List date/time functions only
python jql_functions.py --filter "day"

# Validate JQL syntax
python jql_validate.py "project = PROJ AND status = Open"

# Get value suggestions for a field
python jql_suggest.py status
python jql_suggest.py status --value "In"

# Build a JQL query
python jql_build.py --project PROJ --status Open --type Bug
python jql_build.py --clause "assignee = currentUser()" --clause "status != Done"
```

### Interactive Query Builder

```bash
# Start interactive builder
python jql_interactive.py

# Start with an existing clause
python jql_interactive.py --start-with "project = PROJ"

# Quick mode - prompts for common fields only
python jql_interactive.py --quick

# Use specific JIRA profile
python jql_interactive.py --profile development
```

### Query History

```bash
# List all saved queries
python jql_history.py --list

# Add a new query with a name
python jql_history.py --add "project = PROJ AND status = Open" --name my-issues

# Add a query with description
python jql_history.py --add "assignee = currentUser()" --name assigned --description "My assigned issues"

# Run a saved query by name
python jql_history.py --run my-issues

# Run a saved query by ID
python jql_history.py --run 5

# Run with custom result limit
python jql_history.py --run my-issues --max-results 100

# Show top 10 most used queries
python jql_history.py --list --top 10 --sort use_count

# Delete a query
python jql_history.py --delete 3
python jql_history.py --delete my-issues

# Clear all history
python jql_history.py --clear

# Export history to file
python jql_history.py --export history.json

# Import history (merge with existing)
python jql_history.py --import history.json

# Import history (replace existing)
python jql_history.py --import history.json --replace
```

### Search

```bash
# Search for open bugs
python jql_search.py "project = PROJ AND type = Bug AND status = Open"

# Find my issues
python jql_search.py "assignee = currentUser() AND status != Done"

# Search with specific fields
python jql_search.py "project = PROJ" --fields key,summary,status
```

### Saved Filters

```bash
# List my filters
python get_filters.py --mine

# List favourite filters
python get_filters.py --favourites

# Search filters by name
python get_filters.py --search "sprint"

# Create a new filter
python create_filter.py "Sprint Issues" "sprint in openSprints()"
python create_filter.py "My Bugs" "project = PROJ AND type = Bug" --favourite

# Run a saved filter by ID
python run_filter.py --id 10042

# Run a saved filter by name
python run_filter.py --name "My Open Issues"

# Run filter with custom result limit
python run_filter.py --name "Sprint Issues" --max-results 100

# Run filter with JSON output
python run_filter.py --id 10042 --output json

# Update a filter
python update_filter.py 10042 --name "New Name"
python update_filter.py 10042 --jql "project = NEW AND type = Bug"

# Delete a filter
python delete_filter.py 10042
python delete_filter.py 10042 --yes  # Skip confirmation

# Manage favourites
python favourite_filter.py 10042 --add
python favourite_filter.py 10042 --remove
python favourite_filter.py 10042  # Toggle
```

### Filter Sharing

```bash
# Share with project
python share_filter.py 10042 --project PROJ

# Share with project role
python share_filter.py 10042 --project PROJ --role Developers

# Share with group
python share_filter.py 10042 --group developers

# Share globally
python share_filter.py 10042 --global

# List current permissions
python share_filter.py 10042 --list

# Remove a permission
python share_filter.py 10042 --unshare 456
```

### Filter Subscriptions

```bash
# View subscriptions
python filter_subscriptions.py 10042
```

### Export & Bulk Operations

```bash
# Export to CSV
python export_results.py "project = PROJ AND created >= -7d" --output report.csv

# Export to JSON
python export_results.py "project = PROJ" --output issues.json --format json

# Export specific fields only
python export_results.py "project = PROJ" --output report.csv --fields key,summary,status,priority

# Export large result sets (pagination handled automatically)
python export_results.py "project = PROJ" --output all-issues.csv --max-results 5000

# Bulk update labels
python bulk_update.py "project = PROJ AND labels = old-label" --add-labels "new-label"
```

### Streaming Export for Large Datasets

```bash
# Basic streaming export to CSV
python streaming_export.py "project = PROJ" --output report.csv

# Export to JSON Lines format (recommended for large datasets)
python streaming_export.py "project = PROJ" --output report.jsonl --format jsonl

# Export with custom page size (for rate limiting)
python streaming_export.py "project = PROJ" --output report.csv --page-size 200

# Export up to 50,000 issues
python streaming_export.py "project = PROJ" --output report.csv --max-results 50000

# Enable checkpoints for resumable exports
python streaming_export.py "project = PROJ" --output report.csv --enable-checkpoint

# List pending (incomplete) exports
python streaming_export.py --list-checkpoints

# Resume an interrupted export
python streaming_export.py --resume export-20231215-143022

# Export specific fields only
python streaming_export.py "project = PROJ" --output report.csv \
  --fields key,summary,status,priority,assignee,reporter

# Disable progress bar (for scripting)
python streaming_export.py "project = PROJ" --output report.csv --no-progress
```

## Streaming Export for Large Data Sets

When exporting large numbers of issues (>1000), the export_results.py script automatically handles pagination to fetch all results efficiently.

For very large exports (>10,000 issues), use `streaming_export.py` which provides:

### Advanced Streaming Features

1. **Checkpoint/Resume**: Enable with `--enable-checkpoint` to save progress periodically. If interrupted, resume with `--resume <operation-id>`.

2. **JSON Lines Format**: Use `--format jsonl` for memory-efficient exports where each line is a valid JSON object. Ideal for processing with tools like `jq`.

3. **Configurable Page Size**: Adjust `--page-size` to balance between API efficiency and rate limiting.

4. **Progress Tracking**: Shows a progress bar with tqdm (install with `pip install tqdm`).

### How Streaming Export Works

1. **Automatic Pagination**: Results are fetched in batches (default 100 issues per request)
2. **Memory Efficient**: Issues are written to file as they're fetched, not held in memory
3. **Progress Tracking**: Shows progress for large exports
4. **Resumable**: If interrupted, simply re-run the export with `--resume`

### Usage Examples

```bash
# Export all issues from a project (may be thousands)
python export_results.py "project = PROJ" --output all-issues.csv --max-results 10000

# Export with specific fields to reduce response size
python export_results.py "project = PROJ" \
  --output minimal.csv \
  --fields key,summary,status \
  --max-results 10000

# Export to JSON for programmatic processing
python export_results.py "project = PROJ AND created >= -30d" \
  --output monthly-report.json \
  --format json \
  --max-results 5000
```

### Performance Considerations

| Result Size | Estimated Time | Recommendation |
|-------------|---------------|----------------|
| < 100 | < 5 seconds | Default settings work well |
| 100-1000 | 5-30 seconds | Consider specifying only needed fields |
| 1000-5000 | 30 seconds - 2 minutes | Use `--fields` to limit data |
| 5000-50000 | 2-20 minutes | Use `streaming_export.py` with checkpoints |
| > 50000 | 20+ minutes | Split by date ranges, use checkpoints |

### Optimizing Large Exports

**1. Limit Fields**
Only request the fields you need to reduce API response size and processing time:
```bash
python export_results.py "project = PROJ" \
  --fields key,summary,status,priority,created,updated \
  --output optimized.csv
```

**2. Split by Date Range**
For very large exports, split into smaller date ranges:
```bash
# Export by quarter
python export_results.py "project = PROJ AND created >= 2025-01-01 AND created < 2025-04-01" \
  --output q1-2025.csv

python export_results.py "project = PROJ AND created >= 2025-04-01 AND created < 2025-07-01" \
  --output q2-2025.csv
```

**3. Export During Off-Peak Hours**
Large exports consume API quota. Run during off-peak hours to avoid rate limiting:
```bash
# Schedule for late night
at 2:00 AM <<< 'python export_results.py "project = PROJ" --output nightly-export.csv'
```

### Output Formats

**CSV Format** (default):
```csv
key,summary,status,priority,issuetype,assignee,reporter,created,updated
PROJ-123,Fix login bug,Done,High,Bug,john.doe,2025-01-15,2025-01-20
PROJ-124,Add dark mode,In Progress,Medium,Story,jane.smith,2025-01-16,2025-01-21
```

**JSON Format**:
```json
{
  "issues": [
    {
      "key": "PROJ-123",
      "summary": "Fix login bug",
      "status": "Done",
      "priority": "High"
    }
  ],
  "total": 2
}
```

**JSON Lines Format** (one JSON object per line):
```json
{"key": "PROJ-123", "summary": "Fix login bug", "status": "Done"}
{"key": "PROJ-124", "summary": "Add dark mode", "status": "In Progress"}
```

## JQL Basics

**Basic Syntax:**
```
field operator value
```

**Example Queries:**
- `status = "In Progress"` - Issues in progress
- `assignee = currentUser()` - Your issues
- `created >= -7d` - Created in last 7 days
- `project = PROJ AND priority = High` - High priority in project

**Common Operators:**
- `=, !=` - Equals, not equals
- `~, !~` - Contains, does not contain (for text)
- `<, >, <=, >=` - Comparison operators
- `in, not in` - List membership
- `is, is not` - For EMPTY/NULL checks
- `was, was in, was not, was not in` - Historical values
- `changed` - Field was changed

**Useful Functions:**
- `currentUser()` - The logged-in user
- `membersOf("group")` - Users in a group
- `startOfDay(), endOfDay()` - Date boundaries
- `startOfWeek(), endOfWeek()` - Week boundaries
- `now()` - Current timestamp

See `references/jql_reference.md` for comprehensive JQL documentation.

## Exit Codes

All scripts return consistent exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (API error, validation error, etc.) |
| 2 | Invalid arguments or usage error |
| 130 | Interrupted by user (Ctrl+C) |

## Troubleshooting

### Common Issues

**"Authentication failed" or 401 errors**
- Verify your API token is valid at https://id.atlassian.com/manage-profile/security/api-tokens
- Check that `JIRA_EMAIL` matches the email for your API token
- Ensure `JIRA_SITE_URL` is correct (e.g., `https://company.atlassian.net`)

**"No issues found" when you expect results**
- Verify the JQL syntax with `python jql_validate.py "your query"`
- Check field names are correct with `python jql_fields.py --filter "fieldname"`
- Ensure you have permission to view the issues/project
- Quote values with spaces: `status = "In Progress"` not `status = In Progress`

**"Filter not found" errors**
- Use `python get_filters.py --mine` to list your filters
- Check if the filter ID is correct
- Verify you have permission to access the filter

**Rate limiting (429 errors)**
- Reduce `--page-size` for streaming exports
- Add delays between bulk operations
- Run large exports during off-peak hours
- Split large exports into smaller date ranges

**Export interrupted or taking too long**
- Use `streaming_export.py` with `--enable-checkpoint` for large exports
- Reduce fields with `--fields key,summary,status` to speed up
- Split into date ranges for very large projects

**JQL syntax errors**
- Use `python jql_validate.py "your query"` to get specific error messages
- Use `python jql_interactive.py` for guided query building
- Check field operators with `python jql_fields.py --filter "fieldname"`

**"Query history file not found"**
- History is stored in `~/.jira-skills/jql_history.json`
- First use of `jql_history.py --add` will create the file
- Check file permissions on the directory

### Debug Tips

1. **Test connectivity first**:
   ```bash
   python jql_search.py "project = PROJ" --max-results 1
   ```

2. **Validate JQL before running**:
   ```bash
   python jql_validate.py "your complex query here"
   ```

3. **Check available values**:
   ```bash
   python jql_suggest.py status
   python jql_suggest.py priority
   ```

4. **Use JSON output for scripting**:
   ```bash
   python jql_search.py "project = PROJ" --output json | jq '.issues[].key'
   ```

## Configuration

Uses shared configuration from `.claude/settings.json` and `.claude/settings.local.json`.
Requires JIRA credentials via environment variables or settings files.

## Best Practices

For comprehensive guidance on JQL query optimization, filter organization, and export strategies, see [Best Practices Guide](docs/BEST_PRACTICES.md).

## Related skills

- **jira-issue**: For creating and updating individual issues
- **jira-lifecycle**: For transitioning issues found in searches
- **jira-collaborate**: For bulk commenting on search results
- **jira-agile**: For sprint and board operations
- **jira-relationships**: For issue linking and dependencies
