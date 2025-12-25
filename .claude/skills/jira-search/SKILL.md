# jira-search

Query and discovery operations for JIRA issues using JQL (JIRA Query Language).

## When to use this skill

Use this skill when you need to:
- Search for issues using JQL queries
- Find issues by project, status, assignee, or other criteria
- List saved filters
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

2. **Saved Filters**: Work with saved JIRA filters
   - List accessible filters
   - Execute filters by ID or name
   - Share filter results with team

3. **Export Results**: Export search results
   - Export to CSV format
   - Export to JSON format
   - Select specific fields to export
   - Format for reporting or analysis

4. **Bulk Updates**: Update multiple issues at once
   - Apply changes to search results
   - Bulk assign, label, or prioritize
   - Mass transitions (with caution)

## Available scripts

- `jql_search.py` - Execute JQL queries
- `get_filters.py` - List saved filters
- `run_filter.py` - Execute a saved filter
- `export_results.py` - Export search results to file
- `bulk_update.py` - Bulk update issues from search

## Templates

Pre-configured JQL templates for common queries:
- `jql_templates.json` - Common search patterns

## Examples

```bash
# Search for open bugs
python jql_search.py "project = PROJ AND type = Bug AND status = Open"

# Find my issues
python jql_search.py "assignee = currentUser() AND status != Done"

# Search with specific fields
python jql_search.py "project = PROJ" --fields key,summary,status

# List saved filters
python get_filters.py

# Run a saved filter
python run_filter.py --name "My Open Issues"

# Export to CSV
python export_results.py "project = PROJ AND created >= -7d" --output report.csv

# Bulk update labels
python bulk_update.py "project = PROJ AND labels = old-label" --add-labels "new-label"
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

See `references/jql_reference.md` for comprehensive JQL documentation.

## Configuration

Uses shared configuration from `.claude/settings.json` and `.claude/settings.local.json`.
Requires JIRA credentials via environment variables or settings files.

## Related skills

- **jira-issue**: For creating and updating individual issues
- **jira-lifecycle**: For transitioning issues found in searches
- **jira-collaborate**: For bulk commenting on search results
