# Quick Start: Developer Workflow Integration

Get started with jira-dev in 10 minutes.

## Prerequisites

- Python 3.8+ with JIRA credentials configured
- Git repository with JIRA integration enabled

## 1. Generate Your First Branch Name (2 min)

```bash
# Generate branch name from JIRA issue
python create_branch_name.py PROJ-123
# Output: feature/proj-123-fix-login-button

# Auto-detect prefix from issue type (Bug -> bugfix/, Story -> feature/)
python create_branch_name.py PROJ-123 --auto-prefix

# Create and checkout branch in one command
git checkout -b $(python create_branch_name.py PROJ-123 --output git | cut -d' ' -f3)
```

## 2. Extract Issues from Commits (2 min)

```bash
# Parse issue keys from commit message
python parse_commit_issues.py "PROJ-123: Fix login bug"
# Output: PROJ-123

# Extract from git log
git log --oneline -10 | python parse_commit_issues.py --from-stdin
```

## 3. Link a Commit to JIRA (2 min)

```bash
# Link commit to issue via comment
python link_commit.py PROJ-123 --commit abc123def456 --repo https://github.com/org/repo
```

## 4. Create PR Description (3 min)

```bash
# Generate PR description from JIRA issue
python create_pr_description.py PROJ-123

# Include testing checklist
python create_pr_description.py PROJ-123 --include-checklist

# Copy to clipboard (requires pyperclip)
python create_pr_description.py PROJ-123 --copy
```

## 5. Link Pull Request to JIRA (1 min)

```bash
# Link GitHub PR
python link_pr.py PROJ-123 --pr https://github.com/org/repo/pull/456

# Link GitLab MR
python link_pr.py PROJ-123 --pr https://gitlab.com/org/repo/-/merge_requests/789
```

## What's Next?

| Goal | Resource |
|------|----------|
| Learn all scripts | Run `python <script>.py --help` |
| Phase 1: Git Integration | Branch names, commit parsing, linking |
| Phase 2: PR Management | PR descriptions, PR linking |
| Advanced workflows | [Best Practices Guide](BEST_PRACTICES.md) |
| CI/CD integration | [CI/CD Guide](guides/ci-cd-integration.md) |
| Troubleshooting | [Common Pitfalls](guides/common-pitfalls.md) |

## Common Issues

| Problem | Solution |
|---------|----------|
| Branch name too long | Use `--max-length 80` |
| Issue type not recognized | Use `--prefix custom-type` |
| Development panel empty | Ensure Git email matches JIRA user |
| Smart commits not working | Issue key must be UPPERCASE: `PROJ-123` |

See [SKILL.md](../SKILL.md) for complete documentation.
