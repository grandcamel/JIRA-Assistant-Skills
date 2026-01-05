---
name: "jira-developer-integration"
description: "Developer workflow integration for JIRA - Git branch names, commit parsing, PR descriptions. Use when generating branch names from issues, linking commits, or creating PR descriptions. Also use to troubleshoot Development Panel issues or automate CI/CD integration."
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# JIRA Developer Integration Skill

Developer workflow integration for JIRA including Git, CI/CD, and release automation.

**Quick Start:** [Get started in 10 minutes](docs/QUICK_START.md)

## When to Use This Skill

Use this skill when you need to:

**Starting Development:**
- Generate standardized Git branch names from JIRA issues
- Create feature, bugfix, or hotfix branches with consistent naming

**During Development:**
- Extract JIRA issue keys from commit messages
- Link Git commits to JIRA issues via comments
- Log time and transition issues from commits (Smart Commits)

**Code Review:**
- Generate PR descriptions from JIRA issue details
- Link Pull Requests (GitHub, GitLab, Bitbucket) to JIRA issues

**CI/CD Integration:**
- Track builds and deployments in JIRA
- Auto-transition issues based on PR/deployment events
- Generate release notes from JIRA versions

**Troubleshooting:**
- Debug why Development Panel shows empty
- Fix Smart Commits not working
- Resolve PR linking issues

**IMPORTANT:** Always use the `jira` CLI. Never run Python scripts directly.

## Learning Path

### Phase 1: Core Git Integration (30-45 min)

Learn to automate Git workflow integration. Start here if you're new to JIRA-Git integration.

| Script | Purpose |
|--------|---------|
| `create_branch_name.py` | Generate consistent branch names from issues |
| `parse_commit_issues.py` | Extract issue keys from commit messages |
| `link_commit.py` | Link commits to JIRA issues |
| `get_issue_commits.py` | Retrieve development information |

### Phase 2: Pull Request & CI/CD (45-60 min)

Integrate pull requests and deployment tracking. Prerequisites: Complete Phase 1 first.

| Script | Purpose |
|--------|---------|
| `link_pr.py` | Automatically link PRs to JIRA |
| `create_pr_description.py` | Generate PR descriptions from issues |

**Advanced:** See [CI/CD Integration Guide](docs/guides/ci-cd-integration.md) for pipeline setup.

### Recommended Starting Points

| Role | Start With |
|------|------------|
| Developer | Phase 1, try `create_branch_name.py` |
| Git Administrator | Phase 1, then Phase 2 |
| DevOps Engineer | Phase 2 CI/CD integration |
| Release Manager | Phase 2 deployment tracking |

## Scripts Overview

All scripts support `--help` for detailed usage. See [scripts/REFERENCE.md](scripts/REFERENCE.md) for complete options.

### Quick Examples

```bash
# Generate branch name with default prefix (feature)
jira dev branch-name PROJ-123

# Generate branch name with explicit prefix
jira dev branch-name PROJ-123 --prefix bugfix

# Auto-detect prefix from issue type (Bug -> bugfix, Story -> feature, etc.)
jira dev branch-name PROJ-123 --auto-prefix

# Output git checkout command directly
jira dev branch-name PROJ-123 --output git

# Extract issues from a single commit message
jira dev parse-commits "feat(PROJ-123): add login"

# Extract issues from git log via pipe
git log --oneline -10 | jira dev parse-commits --from-stdin

# Filter to specific project
jira dev parse-commits "Fix PROJ-123 and OTHER-456" --project PROJ

# Generate PR description with testing checklist
jira dev pr-description PROJ-123 --include-checklist

# Generate PR description with labels and components
jira dev pr-description PROJ-123 --include-labels --include-components

# Link PR to issue (--pr is required)
jira dev link-pr PROJ-123 --pr https://github.com/org/repo/pull/456

# Link PR with status and author
jira dev link-pr PROJ-123 --pr https://github.com/org/repo/pull/456 --status merged --author "Jane Doe"

# Link commit to issue (--commit is required)
jira dev link-commit PROJ-123 --commit abc123def --message "feat: add login" --repo https://github.com/org/repo

# Link commit with additional metadata
jira dev link-commit PROJ-123 --commit abc123def --author "John Doe" --branch feature/login

# Get commits linked to issue
jira dev get-commits PROJ-123

# Get commits with detailed information
jira dev get-commits PROJ-123 --detailed

# Get commits filtered by repository
jira dev get-commits PROJ-123 --repo "org/repo" --output table
```

## Configuration

Requires JIRA credentials via environment variables:

| Setting | Description |
|---------|-------------|
| `JIRA_SITE_URL` | Your JIRA instance URL |
| `JIRA_EMAIL` | Your JIRA email |
| `JIRA_API_TOKEN` | Your JIRA API token |

## Common Options

| Option | Description |
|--------|-------------|
| `--profile` | JIRA profile for multi-instance support |
| `--output, -o` | Output format varies by command (see below) |
| `--help` | Show detailed help and examples |

### Output Formats by Command

| Command | Available Formats |
|---------|------------------|
| `branch-name` | text, json, git |
| `parse-commits` | text, json, csv |
| `pr-description` | text, json |
| `link-commit` | text, json |
| `link-pr` | text, json |
| `get-commits` | text, json, table |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (validation, API, config) |
| 2 | Invalid arguments |

## Troubleshooting

See [Common Pitfalls Guide](docs/guides/common-pitfalls.md) for solutions to:
- Development Panel showing empty
- Smart Commits not working
- PR linking issues
- Branch name problems

## Advanced Topics

| Topic | Guide |
|-------|-------|
| Branch naming conventions | [Branch Naming](docs/guides/branch-naming.md) |
| Commit message formats | [Commit Messages](docs/guides/commit-messages.md) |
| Smart Commits | [Smart Commits](docs/guides/smart-commits.md) |
| PR workflows | [PR Workflows](docs/guides/pr-workflows.md) |
| Development Panel | [Development Panel](docs/guides/development-panel.md) |
| CI/CD integration | [CI/CD Integration](docs/guides/ci-cd-integration.md) |
| Automation rules | [Automation Rules](docs/guides/automation-rules.md) |
| Deployment tracking | [Deployment Tracking](docs/guides/deployment-tracking.md) |
| Release notes | [Release Notes](docs/guides/release-notes.md) |

For comprehensive guidance, see [Best Practices Guide](docs/BEST_PRACTICES.md).

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

## Related Skills

| Skill | Relationship |
|-------|-------------|
| jira-issue | Get issue details for branch names |
| jira-lifecycle | Auto-transition on PR merge |
| jira-collaborate | Commit linking uses comments |
| jira-search | Find issues for bulk operations |
| jira-bulk | Process multiple issues from commits |
