# Script Execution Guidelines

**IMPORTANT: Always verify command syntax before execution.**

Before running any JIRA script, check the syntax and available options:

```bash
# Always run --help first to verify syntax
python script_name.py --help
```

---

## Why This Matters

1. **Parameter validation** - Confirm required vs optional arguments
2. **Correct flags** - Verify exact flag names (e.g., `--issue-key` vs `--issue`)
3. **Value formats** - Check expected formats (dates, time strings, JQL)
4. **Avoid failures** - Prevent execution errors from incorrect syntax

---

## Execution Pattern

Follow this pattern for every script execution:

```bash
# Step 1: Check syntax first
python .claude/skills/jira-issue/scripts/create_issue.py --help

# Step 2: Execute with verified parameters
python .claude/skills/jira-issue/scripts/create_issue.py --project PROJ --type Bug --summary "Issue title"
```

---

## Common Parameter Patterns

| Pattern | Example | Notes |
|---------|---------|-------|
| Issue key | `PROJ-123` | Positional or `--issue-key` |
| Project | `--project PROJ` | 2-10 char uppercase |
| Profile | `--profile development` | JIRA instance to use |
| Dry run | `--dry-run` | Preview without changes |
| Output | `--output json` | json, table, or csv |

---

## Error Prevention

When a script fails:
1. Re-run with `--help` to verify exact syntax
2. Check if required parameters are missing
3. Validate parameter value formats
4. Verify `--profile` matches configured instance

---

## Script Locations by Skill

| Skill | Path | Primary Scripts |
|-------|------|-----------------|
| jira-issue | `.claude/skills/jira-issue/scripts/` | create_issue.py, get_issue.py, update_issue.py |
| jira-lifecycle | `.claude/skills/jira-lifecycle/scripts/` | transition_issue.py, assign_issue.py |
| jira-search | `.claude/skills/jira-search/scripts/` | jql_search.py, jql_validate.py |
| jira-collaborate | `.claude/skills/jira-collaborate/scripts/` | add_comment.py, upload_attachment.py |
| jira-agile | `.claude/skills/jira-agile/scripts/` | create_sprint.py, manage_backlog.py |
| jira-relationships | `.claude/skills/jira-relationships/scripts/` | link_issues.py, clone_issue.py |
| jira-time | `.claude/skills/jira-time/scripts/` | log_time.py, get_worklogs.py |
| jira-bulk | `.claude/skills/jira-bulk/scripts/` | bulk_transition.py, bulk_assign.py |
| jira-dev | `.claude/skills/jira-dev/scripts/` | generate_branch.py, parse_commits.py |
| jira-fields | `.claude/skills/jira-fields/scripts/` | discover_fields.py, get_agile_fields.py |
| jira-jsm | `.claude/skills/jira-jsm/scripts/` | create_request.py, manage_queue.py |
| jira-ops | `.claude/skills/jira-ops/scripts/` | warm_cache.py, clear_cache.py |

---

*See [CLAUDE.md](/CLAUDE.md) for comprehensive script development guidelines.*
