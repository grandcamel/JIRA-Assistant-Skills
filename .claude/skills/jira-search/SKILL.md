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

3. **Saved Filters**: Full CRUD operations on saved filters
   - Create new filters from JQL
   - List your filters and favourites
   - Update filter name, JQL, or description
   - Delete filters you own
   - Manage favourite filters

4. **Filter Sharing**: Share filters with teams
   - Share with project members
   - Share with specific project roles
   - Share with groups
   - Share with individual users
   - Share globally (all authenticated users)

5. **Filter Subscriptions**: View email subscriptions
   - List users subscribed to a filter
   - View subscription details

6. **Export Results**: Export search results
   - Export to CSV format
   - Export to JSON format
   - Select specific fields to export
   - Format for reporting or analysis
   - Streaming export for large result sets

7. **Bulk Updates**: Update multiple issues at once
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

### Search
- `jql_search.py` - Execute JQL queries

### Saved Filters
- `create_filter.py` - Create a new saved filter
- `get_filters.py` - List saved filters (my filters, favourites, search)
- `update_filter.py` - Update filter properties
- `delete_filter.py` - Delete a saved filter
- `favourite_filter.py` - Add/remove filter from favourites

### Filter Sharing & Subscriptions
- `share_filter.py` - Manage filter sharing permissions
- `filter_subscriptions.py` - View filter subscriptions

### Export & Bulk Operations
- `export_results.py` - Export search results to file
- `bulk_update.py` - Bulk update issues from search

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

## Streaming Export for Large Data Sets

When exporting large numbers of issues (>1000), the export_results.py script automatically handles pagination to fetch all results efficiently.

### How Streaming Export Works

1. **Automatic Pagination**: Results are fetched in batches (default 100 issues per request)
2. **Memory Efficient**: Issues are written to file as they're fetched, not held in memory
3. **Progress Tracking**: Shows progress for large exports
4. **Resumable**: If interrupted, simply re-run the export

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
| > 5000 | 2+ minutes | Consider exporting in date ranges |

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
key,summary,status,priority,issuetype,assignee,created,updated
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

## Configuration

Uses shared configuration from `.claude/settings.json` and `.claude/settings.local.json`.
Requires JIRA credentials via environment variables or settings files.

## Related skills

- **jira-issue**: For creating and updating individual issues
- **jira-lifecycle**: For transitioning issues found in searches
- **jira-collaborate**: For bulk commenting on search results
- **jira-agile**: For sprint and board operations
- **jira-relationships**: For issue linking and dependencies
