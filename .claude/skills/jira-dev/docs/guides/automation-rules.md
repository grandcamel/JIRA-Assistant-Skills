# Automated Workflow Transitions

**Read time:** 8 minutes

Use JIRA Automation to transition issues based on development events.

## Transition on PR Events

### PR Opened -> In Review

```yaml
Trigger: Development event (Pull request created)
Condition: Issue status = "In Progress"
Action: Transition issue to "In Review"
```

### PR Merged -> Done

```yaml
Trigger: Pull request merged
Conditions:
  - Issue status = "In Review"
  - JQL: development[pullrequests].open = 0
Action:
  - Transition issue to "Done"
  - Add comment: "PR merged: {{pullRequest.url}}"
```

### PR Approved -> Ready for Merge

```yaml
Trigger: Pull request approved
Condition: Issue status = "In Review"
Action: Transition issue to "Ready for Merge"
```

## Transition on Build Events

### Build Success -> Ready for QA

```yaml
Trigger: Build successful
Conditions:
  - Issue status = "In Progress"
  - Build branch matches issue branch
Action: Transition issue to "Ready for QA"
```

### Build Failed -> Flag Issue

```yaml
Trigger: Build failed
Condition: Issue status = "In Review"
Action:
  - Add flag with message "Build failed"
  - Add comment: "Build failed: {{build.url}}"
```

## Transition on Deployment Events

### Deployed to Production -> Released

```yaml
Trigger: Deployment successful
Conditions:
  - Environment = "production"
  - Issue status = "Done"
Action:
  - Transition to "Released"
  - Set Fix Version to {{deployment.version}}
  - Add comment: "Deployed to production"
```

## Complete Workflow Example

```yaml
# Rule 1: Branch created -> Start Progress
Trigger: Branch created
Condition: Issue status = "To Do"
Action: Transition to "In Progress"

# Rule 2: PR created -> In Review
Trigger: Pull request created
Condition: Issue status = "In Progress"
Action:
  - Transition to "In Review"
  - Add comment: "PR created: {{pullRequest.url}}"

# Rule 3: All PRs merged -> Done
Trigger: Pull request merged
Conditions:
  - Issue status = "In Review"
  - JQL: development[pullrequests].open = 0
Action:
  - Transition to "Done"
  - Add comment: "All PRs merged"

# Rule 4: Deployed to prod -> Released
Trigger: Deployment successful
Conditions:
  - Environment = "production"
  - Issue status = "Done"
Action:
  - Transition to "Released"
  - Set Fix Version
```

## Smart Values Reference

| Smart Value | Description |
|-------------|-------------|
| `{{issue.key}}` | Issue key (PROJ-123) |
| `{{issue.summary}}` | Issue title |
| `{{issue.status.name}}` | Current status |
| `{{pullRequest.url}}` | PR URL |
| `{{pullRequest.title}}` | PR title |
| `{{pullRequest.sourceBranch}}` | Source branch |
| `{{build.state}}` | Build status |
| `{{deployment.environment}}` | Environment name |
| `{{commit.authorName}}` | Commit author |

## Custom Transition Logic

### Only When All PRs Merged

```yaml
Trigger: Pull request merged
Conditions:
  - Issue status IN ("In Review", "In QA")
  - Advanced JQL: development[pullrequests].open = 0 AND development[pullrequests].merged > 0
Action:
  - Transition to "Done"
  - Add comment: "All PRs merged"
```

### Based on Branch Name

```yaml
Trigger: Branch created
Conditions:
  - Branch name starts with "hotfix/"
  - Issue status = "To Do"
Action:
  - Transition to "In Progress"
  - Set Priority to "Highest"
  - Add label "hotfix"
```

## Best Practices

1. **Start simple** - Add one rule at a time
2. **Test on small project** - Verify before rolling out
3. **Add audit comments** - Track who/what triggered transitions
4. **Keep override capability** - Allow manual transitions
5. **Check permissions** - Automation user needs transition rights

## Troubleshooting

**Rule not triggering?**
- [ ] Rule is enabled
- [ ] Conditions are met
- [ ] Integration is connected
- [ ] Check audit log for errors

## Next Steps

- [Deployment Tracking](deployment-tracking.md) - Send deployment info
- [Release Notes](release-notes.md) - Generate release notes
