# JIRA Search Troubleshooting Guide

Comprehensive troubleshooting for jira-search skill issues.

---

## Quick Diagnostics

Run these commands to identify common issues:

```bash
# 1. Test basic connectivity
python jql_search.py "project = PROJ" --max-results 1

# 2. Validate JQL syntax
python jql_validate.py "your query here"

# 3. Check available fields
python jql_fields.py --filter "fieldname"

# 4. Get field value suggestions
python jql_suggest.py status
```

---

## Authentication Errors

### 401 Unauthorized

**Symptoms:**
- "Authentication failed"
- "401 Unauthorized" response

**Causes:**
1. Invalid or expired API token
2. Wrong email address
3. Incorrect site URL

**Solutions:**

```bash
# Check your environment variables
echo $JIRA_API_TOKEN
echo $JIRA_EMAIL
echo $JIRA_SITE_URL
```

1. Regenerate token at https://id.atlassian.com/manage-profile/security/api-tokens
2. Verify `JIRA_EMAIL` matches the email for your API token
3. Ensure `JIRA_SITE_URL` is correct format: `https://company.atlassian.net`

### 403 Forbidden

**Symptoms:**
- "You don't have permission"
- "403 Forbidden" response

**Causes:**
1. No access to the project
2. API access disabled for your account
3. IP restrictions

**Solutions:**
1. Request project access from your JIRA administrator
2. Check if your account has API access enabled
3. Verify you are on an allowed network

---

## Search Result Issues

### "No issues found"

**Symptoms:**
- Empty search results when you expect matches

**Diagnostic Steps:**

```bash
# 1. Validate the query syntax
python jql_validate.py "your query"

# 2. Check field names exist
python jql_fields.py --filter "fieldname"

# 3. Verify field values are correct
python jql_suggest.py status

# 4. Simplify the query to isolate the problem
python jql_search.py "project = PROJ" --max-results 1
```

**Common Causes:**

| Issue | Wrong | Correct |
|-------|-------|---------|
| Unquoted spaces | `status = In Progress` | `status = "In Progress"` |
| Wrong operator | `status = Open` (empty field) | `status IS EMPTY` |
| Case sensitivity | `Status = Open` | `status = Open` |
| Wrong field name | `issuetype = Bug` | `type = Bug` |

### Too Many Results

**Symptoms:**
- Query returns thousands of issues
- Slow response times
- Timeouts

**Solutions:**

```bash
# Add project filter
python jql_search.py "project = PROJ AND status = Open"

# Limit results
python jql_search.py "JQL" --max-results 100

# Add date filter
python jql_search.py "JQL AND created >= -30d"
```

---

## JQL Syntax Errors

### "Field 'X' does not exist"

```bash
# List available fields
python jql_fields.py

# Search for similar field name
python jql_fields.py --filter "partial-name"
```

**Common Field Name Issues:**

| Looking For | Might Be Called |
|-------------|-----------------|
| Issue Type | `type` or `issuetype` |
| Story Points | `"Story Points"` (quoted, custom field) |
| Epic Link | `"Epic Link"` (quoted, custom field) |
| Sprint | `sprint` |

### "Value 'X' does not exist"

```bash
# Get valid values for a field
python jql_suggest.py status
python jql_suggest.py priority
python jql_suggest.py project
```

### "Operator not supported"

Different fields support different operators:

| Field Type | Supported Operators |
|------------|---------------------|
| Text | `~`, `!~`, `~=` |
| Select/Status | `=`, `!=`, `IN`, `NOT IN` |
| Date | `=`, `!=`, `>`, `>=`, `<`, `<=` |
| User | `=`, `!=`, `IS`, `IS NOT`, `IN`, `WAS` |

```bash
# Check operators for a field
python jql_fields.py --filter "fieldname"
```

---

## Filter Errors

### "Filter not found"

```bash
# List your filters
python get_filters.py --mine

# Search for filter by name
python get_filters.py --search "filter-name"
```

**Causes:**
1. Wrong filter ID
2. Filter was deleted
3. No permission to access filter

### "Cannot share filter"

**Causes:**
1. Not the filter owner
2. Target project/group does not exist
3. Insufficient permissions

```bash
# Check filter ownership
python get_filters.py --mine

# Verify project exists
python jql_search.py "project = PROJ" --max-results 1
```

---

## Export Issues

### Export Taking Too Long

```bash
# Use streaming export for large datasets
python streaming_export.py "JQL" --output report.csv --enable-checkpoint

# Limit fields to reduce data size
python export_results.py "JQL" --output report.csv --fields key,summary,status

# Split by date ranges
python export_results.py "JQL AND created >= 2025-01-01 AND created < 2025-04-01" --output q1.csv
```

### Export Interrupted

```bash
# List pending exports
python streaming_export.py --list-checkpoints

# Resume interrupted export
python streaming_export.py --resume export-20251226-143022
```

### Rate Limiting (429 Errors)

**Solutions:**

1. Reduce page size:
   ```bash
   python streaming_export.py "JQL" --output report.csv --page-size 50
   ```

2. Run during off-peak hours

3. Split into smaller exports:
   ```bash
   python export_results.py "JQL AND created >= -7d" --output week1.csv
   python export_results.py "JQL AND created >= -14d AND created < -7d" --output week2.csv
   ```

---

## Query History Issues

### "Query history file not found"

**Cause:** First use of history feature

**Solution:**
```bash
# Create first entry
python jql_history.py --add "project = PROJ" --name my-first-query

# History is stored at ~/.jira-skills/jql_history.json
```

### History File Corrupted

```bash
# Export to backup
python jql_history.py --export backup.json

# Clear and reimport
python jql_history.py --clear
python jql_history.py --import backup.json
```

---

## Performance Issues

### Slow Queries

**Optimization Steps:**

1. Always include `project` clause:
   ```jql
   project = PROJ AND status = Open
   ```

2. Use indexed fields first:
   - `project`, `status`, `assignee`, `reporter`
   - `type`, `priority`, `created`, `updated`

3. Avoid negations:
   ```jql
   # Slow
   status != Done AND status != Closed

   # Faster
   status IN (Open, "In Progress", "To Do")
   ```

4. Limit text searches:
   ```jql
   # Slow - searches all text
   text ~ "error"

   # Faster - specific field
   summary ~ "error"
   ```

5. Test incrementally:
   ```bash
   # Start simple
   python jql_search.py "project = PROJ"

   # Add clauses one at a time
   python jql_search.py "project = PROJ AND status = Open"
   ```

### Memory Issues with Large Exports

```bash
# Use JSON Lines format (memory efficient)
python streaming_export.py "JQL" --output data.jsonl --format jsonl

# Process with streaming tools
cat data.jsonl | jq -r '.key'
```

---

## Debug Techniques

### Enable Verbose Output

```bash
# Use JSON output for detailed response
python jql_search.py "JQL" --output json | jq .
```

### Validate Before Execute

```bash
# Always validate complex queries first
python jql_validate.py "complex JQL query here"
```

### Test Incrementally

```bash
# Start with minimal query
python jql_search.py "project = PROJ" --max-results 1

# Add one clause at a time
python jql_search.py "project = PROJ AND status = Open" --max-results 1
python jql_search.py "project = PROJ AND status = Open AND type = Bug" --max-results 1
```

### Check Field Availability

```bash
# List all searchable fields
python jql_fields.py

# Check specific field
python jql_fields.py --filter "story points"

# Get valid values
python jql_suggest.py status
```

---

## Error Code Reference

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Success | None needed |
| 1 | General error | Check error message |
| 2 | Invalid arguments | Check `--help` for usage |
| 130 | User interrupted | Re-run if needed |

---

## Getting Help

### Built-in Help

```bash
# All scripts support --help
python jql_search.py --help
python export_results.py --help
python create_filter.py --help
```

### Documentation

- [QUICK_START.md](../docs/QUICK_START.md) - Getting started guide
- [SCRIPT_REFERENCE.md](../docs/SCRIPT_REFERENCE.md) - All scripts with examples
- [jql_reference.md](jql_reference.md) - JQL syntax reference
- [BEST_PRACTICES.md](BEST_PRACTICES.md) - Expert guidance

### Official Resources

- [Atlassian JQL Guide](https://www.atlassian.com/software/jira/guides/jql/overview)
- [JQL Operators Reference](https://support.atlassian.com/jira-software-cloud/docs/jql-operators/)
