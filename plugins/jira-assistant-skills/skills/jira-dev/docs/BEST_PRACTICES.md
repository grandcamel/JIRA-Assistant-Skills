# JIRA Developer Workflow Best Practices

Comprehensive guide to integrating JIRA with developer workflows including Git, CI/CD pipelines, and release automation.

## Quick Links

| Guide | Read Time | Description |
|-------|-----------|-------------|
| [Branch Naming](guides/branch-naming.md) | 3 min | Standard formats and conventions |
| [Commit Messages](guides/commit-messages.md) | 3 min | Conventional commits with JIRA keys |
| [Smart Commits](guides/smart-commits.md) | 5 min | Log time, transition from commits |
| [PR Workflows](guides/pr-workflows.md) | 5 min | Pull request best practices |
| [Development Panel](guides/development-panel.md) | 3 min | View Git activity in JIRA |
| [CI/CD Integration](guides/ci-cd-integration.md) | 10 min | Build and deployment tracking |
| [Automation Rules](guides/automation-rules.md) | 8 min | Auto-transition on events |
| [Deployment Tracking](guides/deployment-tracking.md) | 5 min | Track deployments per environment |
| [Release Notes](guides/release-notes.md) | 5 min | Generate from JIRA versions |
| [Common Pitfalls](guides/common-pitfalls.md) | 5 min | Troubleshooting guide |

## CI/CD Examples

See [examples/README.md](examples/README.md) for complete, working configurations:

| Platform | File |
|----------|------|
| Jenkins | [jenkins-pipeline.groovy](examples/jenkins-pipeline.groovy) |
| GitHub Actions | [github-actions-workflow.yml](examples/github-actions-workflow.yml) |
| GitLab CI | [gitlab-ci.yml](examples/gitlab-ci.yml) |

## Learning Path

### For Developers

1. [Branch Naming](guides/branch-naming.md) - Start with consistent naming
2. [Commit Messages](guides/commit-messages.md) - Include JIRA keys
3. [Smart Commits](guides/smart-commits.md) - Log time, transition issues
4. [PR Workflows](guides/pr-workflows.md) - Link PRs to JIRA

### For DevOps Engineers

1. [CI/CD Integration](guides/ci-cd-integration.md) - Pipeline setup
2. [Automation Rules](guides/automation-rules.md) - Auto-transitions
3. [Deployment Tracking](guides/deployment-tracking.md) - Environment tracking
4. [Release Notes](guides/release-notes.md) - Automate release notes

### For Troubleshooting

1. [Common Pitfalls](guides/common-pitfalls.md) - All common issues
2. [Development Panel](guides/development-panel.md) - Fix empty panels

## Quick Reference

### Branch Format
```
<type>/<issue-key>-<description>
feature/PROJ-123-user-auth
```

### Commit Format
```
PROJ-123 Fix authentication bug
feat(auth): PROJ-123 add OAuth support
```

### Smart Commits
```bash
git commit -m "PROJ-123 #time 2h #comment Fixed bug"
git commit -m "PROJ-456 #done All tests passing"
```

### PR Commands
```bash
python create_branch_name.py PROJ-123 --auto-prefix
python create_pr_description.py PROJ-123 --include-checklist
python link_pr.py PROJ-123 --pr https://github.com/org/repo/pull/456
```

## Additional Resources

### Official Documentation
- [JIRA Smart Commits](https://support.atlassian.com/jira-software-cloud/docs/process-issues-with-smart-commits/)
- [JIRA Development Panel](https://support.atlassian.com/jira-software-cloud/docs/view-development-information-for-an-issue/)
- [JIRA Automation](https://www.atlassian.com/software/jira/guides/automation)

### Integrations
- GitHub for JIRA
- GitLab JIRA Integration
- Bitbucket Cloud (Native)
- Jenkins JIRA Plugin

---

*Last updated: December 2025*
