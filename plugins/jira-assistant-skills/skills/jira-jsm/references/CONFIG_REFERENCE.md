# JSM Configuration Reference

Configuration options for jira-jsm scripts.

## Configuration Sources

Configuration is merged from 4 sources (priority order):

1. **Environment variables** (highest priority)
2. `.claude/settings.local.json` (gitignored, personal credentials)
3. `.claude/settings.json` (committed, team defaults)
4. Hardcoded defaults (lowest priority)

---

## Environment Variables

### Required

```bash
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

### Optional

```bash
# Default service desk for JSM operations
export JSM_DEFAULT_SERVICE_DESK="1"

# Profile selection
export JIRA_PROFILE="production"
```

---

## Profile Support

All scripts support `--profile` for managing multiple JIRA instances:

```bash
# Use production profile
python create_request.py --profile prod \
  --service-desk 1 --request-type 10 --summary "Issue"

# Use staging profile
python create_request.py --profile staging \
  --service-desk 1 --request-type 10 --summary "Test"
```

### Profile Configuration

In `.claude/settings.json`:

```json
{
  "profiles": {
    "production": {
      "url": "https://company.atlassian.net",
      "project_keys": ["ITS", "HR"],
      "default_project": "ITS",
      "use_service_management": true
    },
    "staging": {
      "url": "https://company-staging.atlassian.net",
      "project_keys": ["TEST"],
      "default_project": "TEST",
      "use_service_management": true
    }
  }
}
```

---

## Settings Files

### .claude/settings.json

Global settings (committed to repo):

```json
{
  "default_profile": "production",
  "profiles": {
    "production": {
      "url": "https://company.atlassian.net"
    }
  }
}
```

### .claude/settings.local.json

Local overrides (gitignored):

```json
{
  "email": "your-email@example.com",
  "api_token": "your-token"
}
```

---

## Service Desk ID Discovery

### Method 1: List All Service Desks

```bash
python list_service_desks.py
```

### Method 2: From Project Key

```bash
python get_service_desk.py --project-key ITS
```

### Method 3: From JIRA URL

The service desk ID is visible in JIRA URLs:
- Customer Portal: `https://domain.atlassian.net/servicedesk/customer/portal/1`
- Agent View: `https://domain.atlassian.net/jira/servicedesk/projects/ITS/queues/custom/1`

The number after `/portal/` is the service desk ID.

---

## Environment Variable Helpers

Store frequently used IDs:

```bash
export IT_SERVICE_DESK=1
export HR_SERVICE_DESK=2
export INCIDENT_REQUEST_TYPE=10
export SERVICE_REQUEST_TYPE=11

python create_request.py \
  --service-desk $IT_SERVICE_DESK \
  --request-type $INCIDENT_REQUEST_TYPE \
  --summary "Issue"
```

---

## API Token Setup

1. Go to [id.atlassian.com](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Name it (e.g., "Claude Code JSM")
4. Copy the token immediately (cannot be viewed again)

---

*Last updated: December 2025*
