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

## Risk Levels

| Operation | Risk | Notes |
|-----------|------|-------|
| Generate branch name | `-` | Read-only, local output |
| Parse commits | `-` | Read-only, local analysis |
| Get commits | `-` | Read-only |
| Generate PR description | `-` | Read-only, local output |
| Link commit | `-` | Adds metadata, easily removed |
| Link PR | `-` | Adds metadata, easily removed |

**Risk Legend**: `-` Safe, read-only | `!` Caution, modifiable | `!!` Warning, destructive but recoverable | `!!!` Danger, irreversible

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

**IMPORTANT:** Always use the `jira-as` CLI. Never run Python scripts directly.

## Available Commands

All commands support `--help` for full documentation.

| Command | Description |
|---------|-------------|
| `jira-as dev branch-name` | Generate consistent branch names from issues |
| `jira-as dev parse-commits` | Extract issue keys from commit messages |
| `jira-as dev link-commit` | Link commits to JIRA issues |
| `jira-as dev get-commits` | Retrieve development information |
| `jira-as dev link-pr` | Automatically link PRs to JIRA |
| `jira-as dev pr-description` | Generate PR descriptions from issues |

### Recommended Starting Points

| Role | Start With |
|------|------------|
| Developer | `jira-as dev branch-name PROJ-123` |
| Git Administrator | Branch names, then PR integration |
| DevOps Engineer | CI/CD integration with `link-pr` and `link-commit` |
| Release Manager | Deployment tracking with `link-pr` |

**Advanced:** See [CI/CD Integration Guide](docs/guides/ci-cd-integration.md) for pipeline setup.

### Quick Examples

```bash
# Generate branch name with default prefix (feature)
jira-as dev branch-name PROJ-123

# Generate branch name with explicit prefix (-p is short for --prefix)
jira-as dev branch-name PROJ-123 -p bugfix
jira-as dev branch-name PROJ-123 --prefix bugfix

# Auto-detect prefix from issue type (Bug -> bugfix, Story -> feature, etc.)
jira-as dev branch-name PROJ-123 --auto-prefix

# Output git checkout command directly (-o is short for --output)
jira-as dev branch-name PROJ-123 -o git

# Extract issues from a single commit message
jira-as dev parse-commits "feat(PROJ-123): add login"

# Extract issues from git log via pipe
git log --oneline -10 | jira-as dev parse-commits --from-stdin

# Filter to specific project (-p is short for --project)
jira-as dev parse-commits "Fix PROJ-123 and OTHER-456" -p PROJ

# Generate PR description with testing checklist (-c is short for --include-checklist)
jira-as dev pr-description PROJ-123 -c
jira-as dev pr-description PROJ-123 --include-checklist

# Generate PR description with labels (-l is short for --include-labels)
jira-as dev pr-description PROJ-123 -l --include-components

# Generate PR description and copy to clipboard
jira-as dev pr-description PROJ-123 --copy

# Link PR to issue (-p is short for --pr)
jira-as dev link-pr PROJ-123 -p https://github.com/org/repo/pull/456

# Link PR with title (-t is short for --title)
jira-as dev link-pr PROJ-123 -p https://github.com/org/repo/pull/456 -t "Fix authentication bug"

# Link PR with status and author (-s, -a are short forms)
jira-as dev link-pr PROJ-123 -p https://github.com/org/repo/pull/456 -s merged -a "Jane Doe"

# Link commit to issue (-c is short for --commit, -m for --message, -r for --repo)
jira-as dev link-commit PROJ-123 -c abc123def -m "feat: add login" -r https://github.com/org/repo

# Link commit with additional metadata (-a for --author, -b for --branch)
jira-as dev link-commit PROJ-123 -c abc123def -a "John Doe" -b feature/login

# Get commits linked to issue
jira-as dev get-commits PROJ-123

# Get commits with detailed information
jira-as dev get-commits PROJ-123 --detailed

# Get commits filtered by repository (-o is short for --output)
jira-as dev get-commits PROJ-123 --repo "org/repo" -o table
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

## Related Skills

| Skill | Relationship |
|-------|-------------|
| jira-issue | Get issue details for branch names |
| jira-lifecycle | Auto-transition on PR merge |
| jira-collaborate | Commit linking uses comments |
| jira-search | Find issues for bulk operations |
| jira-bulk | Process multiple issues from commits |
