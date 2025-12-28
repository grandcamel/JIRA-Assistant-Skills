# Common Pitfalls and Solutions

**Read time:** 5 minutes

Troubleshooting common issues with JIRA developer integration.

## Pitfall 1: Inconsistent Branch Naming

**Problem:**
```bash
# Team uses different formats
my-feature
PROJ-123
feature-proj-123
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

## Pitfall 2: Missing JIRA Keys in Commits

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
```

**.gitmessage:**
```
PROJ-XXX:

# Why:
# What changed:
```

## Pitfall 3: Smart Commits Not Working

**Problem:**
```bash
git commit -m "proj-123 #done"      # Lowercase key
git commit -m "PROJ-123#done"       # Missing space
git commit -m "PROJ-123 #finish"    # Invalid transition
```

**Solution:**
```bash
# Correct format
git commit -m "PROJ-123 #done"

# Check git email matches JIRA
git config user.email  # Must match JIRA user exactly
```

## Pitfall 4: Development Panel Empty

**Problem:**
- Commits not appearing
- Branches not showing
- PRs not linked

**Solution:**

| Symptom | Cause | Fix |
|---------|-------|-----|
| No commits | Issue key wrong | Use UPPERCASE: `PROJ-123` |
| No branches | Not pushed | `git push -u origin branch` |
| No PRs | Integration missing | Install GitHub for JIRA |
| No builds | Email mismatch | Git email must match JIRA |

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

## Pitfall 5: PR Without Context

**Problem:**
```markdown
PR title: "Updates"
Description: "Fixed stuff"
```

**Solution:**
```bash
# Generate from JIRA
python create_pr_description.py PROJ-123 --include-checklist
```

Use PR template in `.github/pull_request_template.md`.

## Pitfall 6: Overwhelming Automation

**Problem:**
- Too many automatic transitions
- Issues moving without verification
- Confusion about current state

**Solution:**
- Start with manual transitions
- Add automation incrementally
- Test on small project first
- Always add audit comments
- Keep override capability

## Pitfall 7: Deployment Tracking Issues

**Problem:**
- Deployments not showing in JIRA
- Wrong environment type
- Missing issue keys

**Solution:**
```yaml
# Always include:
- deployment-sequence-number (unique)
- issue-keys (from commits)
- environment-type (production/staging/testing)
- state (successful/failed)
```

Extract issues:
```bash
git log main..HEAD --format=%B | grep -oE '[A-Z]+-[0-9]+' | sort -u
```

## Pitfall 8: Release Notes Chaos

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

## Quick Troubleshooting Checklist

**Development Panel Empty?**
- [ ] Issue key in UPPERCASE
- [ ] Branch pushed to remote
- [ ] Git email matches JIRA user
- [ ] Integration installed

**Smart Commits Not Working?**
- [ ] Git email matches JIRA exactly
- [ ] Issue key format correct
- [ ] Space before command
- [ ] Valid transition name
- [ ] User has permissions

**Automation Not Triggering?**
- [ ] Rule enabled
- [ ] Conditions met
- [ ] Integration connected
- [ ] Check audit log

## Common API Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid token | Regenerate at id.atlassian.com |
| 403 Forbidden | No permission | Request access from admin |
| 404 Not Found | Issue doesn't exist | Verify issue key |
| 429 Rate Limited | Too many requests | Wait and retry |

## Getting Help

- Run `python <script>.py --help` for usage
- Check [scripts/REFERENCE.md](../../scripts/REFERENCE.md) for options
- See [Development Panel](development-panel.md) for visibility issues
- Review [Smart Commits](smart-commits.md) for commit issues
