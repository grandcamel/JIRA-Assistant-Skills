# JSM Quick Start Guide

**Quick Navigation**:
- Looking for examples? See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
- Have an error? See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Want best practices? See [BEST_PRACTICES.md](BEST_PRACTICES.md)

---

Get started with Jira Service Management in 5 minutes.

## Prerequisites

Before you begin:
- Python 3.8+ installed
- JIRA API token from [id.atlassian.com](https://id.atlassian.com/manage-profile/security/api-tokens)
- Access to a JSM-enabled JIRA instance
- Service desk agent or admin permissions

## 1. Environment Setup

```bash
# Install dependencies
pip install -r .claude/skills/shared/scripts/lib/requirements.txt

# Set environment variables
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

## 2. Verify Connection

```bash
# List all service desks to verify connectivity
python .claude/skills/jira-jsm/scripts/list_service_desks.py

# Expected output:
# ID  Key   Name              Project Key
# 1   ITS   IT Support        ITS
# 2   HR    HR Services       HR
```

## 3. Find Your Service Desk ID

Service desk IDs are numeric identifiers required by most scripts.

```bash
# List all service desks with their IDs
python list_service_desks.py

# Or get a specific service desk by project key
python get_service_desk.py --project-key ITS
```

**Tip**: Store frequently used IDs in environment variables:
```bash
export IT_SERVICE_DESK=1
export HR_SERVICE_DESK=2
```

## 4. List Request Types

Each service desk has specific request types (Incident, Service Request, Change, etc.):

```bash
# List request types for IT Support
python list_request_types.py --service-desk 1

# Example output:
# ID   Name                Description
# 10   Incident            Report a system issue
# 11   Service Request     Request IT services
# 12   Change Request      Request system changes
```

## 5. Create Your First Request

```bash
# Create an incident
python create_request.py \
  --service-desk 1 \
  --request-type 10 \
  --summary "Email service down" \
  --description "Cannot send or receive emails since 9am"

# Output: Created request SD-123
```

## 6. Track SLA Compliance

```bash
# Check SLA status
python get_sla.py SD-123

# Example output:
# Request: SD-123
# SLA: Time to First Response
#   Status: Completed
#   Goal: 4h
#   Elapsed: 45m
#
# SLA: Time to Resolution
#   Status: At Risk
#   Goal: 8h
#   Elapsed: 6h 30m
#   Remaining: 1h 30m
```

## 7. Manage Approvals

```bash
# List pending approvals
python list_pending_approvals.py --user self

# Approve a request
python approve_request.py SD-124 --comment "Approved for deployment"
```

## Common First Steps by Role

### Agent
1. Check your queue: `python get_queue_issues.py 500`
2. Claim a request: Use JIRA UI or jira-issue skill
3. Add first response: `python add_request_comment.py SD-123 --body "Looking into this"`
4. Monitor SLA: `python get_sla.py SD-123`

### Manager
1. Check SLA compliance: `python sla_report.py --service-desk 1`
2. Review pending approvals: `python list_pending_approvals.py --service-desk 1`
3. Identify breaches: `python check_sla_breach.py --service-desk 1`

### Administrator
1. List service desks: `python list_service_desks.py`
2. Review request types: `python list_request_types.py --service-desk 1`
3. Check queues: `python list_queues.py --service-desk 1`

## Troubleshooting First Run

### "Authentication failed"
```bash
# Verify your credentials
echo $JIRA_URL
echo $JIRA_EMAIL
echo $JIRA_API_TOKEN  # Should show your token
```

### "Service desk not found"
```bash
# List all available service desks
python list_service_desks.py
```

### "Permission denied"
- Verify you have agent or admin access to the service desk
- Check that your JIRA user is a member of the service desk project

## Next Steps

- **More examples**: See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) for 40+ examples
- **ITIL workflows**: See [ITIL_WORKFLOWS.md](ITIL_WORKFLOWS.md) for incident, change, problem management
- **Best practices**: See [BEST_PRACTICES.md](BEST_PRACTICES.md) for enterprise patterns
- **All scripts**: See [../SKILL.md](../SKILL.md) for complete script reference

---

*Last updated: December 2025*
