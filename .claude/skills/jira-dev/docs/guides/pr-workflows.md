# Pull Request Best Practices

**Read time:** 5 minutes

## PR Title Format

Include the JIRA issue key for automatic linking:

```
PROJ-123: Add user authentication
[PROJ-456] Fix memory leak in cache
feat(api): PROJ-789 implement rate limiting
```

## Generate PR Description from JIRA

```bash
# Basic description
python create_pr_description.py PROJ-123

# With testing checklist
python create_pr_description.py PROJ-123 --include-checklist

# Include labels and components
python create_pr_description.py PROJ-123 --include-labels --include-components

# Copy to clipboard
python create_pr_description.py PROJ-123 --copy
```

## Standard PR Template

```markdown
## Summary

[Brief description of changes]

## JIRA Issue

[PROJ-123](https://your-company.atlassian.net/browse/PROJ-123)

**Type:** [Bug/Story/Task]
**Priority:** [High/Medium/Low]

## Changes Made

- [Key change 1]
- [Key change 2]

## Acceptance Criteria

- [ ] [Criterion from JIRA]

## Testing Checklist

- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed
```

## PR Linking Strategies

### 1. Automatic Linking (Recommended)

Use JIRA issue key in branch name:
```bash
git checkout -b feature/PROJ-123-user-auth
# PR from this branch auto-links to PROJ-123
```

### 2. Manual Linking

```bash
# Link PR after creation
python link_pr.py PROJ-123 --pr https://github.com/org/repo/pull/456

# With status
python link_pr.py PROJ-123 --pr URL --status open --title "Add auth"
```

### 3. Smart Commits in PR Description

```markdown
Fixes PROJ-123
Closes PROJ-456
Resolves PROJ-789
```

## Supported Providers

| Provider | URL Format |
|----------|------------|
| GitHub | `https://github.com/org/repo/pull/123` |
| GitLab | `https://gitlab.com/org/repo/-/merge_requests/123` |
| Bitbucket | `https://bitbucket.org/org/repo/pull-requests/123` |

## Review Checklist

**Before Creating PR:**
- [ ] Branch includes JIRA issue key
- [ ] Commits reference JIRA issue
- [ ] All tests pass locally
- [ ] PR description is complete

**During Review:**
- [ ] Code follows conventions
- [ ] Tests cover new functionality
- [ ] No security vulnerabilities
- [ ] Documentation updated

**Before Merging:**
- [ ] CI checks pass
- [ ] Required approvals received
- [ ] Conflicts resolved
- [ ] JIRA issue updated

## Next Steps

- [Development Panel](development-panel.md) - View PRs in JIRA
- [CI/CD Integration](ci-cd-integration.md) - Automated workflows
- [Automation Rules](automation-rules.md) - Auto-transition on merge
