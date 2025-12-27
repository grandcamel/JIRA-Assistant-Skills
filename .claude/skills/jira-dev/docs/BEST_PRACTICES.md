# JIRA Developer Workflow Integration Best Practices

Comprehensive guide to integrating JIRA with developer workflows including Git, CI/CD pipelines, and release automation.

---

## Table of Contents

1. [Branch Naming Conventions](#branch-naming-conventions)
2. [Commit Message Formats](#commit-message-formats)
3. [Smart Commits](#smart-commits)
4. [Pull Request Best Practices](#pull-request-best-practices)
5. [Development Panel Usage](#development-panel-usage)
6. [CI/CD Integration Patterns](#cicd-integration-patterns)
7. [Automated Workflow Transitions](#automated-workflow-transitions)
8. [Deployment Tracking](#deployment-tracking)
9. [Release Notes Generation](#release-notes-generation)
10. [Common Pitfalls](#common-pitfalls)
11. [Quick Reference Card](#quick-reference-card)

---

## Branch Naming Conventions

### Standard Format

Follow the pattern: `<type>/<issue-key>-<description>`

**Examples:**
```bash
feature/PROJ-123-user-authentication
bugfix/PROJ-456-memory-leak
hotfix/PROJ-789-payment-api-timeout
task/PROJ-101-database-migration
```

### Branch Type Prefixes

| Branch Type | When to Use | JIRA Issue Type |
|-------------|-------------|-----------------|
| `feature/` | New functionality or improvements | Story, Feature, Improvement, Enhancement |
| `bugfix/` | Bug fixes (non-critical) | Bug, Defect |
| `hotfix/` | Critical bugs in production | Bug (High/Critical priority) |
| `task/` | Technical work, enabler tasks | Task, Sub-task |
| `epic/` | Large feature that needs a dedicated branch | Epic |
| `spike/` | Research, proof of concept | Spike, Research |
| `chore/` | Maintenance, refactoring | Chore, Maintenance |
| `docs/` | Documentation changes | Documentation |
| `release/` | Release preparation | N/A (version-based) |

### Naming Rules

**Do:**
- Use lowercase with hyphens (kebab-case)
- Include the JIRA issue key in UPPERCASE
- Keep description short but meaningful (3-5 words max)
- Use imperative form: `add-feature` not `added-feature`
- Auto-generate from JIRA using `create_branch_name.py`

**Don't:**
- Use underscores or camelCase
- Include spaces or special characters
- Make it too long (>80 characters)
- Use only numbers (e.g., `feature/123`)
- Omit the issue key

**Examples:**

| Bad | Good | Why |
|-----|------|-----|
| `my-branch` | `feature/proj-123-user-login` | Missing issue key and type |
| `Feature_PROJ_123` | `feature/proj-123-add-oauth` | Underscores, no description |
| `proj-123` | `bugfix/proj-123-null-pointer` | Missing type and description |
| `PROJ-123-implement-complex-user-authentication-with-oauth-support` | `feature/proj-123-oauth-auth` | Too long |

### Using create_branch_name.py

```bash
# Auto-generate from JIRA issue
python create_branch_name.py PROJ-123
# Output: feature/proj-123-fix-login-button

# Auto-detect prefix from issue type
python create_branch_name.py PROJ-123 --auto-prefix
# Bug -> bugfix/proj-123-fix-login-button
# Story -> feature/proj-123-add-user-profile

# Custom prefix
python create_branch_name.py PROJ-123 --prefix hotfix

# Generate git command
python create_branch_name.py PROJ-123 --output git
# Output: git checkout -b feature/proj-123-fix-login-button

# Use directly in git
$(python create_branch_name.py PROJ-123 --output git)
```

---

## Commit Message Formats

### Basic Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Always Include JIRA Issue Keys

**Formats that JIRA recognizes:**

```bash
# Direct reference
PROJ-123 Fix authentication bug

# Conventional Commits style
feat(auth): PROJ-123 add OAuth support

# Action prefix
Fixes PROJ-123: Null pointer in login
Closes PROJ-456: Memory leak in cache
Resolves PROJ-789: API timeout

# Brackets
[PROJ-123] Fix login button styling

# Multiple issues
PROJ-123 PROJ-456 Update shared dependencies
```

### Commit Types

Use conventional commit types for clarity:

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(auth): PROJ-123 add two-factor authentication` |
| `fix` | Bug fix | `fix(api): PROJ-456 handle null response` |
| `docs` | Documentation | `docs: PROJ-789 update API guide` |
| `style` | Code style (no logic change) | `style: PROJ-101 format with prettier` |
| `refactor` | Code refactoring | `refactor(db): PROJ-202 optimize query performance` |
| `perf` | Performance improvement | `perf(cache): PROJ-303 reduce memory usage` |
| `test` | Add/update tests | `test(auth): PROJ-404 add OAuth tests` |
| `build` | Build system changes | `build: PROJ-505 update webpack config` |
| `ci` | CI/CD changes | `ci: PROJ-606 add GitHub Actions workflow` |
| `chore` | Maintenance | `chore: PROJ-707 update dependencies` |

### Good Commit Message Examples

```bash
# Feature with context
feat(payments): PROJ-123 add Stripe integration

Implements Stripe payment processing with webhook support.
Includes error handling and retry logic for failed transactions.

Refs: PROJ-123

# Bug fix with reproduction steps
fix(login): PROJ-456 prevent session timeout on mobile

Users were getting logged out after 5 minutes on mobile Safari.
Fixed by updating session cookie settings to SameSite=None.

Fixes: PROJ-456

# Multiple related changes
refactor(api): PROJ-789 PROJ-790 consolidate error handling

- Unified error response format across all endpoints
- Added custom error classes for better debugging
- Updated tests to match new error structure

Closes: PROJ-789, PROJ-790
```

### Bad Commit Message Examples

| Bad | Problem | Good |
|-----|---------|------|
| `fixed stuff` | No issue key, vague | `fix(auth): PROJ-123 resolve token expiration` |
| `WIP` | No context | `feat(api): PROJ-456 add user endpoint (WIP)` |
| `Updated files` | No detail | `docs: PROJ-789 update installation guide` |
| `proj-123` | Only issue key | `fix(ui): PROJ-123 align button spacing` |

---

## Smart Commits

Smart Commits allow you to perform JIRA actions directly from commit messages.

### Syntax

```
<ignored-text> <ISSUE-KEY> <ignored-text> #<command> <command-arguments>
```

### Available Commands

#### 1. #comment - Add Comments

```bash
git commit -m "PROJ-123 #comment Fixed the login bug"

git commit -m "PROJ-456 #comment This is a complex change that requires review"

# Multi-line (if supported)
git commit -m "PROJ-789 #comment Code review feedback addressed:
- Updated error handling
- Added unit tests
- Improved performance"
```

#### 2. #time - Log Work

```bash
# Log time
git commit -m "PROJ-123 #time 2h Fixed authentication"

git commit -m "PROJ-456 #time 1d 4h Implemented payment processing"

# Time formats accepted
#time 30m     # 30 minutes
#time 2h      # 2 hours
#time 1d      # 1 day (typically 8 hours)
#time 1w      # 1 week (typically 5 days)
#time 2h 30m  # 2 hours 30 minutes
```

#### 3. #transition - Change Status

```bash
# Transition to status
git commit -m "PROJ-123 #in-progress Starting work"

git commit -m "PROJ-456 #done Fixed and tested"

# Common transitions (use status name before first space)
#start         # Start Progress
#stop          # Stop Progress
#in-review     # In Review
#in-qa         # In QA
#done          # Done
#close         # Closed
```

### Combining Commands

You can use multiple commands in one commit:

```bash
# Comment + time
git commit -m "PROJ-123 #comment Fixed auth bug #time 2h"

# Transition + comment
git commit -m "PROJ-456 #done #comment All tests passing"

# All three
git commit -m "PROJ-789 #in-review #time 3h #comment Ready for review"

# Multiple lines (each command on separate line)
git commit -m "PROJ-123 #time 2h
#comment Implemented OAuth
#in-review"
```

### Smart Commits Requirements

**For Smart Commits to work:**

1. **Email must match:** Git email must exactly match JIRA user email
   ```bash
   git config user.email "your.email@company.com"
   ```

2. **Integration required:** JIRA must have Git integration installed
   - Bitbucket integration (native)
   - GitHub for JIRA app
   - GitLab integration
   - Git Integration for JIRA app

3. **Permissions:** User must have permission to:
   - Comment on issues (#comment)
   - Log work (#time)
   - Transition issues (#transition)

4. **Issue key format:** Must use uppercase: `PROJ-123` not `proj-123`

### Smart Commits Examples by Workflow

**Starting work:**
```bash
git commit -m "PROJ-123 #start #comment Beginning implementation"
```

**During development:**
```bash
git commit -m "PROJ-123 #time 1h #comment Added validation logic"
git commit -m "PROJ-123 #time 2h #comment Implemented API endpoint"
```

**Code review:**
```bash
git commit -m "PROJ-123 #in-review #comment PR created, ready for review"
```

**After review:**
```bash
git commit -m "PROJ-123 #time 30m #comment Addressed review feedback"
```

**Completing work:**
```bash
git commit -m "PROJ-123 #done #time 1h #comment All tests passing, ready to merge"
```

---

## Pull Request Best Practices

### PR Title Format

Include the JIRA issue key for automatic linking:

```
PROJ-123: Add user authentication
[PROJ-456] Fix memory leak in cache
feat(api): PROJ-789 implement rate limiting
```

### PR Description Template

Use `create_pr_description.py` to generate from JIRA:

```bash
python create_pr_description.py PROJ-123 --include-checklist
```

**Standard PR template:**

```markdown
## Summary

[Brief description of changes]

## JIRA Issue

[PROJ-123](https://your-company.atlassian.net/browse/PROJ-123)

**Type:** [Bug/Story/Task]
**Priority:** [High/Medium/Low]

## Description

[Detailed explanation from JIRA issue]

## Changes Made

- [List key changes]
- [Technical implementation details]

## Acceptance Criteria

- [ ] [Criterion 1 from JIRA]
- [ ] [Criterion 2 from JIRA]
- [ ] [Criterion 3 from JIRA]

## Testing Checklist

- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] No regressions introduced
- [ ] Performance impact assessed

## Screenshots/Videos

[If applicable]

## Deployment Notes

[Any special deployment considerations]

## Related PRs

- [Link to related PRs if any]
```

### PR Linking Strategies

**1. Automatic Linking (Recommended)**

Use JIRA issue key in branch name:
```bash
git checkout -b feature/proj-123-user-auth
# PR created from this branch auto-links to PROJ-123
```

**2. Manual Linking**

```bash
# Link PR after creation
python link_pr.py PROJ-123 --pr https://github.com/org/repo/pull/456

# With status
python link_pr.py PROJ-123 --pr https://github.com/org/repo/pull/456 --status open --title "Add user auth"
```

**3. Smart Commits in PR Description**

```markdown
Fixes PROJ-123
Closes PROJ-456
Resolves PROJ-789
```

### PR Review Checklist

**Before Creating PR:**
- [ ] Branch name includes JIRA issue key
- [ ] Commits reference JIRA issue
- [ ] All tests pass locally
- [ ] Code is self-documented
- [ ] PR description is complete

**During Review:**
- [ ] Code follows team conventions
- [ ] Tests cover new functionality
- [ ] No security vulnerabilities
- [ ] Performance is acceptable
- [ ] Documentation is updated

**Before Merging:**
- [ ] All CI checks pass
- [ ] Required approvals received
- [ ] Conflicts resolved
- [ ] JIRA issue updated
- [ ] Squash commits if needed

---

## Development Panel Usage

The JIRA Development Panel displays Git activity associated with issues.

### What Appears in Development Panel

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
- Link to build logs

**Deployments:**
- Deployment environment (dev, staging, prod)
- Deployment status and timestamp
- Version deployed
- Link to deployment details

### Accessing Development Information

**Via UI:**
- View in JIRA issue detail page
- Development section in right panel
- Click icons for repository links

**Via API:**

```bash
# Get commits for issue
python get_issue_commits.py PROJ-123

# With details
python get_issue_commits.py PROJ-123 --detailed

# JSON output
python get_issue_commits.py PROJ-123 --output json
```

### Best Practices

**1. Consistent Naming:**
- Always include issue key in branches: `feature/proj-123-name`
- Reference issues in commits: `PROJ-123 commit message`
- Link PRs explicitly if auto-linking fails

**2. Keep it Updated:**
- Push branches regularly (makes them visible)
- Create PRs promptly (shows progress)
- Merge or delete stale branches

**3. Use for Visibility:**
- Product managers can track development progress
- QA can see what changed for testing
- DevOps can link deployments to changes

**4. Troubleshooting:**

| Issue | Solution |
|-------|----------|
| Branch not showing | Push to remote: `git push -u origin branch-name` |
| Commits not appearing | Verify issue key format: `PROJ-123` not `proj-123` |
| PR not linked | Check Git integration is installed and configured |
| Development panel empty | Verify email in Git config matches JIRA user |

---

## CI/CD Integration Patterns

### Jenkins Integration

**1. Install JIRA Plugin:**
```groovy
// Jenkinsfile
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                script {
                    // Update JIRA with build info
                    jiraSendBuildInfo(
                        site: 'your-jira-instance',
                        branch: env.BRANCH_NAME
                    )
                }
                sh 'npm install'
                sh 'npm run build'
            }
        }

        stage('Test') {
            steps {
                sh 'npm test'
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Send deployment info to JIRA
                    jiraSendDeploymentInfo(
                        site: 'your-jira-instance',
                        environmentId: 'production',
                        environmentName: 'Production',
                        environmentType: 'production',
                        state: 'successful'
                    )
                }
                sh 'npm run deploy'
            }
        }
    }

    post {
        always {
            // Comment on JIRA issues mentioned in commits
            script {
                def issues = sh(
                    script: "git log --format=%B -n 1 | grep -oE '[A-Z]+-[0-9]+' | sort -u",
                    returnStdout: true
                ).trim()

                if (issues) {
                    issues.split('\n').each { issue ->
                        jiraComment(
                            issueKey: issue,
                            body: "Build ${currentBuild.result}: ${env.BUILD_URL}"
                        )
                    }
                }
            }
        }
    }
}
```

**2. Update JIRA on Build Status:**
```groovy
// Update status based on build result
stage('Update JIRA') {
    steps {
        script {
            if (currentBuild.result == 'SUCCESS') {
                jiraTransitionIssue(
                    idOrKey: env.JIRA_ISSUE,
                    input: [transition: [id: '31']] // ID for "Done"
                )
            }
        }
    }
}
```

### GitHub Actions Integration

**1. Basic Workflow:**

```yaml
# .github/workflows/jira-integration.yml
name: JIRA Integration

on:
  push:
    branches: [ main, develop, 'feature/*' ]
  pull_request:
    types: [ opened, synchronize, reopened ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Extract JIRA issues
        id: extract-issues
        run: |
          ISSUES=$(git log --format=%B -n 1 | grep -oE '[A-Z]+-[0-9]+' | sort -u | tr '\n' ',')
          echo "issues=${ISSUES%,}" >> $GITHUB_OUTPUT

      - name: Send build info to JIRA
        if: steps.extract-issues.outputs.issues != ''
        uses: HighwayThree/jira-upload-build-info@v1
        with:
          cloud-instance-base-url: ${{ secrets.JIRA_BASE_URL }}
          client-id: ${{ secrets.JIRA_CLIENT_ID }}
          client-secret: ${{ secrets.JIRA_CLIENT_SECRET }}
          pipeline-id: '${{ github.repository }} ${{ github.workflow }}'
          build-number: ${{ github.run_number }}
          build-display-name: 'Build #${{ github.run_number }}'
          build-state: 'successful'
          build-url: '${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}'
          update-sequence-number: '${{ github.run_id }}'
          issue-keys: ${{ steps.extract-issues.outputs.issues }}

      - name: Build
        run: |
          npm install
          npm run build

      - name: Test
        run: npm test

      - name: Deploy to Production
        if: github.ref == 'refs/heads/main'
        run: npm run deploy

      - name: Send deployment info to JIRA
        if: github.ref == 'refs/heads/main'
        uses: HighwayThree/jira-upload-deployment-info@v1
        with:
          cloud-instance-base-url: ${{ secrets.JIRA_BASE_URL }}
          client-id: ${{ secrets.JIRA_CLIENT_ID }}
          client-secret: ${{ secrets.JIRA_CLIENT_SECRET }}
          deployment-sequence-number: '${{ github.run_id }}'
          update-sequence-number: '${{ github.run_id }}'
          issue-keys: ${{ steps.extract-issues.outputs.issues }}
          environment-id: 'production'
          environment-name: 'Production'
          environment-type: 'production'
          state: 'successful'
```

**2. Comment on JIRA from PR:**

```yaml
# .github/workflows/pr-comment.yml
name: PR JIRA Comment

on:
  pull_request:
    types: [ opened, reopened ]

jobs:
  comment:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Extract JIRA issue
        id: issue
        run: |
          BRANCH="${{ github.head_ref }}"
          ISSUE=$(echo "$BRANCH" | grep -oE '[A-Z]+-[0-9]+' | head -n 1)
          echo "key=$ISSUE" >> $GITHUB_OUTPUT

      - name: Comment on JIRA
        if: steps.issue.outputs.key != ''
        uses: atlassian/gajira-comment@v3
        with:
          issue: ${{ steps.issue.outputs.key }}
          comment: |
            PR created: ${{ github.event.pull_request.html_url }}
            Title: ${{ github.event.pull_request.title }}
            Author: @${{ github.actor }}
        env:
          JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
          JIRA_USER_EMAIL: ${{ secrets.JIRA_USER_EMAIL }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
```

### GitLab CI Integration

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy
  - notify

variables:
  JIRA_URL: "https://your-company.atlassian.net"

build:
  stage: build
  script:
    - npm install
    - npm run build
  artifacts:
    paths:
      - dist/

test:
  stage: test
  script:
    - npm test

deploy:production:
  stage: deploy
  script:
    - npm run deploy
  only:
    - main
  environment:
    name: production
    url: https://production.example.com

notify_jira:
  stage: notify
  script:
    # Extract JIRA issues from commit messages
    - |
      ISSUES=$(git log -1 --pretty=%B | grep -oE '[A-Z]+-[0-9]+' | sort -u)
      for issue in $ISSUES; do
        curl -X POST \
          -H "Authorization: Basic $(echo -n ${JIRA_EMAIL}:${JIRA_TOKEN} | base64)" \
          -H "Content-Type: application/json" \
          -d "{
            \"body\": \"Pipeline ${CI_PIPELINE_ID} ${CI_JOB_STATUS}: ${CI_PIPELINE_URL}\"
          }" \
          "${JIRA_URL}/rest/api/3/issue/${issue}/comment"
      done
  only:
    - main
```

### Integration Benefits

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

---

## Automated Workflow Transitions

### Transition on PR Events

**1. PR Opened → In Review:**

```yaml
# JIRA Automation Rule
Trigger: Development event (Pull request created)
Condition: Issue status = "In Progress"
Action: Transition issue to "In Review"
```

**2. PR Merged → Done:**

```yaml
# JIRA Automation Rule
Trigger: Pull request merged
Conditions:
  - Issue status = "In Review"
  - JQL: development[pullrequests].open = 0  # No other open PRs
Action:
  - Transition issue to "Done"
  - Add comment: "PR merged: {{pullRequest.url}}"
```

**3. PR Approved → Ready for Merge:**

```yaml
# JIRA Automation Rule
Trigger: Pull request approved
Condition: Issue status = "In Review"
Action: Transition issue to "Ready for Merge"
```

### Transition on Build Events

**1. Build Success → Ready for QA:**

```yaml
# JIRA Automation Rule (Cloud only)
Trigger: Build successful
Conditions:
  - Issue status = "In Progress"
  - Build branch matches issue branch
Action: Transition issue to "Ready for QA"
```

**2. Deployment Success → Released:**

```yaml
# JIRA Automation Rule
Trigger: Deployment successful
Conditions:
  - Environment = "production"
  - Issue status = "Done"
Action:
  - Transition issue to "Released"
  - Add comment: "Deployed to production"
  - Set Fix Version
```

### Custom Transition Logic

**Transition only when all PRs merged:**

```yaml
# JIRA Automation Rule
Trigger: Pull request merged
Conditions:
  - Issue status IN ("In Review", "In QA")
  - Advanced JQL: development[pullrequests].open = 0 AND development[pullrequests].merged > 0
Action:
  - Transition issue to "Done"
  - Add comment: "All PRs merged, moving to Done"
```

**Transition based on branch name:**

```yaml
# JIRA Automation Rule
Trigger: Branch created
Conditions:
  - Branch name starts with "hotfix/"
  - Issue status = "To Do"
Action:
  - Transition issue to "In Progress"
  - Set Priority to "Highest"
  - Add label "hotfix"
```

### Smart Values for Automation

Useful smart values in automation rules:

```
{{issue.key}}                  # PROJ-123
{{issue.summary}}              # Issue title
{{issue.status.name}}          # Current status
{{pullRequest.url}}            # PR URL
{{pullRequest.title}}          # PR title
{{pullRequest.sourceBranch}}   # Source branch name
{{build.state}}                # Build status
{{deployment.environment}}     # Deployment environment
{{commit.authorName}}          # Commit author
```

### Example: Complete Workflow Automation

```yaml
# Rule 1: Branch created → Start Progress
Trigger: Branch created
Condition: Issue status = "To Do"
Action: Transition to "In Progress"

# Rule 2: PR created → In Review
Trigger: Pull request created
Condition: Issue status = "In Progress"
Action:
  - Transition to "In Review"
  - Add comment: "PR created: {{pullRequest.url}}"

# Rule 3: Build failed → Flag
Trigger: Build failed
Condition: Issue status = "In Review"
Action:
  - Add flag with message "Build failed"
  - Add comment: "Build failed: {{build.url}}"

# Rule 4: All PRs merged → Done
Trigger: Pull request merged
Conditions:
  - Issue status = "In Review"
  - JQL: development[pullrequests].open = 0
Action:
  - Transition to "Done"
  - Add comment: "All PRs merged"

# Rule 5: Deployed to prod → Released
Trigger: Deployment successful
Conditions:
  - Environment = "production"
  - Issue status = "Done"
Action:
  - Transition to "Released"
  - Set Fix Version to {{deployment.version}}
  - Add comment: "Deployed to production"
```

---

## Deployment Tracking

### Link Deployments to JIRA

**Via API (CI/CD Pipeline):**

```bash
# Send deployment info via REST API
curl -X POST \
  "https://your-company.atlassian.net/rest/deployments/0.1/bulk" \
  -H "Authorization: Bearer ${JIRA_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "deployments": [
      {
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
      }
    ]
  }'
```

**Via GitHub Actions:**

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

### Environment Types

| Environment Type | When to Use | Example |
|------------------|-------------|---------|
| `development` | Developer environments | Local, dev server |
| `testing` | QA/test environments | QA server, staging |
| `staging` | Pre-production | Staging environment |
| `production` | Live production | Production servers |

### Deployment States

| State | Meaning |
|-------|---------|
| `unknown` | Deployment state unknown |
| `pending` | Deployment queued/waiting |
| `in_progress` | Currently deploying |
| `cancelled` | Deployment cancelled |
| `failed` | Deployment failed |
| `rolled_back` | Rolled back to previous version |
| `successful` | Deployment successful |

### Viewing Deployments in JIRA

**In Issue View:**
1. Open JIRA issue (e.g., PROJ-123)
2. Look for "Deployments" section in Development panel
3. See deployment environments, status, and timestamps
4. Click deployment link to view details in CI/CD tool

**In Releases:**
1. Navigate to Releases page
2. Select version (e.g., v2.0.0)
3. View all deployments for issues in that version
4. See deployment timeline across environments

### Best Practices

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
# On deployment failure
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
  - Set Fix Version to {{deployment.version}}
  - Transition to "Released"
```

---

## Release Notes Generation

### Using JIRA Built-in Release Notes

**1. Via UI:**
- Navigate to Project → Releases
- Select version (e.g., v2.0.0)
- Click "Release notes" button
- Choose format: HTML or plain text
- Copy or download

**2. Via API:**

```bash
# Get issues for version
curl -X GET \
  "https://your-company.atlassian.net/rest/api/3/search?jql=project=PROJ+AND+fixVersion=2.0.0" \
  -H "Authorization: Bearer ${JIRA_API_TOKEN}"
```

### Automated Release Notes Generation

**Script to generate from JIRA:**

```bash
#!/bin/bash
# generate-release-notes.sh

VERSION="$1"
PROJECT="$2"

# JQL to find issues in version
JQL="project=${PROJECT}+AND+fixVersion=${VERSION}+ORDER+BY+type,priority+DESC"

# Fetch issues
curl -s -X GET \
  "https://your-company.atlassian.net/rest/api/3/search?jql=${JQL}" \
  -H "Authorization: Bearer ${JIRA_API_TOKEN}" \
  -H "Content-Type: application/json" \
  | jq -r '
    "# Release Notes - " + (.issues[0].fields.fixVersions[] | select(.name == "'$VERSION'") | .name),
    "",
    "## New Features",
    (.issues[] | select(.fields.issuetype.name == "Story" or .fields.issuetype.name == "Feature") |
      "- **" + .key + "**: " + .fields.summary),
    "",
    "## Bug Fixes",
    (.issues[] | select(.fields.issuetype.name == "Bug") |
      "- **" + .key + "**: " + .fields.summary),
    "",
    "## Improvements",
    (.issues[] | select(.fields.issuetype.name == "Improvement" or .fields.issuetype.name == "Enhancement") |
      "- **" + .key + "**: " + .fields.summary)
  ' > "release-notes-${VERSION}.md"

echo "Release notes generated: release-notes-${VERSION}.md"
```

**Usage:**
```bash
./generate-release-notes.sh "2.0.0" "PROJ"
```

### GitHub Release with JIRA Integration

```yaml
# .github/workflows/release.yml
name: Create Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Generate release notes from JIRA
        id: release-notes
        env:
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
          VERSION: ${{ steps.version.outputs.VERSION }}
        run: |
          # Fetch issues from JIRA
          NOTES=$(curl -s -X GET \
            "https://your-company.atlassian.net/rest/api/3/search?jql=project=PROJ+AND+fixVersion=${VERSION}" \
            -H "Authorization: Bearer ${JIRA_API_TOKEN}" \
            | jq -r '.issues[] | "- **\(.key)**: \(.fields.summary)"')

          echo "notes<<EOF" >> $GITHUB_OUTPUT
          echo "${NOTES}" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

      - name: Create GitHub Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ steps.version.outputs.VERSION }}
          body: |
            # Release ${{ steps.version.outputs.VERSION }}

            ## Changes
            ${{ steps.release-notes.outputs.notes }}

            See [JIRA Release](https://your-company.atlassian.net/projects/PROJ/versions/${{ steps.version.outputs.VERSION }}) for full details.
          draft: false
          prerelease: false
```

### Release Notes Template

```markdown
# Release v2.0.0 - December 26, 2025

## Summary
This release includes major improvements to authentication, bug fixes for the payment system, and performance optimizations.

## New Features
- **PROJ-123**: Add OAuth 2.0 authentication support
- **PROJ-456**: Implement two-factor authentication
- **PROJ-789**: Add user profile customization

## Bug Fixes
- **PROJ-234**: Fix payment timeout on slow connections
- **PROJ-567**: Resolve session expiration on mobile devices
- **PROJ-890**: Correct timezone handling in reports

## Improvements
- **PROJ-345**: Optimize database queries (50% faster)
- **PROJ-678**: Improve error messages for API responses
- **PROJ-901**: Update UI for better accessibility

## Technical Changes
- **PROJ-111**: Upgrade to Node.js 20
- **PROJ-222**: Migrate to PostgreSQL 16
- **PROJ-333**: Update CI/CD pipeline

## Breaking Changes
- **PROJ-444**: API v1 deprecated (use API v2)
- **PROJ-555**: Remove legacy authentication endpoints

## Known Issues
- **PROJ-666**: Intermittent timeout on large file uploads (fix planned for v2.1)

## Deployment Notes
1. Run database migration: `npm run migrate`
2. Update environment variables (see `.env.example`)
3. Restart application servers

## Contributors
- @developer1 (15 issues)
- @developer2 (12 issues)
- @developer3 (8 issues)

Full changelog: https://your-company.atlassian.net/projects/PROJ/versions/10100
```

### Best Practices

**1. Group by Type:**
- Separate features, bugs, improvements
- Use consistent formatting
- Include JIRA issue keys

**2. User-Friendly Language:**
- Avoid technical jargon for end-user notes
- Explain impact, not implementation
- Include "why it matters"

**3. Include Links:**
- Link to JIRA issues for details
- Reference documentation updates
- Include migration guides

**4. Automate When Possible:**
- Generate from JIRA during release
- Include in CI/CD pipeline
- Version control release notes

**5. Communicate Breaking Changes:**
- Highlight prominently
- Provide migration path
- Include timeline for deprecation

---

## Common Pitfalls

### Pitfall 1: Inconsistent Branch Naming

**Problem:**
```bash
# Team members use different formats
my-feature
PROJ-123
feature-proj-123
proj-123-feature
```

**Solution:**
```bash
# Use standardized script
python create_branch_name.py PROJ-123 --auto-prefix

# Add git alias
git config alias.jira-branch '!f() { $(python /path/to/create_branch_name.py "$1" --output git); }; f'

# Usage
git jira-branch PROJ-123
```

### Pitfall 2: Missing JIRA Keys in Commits

**Problem:**
```bash
git commit -m "Fixed login bug"
# JIRA has no idea this commit exists
```

**Solution:**
```bash
# Always include issue key
git commit -m "PROJ-123 Fixed login bug"

# Use commit message template
git config commit.template .gitmessage

# .gitmessage
PROJ-XXX:

# Why:
# What changed:
```

### Pitfall 3: Smart Commits Not Working

**Problem:**
```bash
git commit -m "proj-123 #done"  # Lowercase key
git commit -m "PROJ-123#done"   # Missing space
git commit -m "PROJ-123 #finish work"  # Invalid transition
```

**Solution:**
```bash
# Correct format
git commit -m "PROJ-123 #done"

# Check git email matches JIRA
git config user.email  # Must match JIRA user email exactly

# Test transition name
python link_commit.py PROJ-123 --commit abc123 --test-transition "done"
```

### Pitfall 4: Overwhelming Automation

**Problem:**
- Too many automatic transitions
- Issues moving without human verification
- Confusion about current state

**Solution:**
- Start with manual transitions
- Add automation incrementally
- Test on small project first
- Always add audit comments
- Keep override capability

### Pitfall 5: PR Without Context

**Problem:**
```markdown
PR title: "Updates"
Description: "Fixed stuff"
```

**Solution:**
```bash
# Generate from JIRA
python create_pr_description.py PROJ-123 --include-checklist

# Use PR template
# .github/pull_request_template.md
## JIRA Issue
[PROJ-XXX](https://...)

## What changed?

## Why?

## Testing
- [ ] Tests added
- [ ] Manual testing done
```

### Pitfall 6: Development Panel Empty

**Problem:**
- Commits not appearing
- Branches not showing
- PRs not linked

**Solution:**

| Symptom | Cause | Fix |
|---------|-------|-----|
| No commits | Issue key format wrong | Use UPPERCASE: `PROJ-123` |
| No branches | Not pushed to remote | `git push -u origin branch` |
| No PRs | Integration not installed | Install GitHub/GitLab for JIRA |
| No builds | Email mismatch | Git email must match JIRA user |

**Verification:**
```bash
# Check git email
git config user.email

# Check JIRA user email (via API)
curl -H "Authorization: Bearer ${JIRA_API_TOKEN}" \
  https://your-company.atlassian.net/rest/api/3/myself \
  | jq -r '.emailAddress'

# They MUST match exactly
```

### Pitfall 7: Deployment Tracking Issues

**Problem:**
- Deployments not showing in JIRA
- Wrong environment type
- Missing issue keys

**Solution:**
```yaml
# Always include:
- deployment-sequence-number (unique)
- issue-keys (from commits)
- environment-type (production/staging/testing/development)
- state (successful/failed)

# Extract issues from commits
git log main..HEAD --format=%B | grep -oE '[A-Z]+-[0-9]+' | sort -u
```

### Pitfall 8: Release Notes Chaos

**Problem:**
- Missing issues in release notes
- Wrong version tagged
- Incomplete information

**Solution:**
- Tag fix version during development
- Use JQL to verify completeness:
  ```jql
  project = PROJ AND fixVersion = "2.0.0" AND status != Done
  ```
- Automate generation in CI/CD
- Review before publishing

---

## Quick Reference Card

### Branch Naming

```bash
# Format
<type>/<issue-key>-<description>

# Examples
feature/proj-123-user-auth
bugfix/proj-456-memory-leak
hotfix/proj-789-api-timeout

# Auto-generate
python create_branch_name.py PROJ-123 --auto-prefix
```

### Commit Messages

```bash
# With JIRA key
git commit -m "PROJ-123 Fix authentication bug"

# Conventional commits
git commit -m "feat(auth): PROJ-123 add OAuth support"

# Smart commits
git commit -m "PROJ-123 #time 2h #comment Fixed bug"
git commit -m "PROJ-456 #in-review #time 3h"
git commit -m "PROJ-789 #done All tests passing"
```

### Smart Commit Commands

| Command | Example | Purpose |
|---------|---------|---------|
| `#comment` | `#comment Fixed auth bug` | Add comment |
| `#time` | `#time 2h` | Log work |
| `#<transition>` | `#in-review` | Change status |

### PR Commands

```bash
# Generate description from JIRA
python create_pr_description.py PROJ-123 --include-checklist

# Link PR manually
python link_pr.py PROJ-123 --pr https://github.com/org/repo/pull/456

# Get commits for issue
python get_issue_commits.py PROJ-123 --detailed
```

### Useful JQL

```jql
# Find issues without fix version
project = PROJ AND status = Done AND fixVersion IS EMPTY

# Issues with open PRs
project = PROJ AND development[pullrequests].open > 0

# Issues deployed to production
project = PROJ AND development[deployment].environment = production

# Issues with failed builds
project = PROJ AND development[builds].state = failed
```

### Git Configuration

```bash
# Set email (MUST match JIRA)
git config user.email "your@company.com"

# Commit message template
git config commit.template .gitmessage

# Alias for branch creation
git config alias.jira-branch '!f() { $(python create_branch_name.py "$1" --output git); }; f'

# Usage
git jira-branch PROJ-123
```

### Automation Rule Pattern

```yaml
Trigger: [Pull request merged / Branch created / Build status]
Conditions:
  - Issue status = [Current status]
  - Additional filters
Action:
  - Transition issue to [New status]
  - Add comment: [Message with smart values]
  - [Optional: Assign, label, etc.]
```

### CI/CD Integration Checklist

- [ ] Install JIRA integration plugin/app
- [ ] Configure authentication (API token)
- [ ] Extract JIRA keys from commits
- [ ] Send build info to JIRA
- [ ] Send deployment info to JIRA
- [ ] Add JIRA comments on success/failure
- [ ] Set up automatic transitions
- [ ] Test with sample issue

### Troubleshooting Checklist

**Development Panel Empty?**
- [ ] Issue key in UPPERCASE: `PROJ-123`
- [ ] Branch pushed to remote
- [ ] Git email matches JIRA user
- [ ] Integration installed and configured

**Smart Commits Not Working?**
- [ ] Git email matches JIRA user exactly
- [ ] Issue key format correct
- [ ] Space before command: `PROJ-123 #time`
- [ ] Valid transition name
- [ ] User has required permissions

**Automation Not Triggering?**
- [ ] Rule enabled
- [ ] Conditions met
- [ ] Integration connected
- [ ] Check audit log for errors

---

## Additional Resources

### Official Documentation
- [JIRA Smart Commits](https://support.atlassian.com/jira-software-cloud/docs/process-issues-with-smart-commits/)
- [JIRA Development Panel](https://help.gitkraken.com/git-integration-for-jira-cloud/jira-git-integration-development-panel-gij-cloud/)
- [GitHub for JIRA](https://github.com/marketplace/actions/jira-development-integration)
- [JIRA Automation](https://www.atlassian.com/devops/automation-tutorials/jira-automation-rule-on-pullrequest-merge)
- [JIRA Release Management](https://www.apwide.com/release-management-in-jira/)

### Tools and Integrations
- Git Integration for JIRA (Atlassian Marketplace)
- GitHub for JIRA (Native integration)
- GitLab JIRA Integration
- Bitbucket Cloud (Native integration)
- Jenkins JIRA Plugin

### Best Practices Articles
- [Git Branch Naming Conventions 2025](https://medium.com/@jaychu259/git-branch-naming-conventions-2025-the-ultimate-guide-for-developers-5f8e0b3bb9f7)
- [JIRA CI/CD Integration](https://www.zigiwave.com/resources/integrating-jira-with-ci-cd-pipelines-for-enhanced-devops-efficiency)
- [PR Automation with JIRA](https://www.atlassian.com/devops/automation-tutorials/jira-automation-rule-on-pullrequest-merge)

---

*Last updated: December 2025*
