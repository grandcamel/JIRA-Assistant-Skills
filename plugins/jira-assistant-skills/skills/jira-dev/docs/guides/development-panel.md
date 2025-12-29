# Development Panel Usage

**Read time:** 3 minutes

The JIRA Development Panel displays Git activity associated with issues.

## What Appears in Development Panel

**Branches:**
- All branches containing the issue key
- Ahead/behind commit counts
- Last commit timestamp
- Direct links to repository

**Commits:**
- All commits mentioning the issue key
- Commit message and author
- Timestamp and SHA
- Link to diff in repository

**Pull Requests:**
- Open, merged, and declined PRs
- PR status and review state
- Number of files changed
- Link to PR in repository

**Builds:**
- CI/CD build status
- Build number and duration
- Success/failure indicator

**Deployments:**
- Deployment environment (dev, staging, prod)
- Deployment status and timestamp
- Version deployed

## Accessing Development Information

### Via JIRA UI
1. Open JIRA issue (e.g., PROJ-123)
2. Look for "Development" section in right panel
3. Click icons for repository links

### Via API

```bash
# Get commits for issue
python get_issue_commits.py PROJ-123

# With details
python get_issue_commits.py PROJ-123 --detailed

# JSON output
python get_issue_commits.py PROJ-123 --output json
```

## Best Practices

**1. Consistent Naming:**
- Always include issue key in branches: `feature/PROJ-123-name`
- Reference issues in commits: `PROJ-123 commit message`
- Link PRs explicitly if auto-linking fails

**2. Keep it Updated:**
- Push branches regularly (makes them visible)
- Create PRs promptly (shows progress)
- Merge or delete stale branches

**3. Use for Visibility:**
- Product managers track development progress
- QA sees what changed for testing
- DevOps links deployments to changes

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Branch not showing | Push to remote: `git push -u origin branch-name` |
| Commits not appearing | Verify issue key format: `PROJ-123` (uppercase) |
| PR not linked | Check Git integration is installed |
| Panel empty | Verify Git email matches JIRA user |

**Verification:**
```bash
# Check git email
git config user.email

# Check JIRA user email
curl -H "Authorization: Bearer ${JIRA_API_TOKEN}" \
  https://your-company.atlassian.net/rest/api/3/myself \
  | jq -r '.emailAddress'

# They MUST match exactly
```

## Requirements

- JIRA Development Tool integration installed (GitHub for JIRA, etc.)
- Commits include JIRA issue keys in messages
- Integration has synced recent commits (may take a few minutes)
- User has permission to view development information

## Next Steps

- [CI/CD Integration](ci-cd-integration.md) - Build and deployment tracking
- [Automation Rules](automation-rules.md) - Automatic transitions
