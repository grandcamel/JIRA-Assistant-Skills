# Release Notes Generation

**Read time:** 5 minutes

Generate release notes from JIRA issues in a version.

## Using JIRA Built-in Release Notes

### Via UI
1. Navigate to Project > Releases
2. Select version (e.g., v2.0.0)
3. Click "Release notes" button
4. Choose format: HTML or plain text
5. Copy or download

### Via API

```bash
# Get issues for version (using /search/jql per CHANGE-2046)
curl -X GET \
  "https://your-company.atlassian.net/rest/api/3/search/jql?jql=project=PROJ+AND+fixVersion=2.0.0" \
  -H "Authorization: Bearer ${JIRA_API_TOKEN}"
```

## Automated Release Notes Script

```bash
#!/bin/bash
# generate-release-notes.sh

VERSION="$1"
PROJECT="$2"

JQL="project=${PROJECT}+AND+fixVersion=${VERSION}+ORDER+BY+type,priority+DESC"

curl -s -X GET \
  "https://your-company.atlassian.net/rest/api/3/search/jql?jql=${JQL}" \
  -H "Authorization: Bearer ${JIRA_API_TOKEN}" \
  | jq -r '
    "# Release Notes - '$VERSION'",
    "",
    "## New Features",
    (.issues[] | select(.fields.issuetype.name == "Story") |
      "- **\(.key)**: \(.fields.summary)"),
    "",
    "## Bug Fixes",
    (.issues[] | select(.fields.issuetype.name == "Bug") |
      "- **\(.key)**: \(.fields.summary)")
  '
```

**Usage:**
```bash
./generate-release-notes.sh "2.0.0" "PROJ"
```

## Release Notes Template

```markdown
# Release v2.0.0 - December 2025

## Summary
Major improvements to authentication and bug fixes for payments.

## New Features
- **PROJ-123**: Add OAuth 2.0 authentication support
- **PROJ-456**: Implement two-factor authentication

## Bug Fixes
- **PROJ-234**: Fix payment timeout on slow connections
- **PROJ-567**: Resolve session expiration on mobile

## Improvements
- **PROJ-345**: Optimize database queries (50% faster)
- **PROJ-678**: Improve error messages

## Breaking Changes
- **PROJ-444**: API v1 deprecated (use API v2)

## Deployment Notes
1. Run database migration: `npm run migrate`
2. Update environment variables

Full changelog: https://your-company.atlassian.net/projects/PROJ/versions/10100
```

## GitHub Release Integration

```yaml
# .github/workflows/release.yml
- name: Generate release notes from JIRA
  run: |
    NOTES=$(curl -s -X GET \
      "https://your-company.atlassian.net/rest/api/3/search/jql?jql=project=PROJ+AND+fixVersion=${VERSION}" \
      -H "Authorization: Bearer ${JIRA_API_TOKEN}" \
      | jq -r '.issues[] | "- **\(.key)**: \(.fields.summary)"')

- name: Create GitHub Release
  uses: actions/create-release@v1
  with:
    release_name: Release ${{ env.VERSION }}
    body: |
      ## Changes
      ${{ env.NOTES }}
```

## Best Practices

**1. Group by Type:**
- Separate features, bugs, improvements
- Include JIRA issue keys

**2. User-Friendly Language:**
- Avoid technical jargon
- Explain impact, not implementation

**3. Include Links:**
- Link to JIRA issues
- Reference documentation

**4. Automate When Possible:**
- Generate during release
- Include in CI/CD pipeline

**5. Communicate Breaking Changes:**
- Highlight prominently
- Provide migration path

## Useful JQL for Releases

```jql
# Issues in version
project = PROJ AND fixVersion = "2.0.0"

# Done issues without fix version
project = PROJ AND status = Done AND fixVersion IS EMPTY

# Issues missing from release
project = PROJ AND fixVersion = "2.0.0" AND status != Done
```

## Next Steps

- [Common Pitfalls](common-pitfalls.md) - Troubleshooting common issues
