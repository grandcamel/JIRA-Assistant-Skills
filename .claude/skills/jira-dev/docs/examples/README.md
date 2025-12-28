# CI/CD Integration Examples

Complete, working examples for integrating your CI/CD pipeline with JIRA.

## Available Examples

| File | Platform | Description |
|------|----------|-------------|
| [jenkins-pipeline.groovy](jenkins-pipeline.groovy) | Jenkins | Full pipeline with build/deploy tracking |
| [github-actions-workflow.yml](github-actions-workflow.yml) | GitHub Actions | Workflow with JIRA integration |
| [gitlab-ci.yml](gitlab-ci.yml) | GitLab CI | Pipeline with MR and deploy notifications |

## Features Demonstrated

All examples include:
- Extracting JIRA issue keys from commits
- Sending build information to JIRA
- Sending deployment information per environment
- Commenting on JIRA issues
- Handling success and failure states

## Required Secrets

### Jenkins
- JIRA site configuration in Jenkins system settings
- JIRA API credentials for jiraComment/jiraTransitionIssue

### GitHub Actions
```
JIRA_BASE_URL      - https://your-company.atlassian.net
JIRA_CLIENT_ID     - OAuth app client ID
JIRA_CLIENT_SECRET - OAuth app client secret
JIRA_USER_EMAIL    - User email for API auth
JIRA_API_TOKEN     - API token from id.atlassian.com
```

### GitLab CI
```
JIRA_URL    - https://your-company.atlassian.net
JIRA_EMAIL  - User email for API auth
JIRA_TOKEN  - API token from id.atlassian.com
```

## Usage

1. Copy the appropriate example to your repository
2. Configure secrets in your CI/CD platform
3. Adjust environment names and URLs
4. Test with a sample issue

## See Also

- [CI/CD Integration Guide](../guides/ci-cd-integration.md) - Concepts and patterns
- [Automation Rules](../guides/automation-rules.md) - JIRA-side automation
- [Deployment Tracking](../guides/deployment-tracking.md) - Detailed deployment setup
