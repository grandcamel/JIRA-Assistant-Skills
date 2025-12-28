# Troubleshooting Guide

Common issues and solutions for jira-agile operations.

## Field-Related Issues

### "Epic Link field not found"

**Cause:** Custom field IDs vary by JIRA instance.

**Solutions:**
1. Use jira-fields skill to discover correct field ID:
   ```bash
   python get_agile_fields.py
   ```
2. Check your instance's epic link field ID
3. Update field configuration (see [Field Reference](FIELD_REFERENCE.md))
4. Direct API check: `https://your-domain.atlassian.net/rest/api/3/field`

### "Issue type 'Epic' not found"

**Cause:** Project doesn't have Epic issue type enabled.

**Solutions:**
1. Check project settings: Administration > Projects > [Project] > Issue Types
2. Add Epic issue type to project scheme
3. Some project templates don't include Epics by default

### Story points not showing

**Cause:** Story Points field not configured for project.

**Solutions:**
1. Use jira-fields skill to discover the correct field ID
2. Check STORY_POINTS_FIELD constant matches your field ID
3. Verify the field is on your project's screens
4. Check field configuration in JIRA admin

## Hierarchy Issues

### "Subtask cannot have subtasks"

**Cause:** JIRA enforces a one-level hierarchy for subtasks.

**Solutions:**
1. Use epics for multi-level organization instead
2. Consider using issue links (jira-relationships skill) for complex dependencies
3. Restructure work breakdown to use parent stories with subtasks

## Board and Sprint Issues

### "Board not found" or "Sprint not found"

**Cause:** Invalid ID or permission issue.

**Solutions:**
1. Verify the board/sprint ID is correct
2. Ensure you have permission to access the board
3. Check that the board is a Scrum board (Kanban boards don't have sprints)
4. API check: `https://your-domain.atlassian.net/rest/agile/1.0/board`

## Permission Issues

### Permission errors on bulk operations

**Cause:** Insufficient permissions on target issues.

**Solutions:**
1. Use `--dry-run` first to identify issues you cannot modify
2. Check project permissions and issue security levels
3. Verify you have "Edit Issues" permission
4. For sprints: Check "Manage Sprints" permission

## API Issues

### API rate limiting (429 errors)

**Cause:** Too many requests in short time period.

**Solutions:**
1. The client automatically retries with exponential backoff
2. For very large bulk operations, split into smaller batches
3. Use JQL queries with `--dry-run` to estimate operation size first
4. Add delays between batch operations

## Quick Diagnostic Commands

```bash
# Test basic connectivity
python get_epic.py EXISTING-EPIC-KEY

# Check board access
python get_backlog.py --board BOARD-ID --max-results 1

# Verify sprint access
python get_sprint.py SPRINT-ID

# Discover field IDs
python get_agile_fields.py
```

## Getting Help

1. Check script help: `python SCRIPT.py --help`
2. Review [Field Reference](FIELD_REFERENCE.md) for field configuration
3. See [Best Practices](BEST_PRACTICES.md) for workflow guidance
4. Check JIRA Cloud status: https://status.atlassian.com/
