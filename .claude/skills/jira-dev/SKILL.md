---
name: "JIRA Developer Integration"
description: "Developer workflow integration for JIRA - Git branch names, commit parsing, PR descriptions. Use when generating branch names from issues, linking commits, or creating PR descriptions."
---

# JIRA Developer Integration Skill

Developer workflow integration for JIRA including Git, CI/CD, and release automation.

## When to use this skill

Use this skill when you need to:
- Generate standardized Git branch names from JIRA issues
- Extract JIRA issue keys from commit messages
- Link Git commits to JIRA issues via comments
- Retrieve commits linked to a JIRA issue via Development Information API
- Link Pull Requests (GitHub, GitLab, Bitbucket) to JIRA issues
- Generate PR descriptions from JIRA issue details
- Integrate developer workflows with JIRA tracking

## Phase 1: Git Integration

### create_branch_name.py

Generate standardized Git branch names from JIRA issues.

```bash
# Basic usage - creates feature/proj-123-fix-login-button
python create_branch_name.py PROJ-123

# Auto-detect prefix from issue type (Bug -> bugfix/, Story -> feature/)
python create_branch_name.py PROJ-123 --auto-prefix

# Custom prefix
python create_branch_name.py PROJ-123 --prefix bugfix

# Output as git command
python create_branch_name.py PROJ-123 --output git
# Output: git checkout -b feature/proj-123-fix-login-button

# Output as JSON
python create_branch_name.py PROJ-123 --output json
```

**Features:**
- Sanitizes special characters for valid git branch names
- Truncates long summaries while respecting word boundaries
- Auto-prefix based on issue type (Bug, Story, Task, etc.)
- Multiple output formats (text, json, git command)

### parse_commit_issues.py

Extract JIRA issue keys from commit messages.

```bash
# Parse single message
python parse_commit_issues.py "PROJ-123: Fix login bug"
# Output: PROJ-123

# Parse multiple issues
python parse_commit_issues.py "Fix PROJ-123 and PROJ-456"
# Output:
# PROJ-123
# PROJ-456

# Read from git log
git log --oneline -10 | python parse_commit_issues.py --from-stdin

# Filter by project
python parse_commit_issues.py "PROJ-123 OTHER-456" --project PROJ
# Output: PROJ-123

# JSON output
python parse_commit_issues.py "Fixes PROJ-123" --output json
```

**Supported Formats:**
- Direct: `PROJ-123`
- Prefixed: `Fixes PROJ-123`, `Closes PROJ-123`
- Conventional: `feat(PROJ-123): add feature`
- Brackets: `[PROJ-123] Fix bug`

### link_commit.py

Link Git commits to JIRA issues via comments.

```bash
# Link commit to issue
python link_commit.py PROJ-123 --commit abc123def456 --repo https://github.com/org/repo

# With commit message
python link_commit.py PROJ-123 --commit abc123 --message "Fixed authentication"

# Auto-extract issues from message and link
python link_commit.py --from-message "PROJ-123: Fix login bug" --commit abc123
```

**Repository Support:**
- GitHub: Creates `github.com/org/repo/commit/sha` links
- GitLab: Creates `gitlab.com/org/repo/-/commit/sha` links
- Bitbucket: Creates `bitbucket.org/org/repo/commits/sha` links

### get_issue_commits.py

Get commits linked to a JIRA issue via Development Information API.

```bash
# Get commits for issue
python get_issue_commits.py PROJ-123

# With details (message, author)
python get_issue_commits.py PROJ-123 --detailed

# Filter by repository
python get_issue_commits.py PROJ-123 --repo "org/repo"

# JSON output
python get_issue_commits.py PROJ-123 --output json
```

**Note:** Requires JIRA Development Information integration (GitHub for JIRA, etc.)

## Phase 2: PR Management

### link_pr.py

Link Pull Requests to JIRA issues.

```bash
# Link GitHub PR
python link_pr.py PROJ-123 --pr https://github.com/org/repo/pull/456

# Link GitLab Merge Request
python link_pr.py PROJ-123 --pr https://gitlab.com/org/repo/-/merge_requests/789

# Link Bitbucket PR
python link_pr.py PROJ-123 --pr https://bitbucket.org/org/repo/pull-requests/101

# With status and title
python link_pr.py PROJ-123 --pr https://github.com/org/repo/pull/456 --status merged --title "Fix login"

# JSON output
python link_pr.py PROJ-123 --pr https://github.com/org/repo/pull/456 --output json
```

**Supported Providers:**
- GitHub (pull requests)
- GitLab (merge requests)
- Bitbucket (pull requests)

### create_pr_description.py

Generate PR descriptions from JIRA issue details.

```bash
# Basic PR description
python create_pr_description.py PROJ-123

# With testing checklist
python create_pr_description.py PROJ-123 --include-checklist

# Include labels
python create_pr_description.py PROJ-123 --include-labels

# Include components
python create_pr_description.py PROJ-123 --include-components

# Copy to clipboard (requires pyperclip)
python create_pr_description.py PROJ-123 --copy

# JSON output
python create_pr_description.py PROJ-123 --output json
```

**Output Includes:**
- Summary from JIRA issue
- Link to JIRA issue
- Issue type and priority
- Description excerpt
- Acceptance criteria (auto-extracted)
- Optional: Labels, components, testing checklist

**Example Output:**
```markdown
## Summary

Fix login button not responding

## JIRA Issue

[PROJ-123](https://jira.example.com/browse/PROJ-123)

**Type:** Bug
**Priority:** High

## Description

The login button does not respond to clicks on mobile devices...

## Acceptance Criteria

- [ ] Login button responds to touch on iOS
- [ ] Login button responds to touch on Android

## Testing Checklist

- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] No regressions introduced
```

## Configuration

Uses shared configuration from `.claude/settings.json` and `.claude/settings.local.json`.

Required environment variables or config:
- `JIRA_SITE_URL`: Your JIRA instance URL
- `JIRA_EMAIL`: Your JIRA email
- `JIRA_API_TOKEN`: Your JIRA API token

## Issue Type Prefixes

| Issue Type | Branch Prefix |
|------------|--------------|
| Bug, Defect | `bugfix/` |
| Story, Feature, Improvement | `feature/` |
| Task, Sub-task | `task/` |
| Epic | `epic/` |
| Spike, Research | `spike/` |
| Chore, Maintenance | `chore/` |
| Documentation | `docs/` |

## Common Options

All scripts support these common options:

| Option | Description |
|--------|-------------|
| `--profile` | JIRA profile for multi-instance support |
| `--output` | Output format: `text` (default), `json`, or `git` (branch scripts only) |
| `--help` | Show detailed help and examples |

Script-specific options:

| Script | Key Options |
|--------|-------------|
| `create_branch_name.py` | `--prefix`, `--auto-prefix`, `--max-length` |
| `parse_commit_issues.py` | `--from-stdin`, `--project`, `--unique` |
| `link_commit.py` | `--commit`, `--repo`, `--message`, `--from-message` |
| `get_issue_commits.py` | `--detailed`, `--repo` |
| `link_pr.py` | `--pr`, `--status`, `--title` |
| `create_pr_description.py` | `--include-checklist`, `--include-labels`, `--include-components`, `--copy` |

## Exit Codes

All scripts use the following exit codes:

| Exit Code | Meaning |
|-----------|---------|
| 0 | Operation completed successfully |
| 1 | Error occurred (validation, API, or configuration error) |
| 2 | Invalid arguments or usage error |

## Troubleshooting

### Development Information API Issues

**Problem:** `get_issue_commits.py` returns empty results

**Solutions:**
1. Verify your JIRA instance has a Development Tool integration installed (e.g., GitHub for JIRA, Bitbucket for JIRA)
2. Check that commits include JIRA issue keys in commit messages
3. Ensure the integration has synced recent commits (may take a few minutes)
4. Verify you have permission to view development information on the issue

### Branch Name Generation Issues

**Problem:** Branch name is truncated unexpectedly

**Solution:** Use `--max-length` to increase the limit (default is 50 characters):
```bash
python create_branch_name.py PROJ-123 --max-length 80
```

**Problem:** Issue type not recognized for auto-prefix

**Solution:** Use custom prefix instead:
```bash
python create_branch_name.py PROJ-123 --prefix custom-type
```

### Commit Linking Issues

**Problem:** Comment not appearing on JIRA issue

**Solutions:**
1. Verify JIRA API credentials have comment permission
2. Check the issue key is valid and accessible
3. Ensure the repository URL format is correct for your provider

### PR Link Issues

**Problem:** PR link not recognized by JIRA

**Solutions:**
1. Verify the PR URL format matches supported providers
2. Check that JIRA has the corresponding integration installed
3. For GitLab, use the correct merge request URL format (`/-/merge_requests/`)

### Common API Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid or expired API token | Regenerate token at id.atlassian.com |
| 403 Forbidden | Insufficient permissions | Request access from JIRA admin |
| 404 Not Found | Issue key doesn't exist | Verify issue key format and project access |
| 429 Rate Limited | Too many API requests | Wait and retry; scripts auto-retry with backoff |

## Scripts Summary

| Phase | Script | Purpose | Tests |
|-------|--------|---------|-------|
| 1 | create_branch_name.py | Generate branch names | 10 |
| 1 | parse_commit_issues.py | Extract issue keys | 8 |
| 1 | link_commit.py | Link commits to issues | 6 |
| 1 | get_issue_commits.py | Get linked commits | 5 |
| 2 | link_pr.py | Link PRs to issues | 7 |
| 2 | create_pr_description.py | Generate PR descriptions | 6 |
| **Total** | **6 scripts** | | **42 tests** |

## Best Practices

For comprehensive guidance on Git integration patterns, branch naming conventions, and PR workflows, see [Best Practices Guide](docs/BEST_PRACTICES.md).

## Related Skills

- **jira-issue**: Core CRUD operations on issues (get issue details for branch names)
- **jira-lifecycle**: Workflow transitions (auto-transition on PR merge)
- **jira-collaborate**: Comments and attachments (commit linking uses comments)
- **jira-search**: JQL queries to find issues for bulk operations
- **jira-bulk**: Bulk operations for processing multiple issues from commits
