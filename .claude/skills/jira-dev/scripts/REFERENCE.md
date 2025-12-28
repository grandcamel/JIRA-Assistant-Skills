# Script Reference Card

Quick reference for all jira-dev scripts. Run `python <script>.py --help` for detailed usage.

## Phase 1: Git Integration

| Script | Purpose | Basic Usage |
|--------|---------|-------------|
| `create_branch_name.py` | Generate Git branch names | `python create_branch_name.py PROJ-123` |
| `parse_commit_issues.py` | Extract issue keys from commits | `python parse_commit_issues.py "message"` |
| `link_commit.py` | Link commits to JIRA issues | `python link_commit.py PROJ-123 --commit SHA` |
| `get_issue_commits.py` | Get commits linked to issue | `python get_issue_commits.py PROJ-123` |

## Phase 2: PR Management

| Script | Purpose | Basic Usage |
|--------|---------|-------------|
| `link_pr.py` | Link PRs to JIRA issues | `python link_pr.py PROJ-123 --pr URL` |
| `create_pr_description.py` | Generate PR descriptions | `python create_pr_description.py PROJ-123` |

## Key Options by Script

### create_branch_name.py
| Option | Description |
|--------|-------------|
| `--auto-prefix` | Auto-detect prefix from issue type |
| `--prefix TYPE` | Use custom prefix (feature, bugfix, hotfix) |
| `--max-length N` | Maximum branch name length (default: 50) |
| `--output FORMAT` | Output: text, json, git |

### parse_commit_issues.py
| Option | Description |
|--------|-------------|
| `--from-stdin` | Read from stdin (pipe git log) |
| `--project KEY` | Filter by project key |
| `--unique` | Return unique keys only |
| `--output FORMAT` | Output: text, json |

### link_commit.py
| Option | Description |
|--------|-------------|
| `--commit SHA` | Commit SHA to link |
| `--repo URL` | Repository URL |
| `--message TEXT` | Commit message |
| `--from-message` | Extract issues from message |

### get_issue_commits.py
| Option | Description |
|--------|-------------|
| `--detailed` | Include message and author |
| `--repo FILTER` | Filter by repository |
| `--output FORMAT` | Output: text, json |

### link_pr.py
| Option | Description |
|--------|-------------|
| `--pr URL` | Pull request URL |
| `--status STATUS` | PR status (open, merged, declined) |
| `--title TEXT` | PR title |
| `--output FORMAT` | Output: text, json |

### create_pr_description.py
| Option | Description |
|--------|-------------|
| `--include-checklist` | Add testing checklist |
| `--include-labels` | Include issue labels |
| `--include-components` | Include components |
| `--copy` | Copy to clipboard |
| `--output FORMAT` | Output: text, json |

## Common Options (All Scripts)

| Option | Description |
|--------|-------------|
| `--profile NAME` | JIRA profile for multi-instance |
| `--output FORMAT` | Output format: text (default), json |
| `--help` | Show detailed help |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (validation, API, config) |
| 2 | Invalid arguments |

## Issue Type Prefixes

| Issue Type | Branch Prefix |
|------------|--------------|
| Bug, Defect | `bugfix/` |
| Story, Feature | `feature/` |
| Task, Sub-task | `task/` |
| Epic | `epic/` |
| Spike, Research | `spike/` |
| Chore | `chore/` |
| Documentation | `docs/` |
