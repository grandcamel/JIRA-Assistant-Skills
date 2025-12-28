# CI/CD Integration Patterns

**Read time:** 10 minutes

Integrate your CI/CD pipeline with JIRA for build and deployment tracking.

## Overview

CI/CD integration enables:
- Build status visible in JIRA issues
- Deployment tracking per environment
- Automatic issue transitions
- Audit trail for releases

## Quick Setup

1. Install JIRA integration plugin for your CI/CD platform
2. Configure API authentication (token or OAuth)
3. Add build/deployment info steps to pipeline
4. Test with a sample issue

## Platform Examples

### Jenkins

See [examples/jenkins-pipeline.groovy](../examples/jenkins-pipeline.groovy) for complete configuration.

**Key steps:**
```groovy
jiraSendBuildInfo(site: 'your-jira-instance', branch: env.BRANCH_NAME)

jiraSendDeploymentInfo(
    site: 'your-jira-instance',
    environmentId: 'production',
    environmentName: 'Production',
    environmentType: 'production',
    state: 'successful'
)
```

### GitHub Actions

See [examples/github-actions-workflow.yml](../examples/github-actions-workflow.yml) for complete configuration.

**Key steps:**
```yaml
- name: Extract JIRA issues
  run: |
    ISSUES=$(git log --format=%B -n 1 | grep -oE '[A-Z]+-[0-9]+' | sort -u)

- name: Send build info to JIRA
  uses: HighwayThree/jira-upload-build-info@v1

- name: Send deployment info to JIRA
  uses: HighwayThree/jira-upload-deployment-info@v1
```

### GitLab CI

See [examples/gitlab-ci.yml](../examples/gitlab-ci.yml) for complete configuration.

## Environment Types

| Type | When to Use | Example |
|------|-------------|---------|
| `development` | Developer environments | Local, dev server |
| `testing` | QA/test environments | QA server |
| `staging` | Pre-production | Staging environment |
| `production` | Live production | Production servers |

## Deployment States

| State | Meaning |
|-------|---------|
| `pending` | Deployment queued |
| `in_progress` | Currently deploying |
| `successful` | Deployment completed |
| `failed` | Deployment failed |
| `rolled_back` | Rolled back to previous |
| `cancelled` | Deployment cancelled |

## Extracting JIRA Issues

```bash
# From commit message
git log --format=%B -n 1 | grep -oE '[A-Z]+-[0-9]+' | sort -u

# From all commits in branch
git log main..HEAD --format=%B | grep -oE '[A-Z]+-[0-9]+' | sort -u

# Using parse_commit_issues.py
git log --oneline -10 | python parse_commit_issues.py --from-stdin --unique
```

## Benefits

**Visibility:**
- Track build status in JIRA
- See deployment history per issue
- Link failures to issues

**Automation:**
- Auto-comment on builds
- Transition issues on deployment
- Create issues for failed builds

**Metrics:**
- Lead time from commit to deploy
- Build success rate per issue
- Deployment frequency

## Best Practices

1. **Extract issues from commits** - Automatically detect affected issues
2. **Track all environments** - Send deployment info for dev, staging, prod
3. **Include version information** - Tag deployments with release versions
4. **Link failed deployments** - Make failures visible in JIRA
5. **Automate transitions** - Move issues to "Released" on production deploy

## Next Steps

- [Automation Rules](automation-rules.md) - Auto-transition on events
- [Deployment Tracking](deployment-tracking.md) - Detailed deployment setup
- [Release Notes](release-notes.md) - Generate release notes from JIRA
