# JIRA Search Quick Start

Get started with JQL search in 5 minutes.

---

## Your First Search

### Step 1: Verify Setup

```bash
# Test connectivity with a simple search
python jql_search.py "project = PROJ" --max-results 1
```

If this works, you are ready to search.

### Step 2: Find Your Issues

```bash
# Find all issues assigned to you
python jql_search.py "assignee = currentUser() AND status != Done"
```

### Step 3: Search by Criteria

```bash
# Find open bugs in a project
python jql_search.py "project = PROJ AND type = Bug AND status = Open"

# Find high priority work
python jql_search.py "priority IN (Highest, High) AND status != Done"

# Find issues created this week
python jql_search.py "created >= startOfWeek()"
```

---

## Common Search Patterns

| Goal | JQL Query | Script Command |
|------|-----------|----------------|
| My work | `assignee = currentUser() AND status != Done` | `jql_search.py "..."` |
| Team bugs | `assignee IN membersOf("team") AND type = Bug` | `jql_search.py "..."` |
| Overdue | `duedate < now() AND status != Done` | `jql_search.py "..."` |
| Created today | `created >= startOfDay()` | `jql_search.py "..."` |
| Unassigned | `assignee IS EMPTY AND status = Open` | `jql_search.py "..."` |

---

## 5 Most Common Scripts

| Script | Purpose | Example |
|--------|---------|---------|
| `jql_search.py` | Execute JQL queries | `python jql_search.py "project = PROJ"` |
| `export_results.py` | Export to CSV/JSON | `python export_results.py "project = PROJ" -o report.csv` |
| `create_filter.py` | Save a reusable filter | `python create_filter.py "My Filter" "assignee = currentUser()"` |
| `jql_validate.py` | Check JQL syntax | `python jql_validate.py "your query"` |
| `run_filter.py` | Run a saved filter | `python run_filter.py --name "Sprint Issues"` |

---

## Quick Troubleshooting

**"No issues found"**
```bash
# Validate your query syntax
python jql_validate.py "your query here"
```

**"401 Unauthorized"**
- Check your API token at https://id.atlassian.com/manage-profile/security/api-tokens
- Verify `JIRA_EMAIL` matches your token's email

**"Field not found"**
```bash
# List available fields
python jql_fields.py --filter "fieldname"
```

**"Query too slow"**
- Add `project = PROJ` to limit scope
- Use `--fields key,summary,status` to limit returned data

---

## Next Steps

### Learn JQL Syntax
- See [references/jql_reference.md](../references/jql_reference.md) for operators and functions
- See [references/search_examples.md](../references/search_examples.md) for query patterns

### Save and Share Searches
1. Create a filter: `python create_filter.py "Filter Name" "JQL query" --favourite`
2. Share with team: `python share_filter.py FILTER_ID --project PROJ`
3. Run later: `python run_filter.py --name "Filter Name"`

### Export Data
- Small exports: `python export_results.py "query" --output report.csv`
- Large exports (>5000): `python streaming_export.py "query" --output report.csv --enable-checkpoint`

### Build Complex Queries
```bash
# Interactive query builder
python jql_interactive.py

# Get field suggestions
python jql_suggest.py status
```

---

## Quick Reference

```bash
# Essential commands
python jql_search.py "JQL"              # Search
python jql_validate.py "JQL"            # Validate
python export_results.py "JQL" -o FILE  # Export
python create_filter.py NAME "JQL"      # Save filter
python run_filter.py --name NAME        # Run filter
```

For complete documentation, see:
- [SKILL.md](../SKILL.md) - Full capabilities overview
- [SCRIPT_REFERENCE.md](SCRIPT_REFERENCE.md) - All scripts with examples
- [references/BEST_PRACTICES.md](../references/BEST_PRACTICES.md) - Expert guide
