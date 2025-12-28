# Deployment Tracking

**Read time:** 5 minutes

Track deployments in JIRA to see where your code is running.

## Sending Deployment Info

### Via REST API

```bash
curl -X POST \
  "https://your-company.atlassian.net/rest/deployments/0.1/bulk" \
  -H "Authorization: Bearer ${JIRA_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "deployments": [{
      "deploymentSequenceNumber": "12345",
      "updateSequenceNumber": "12345",
      "issueKeys": ["PROJ-123", "PROJ-456"],
      "displayName": "Deployment #123",
      "url": "https://ci.example.com/deploy/123",
      "description": "Production deployment",
      "lastUpdated": "2025-12-26T10:30:00Z",
      "state": "successful",
      "pipeline": {
        "id": "main-pipeline",
        "displayName": "Main Pipeline",
        "url": "https://ci.example.com/pipeline/main"
      },
      "environment": {
        "id": "prod",
        "displayName": "Production",
        "type": "production"
      }
    }]
  }'
```

### Via GitHub Actions

```yaml
- name: Send deployment info to JIRA
  uses: HighwayThree/jira-upload-deployment-info@v1
  with:
    cloud-instance-base-url: ${{ secrets.JIRA_BASE_URL }}
    client-id: ${{ secrets.JIRA_CLIENT_ID }}
    client-secret: ${{ secrets.JIRA_CLIENT_SECRET }}
    deployment-sequence-number: '${{ github.run_id }}'
    issue-keys: 'PROJ-123,PROJ-456'
    environment-id: 'production'
    environment-name: 'Production'
    environment-type: 'production'
    state: 'successful'
```

## Environment Types

| Type | When to Use |
|------|-------------|
| `development` | Developer environments, local |
| `testing` | QA/test environments |
| `staging` | Pre-production |
| `production` | Live production |

## Deployment States

| State | Meaning |
|-------|---------|
| `unknown` | State unknown |
| `pending` | Queued/waiting |
| `in_progress` | Currently deploying |
| `cancelled` | Deployment cancelled |
| `failed` | Deployment failed |
| `rolled_back` | Rolled back |
| `successful` | Completed successfully |

## Viewing Deployments in JIRA

**In Issue View:**
1. Open JIRA issue
2. Look for "Deployments" in Development panel
3. See environments, status, timestamps
4. Click deployment link for details

**In Releases:**
1. Navigate to Releases page
2. Select version
3. View deployments for all issues in version
4. See deployment timeline across environments

## Best Practices

**1. Track All Environments:**
```yaml
# Deploy to staging
- environment: staging
  issues: PROJ-123

# Deploy to production (same issue)
- environment: production
  issues: PROJ-123
```

**2. Include Version Information:**
```json
{
  "environment": {
    "id": "prod",
    "displayName": "Production (v2.1.0)"
  }
}
```

**3. Link Failed Deployments:**
```yaml
state: 'failed'
description: 'Deployment failed: Database migration error'
```

**4. Automatic Version Tagging:**
```yaml
# JIRA Automation Rule
Trigger: Deployment successful
Conditions:
  - Environment = "production"
Action:
  - Set Fix Version
  - Transition to "Released"
```

## Extracting Issues for Deployment

```bash
# From commits since last deployment
git log v1.0.0..HEAD --format=%B | grep -oE '[A-Z]+-[0-9]+' | sort -u

# From branch
git log main..release/2.0 --format=%B | grep -oE '[A-Z]+-[0-9]+' | sort -u
```

## Next Steps

- [Release Notes](release-notes.md) - Generate release notes
- [Automation Rules](automation-rules.md) - Auto-transition on deploy
