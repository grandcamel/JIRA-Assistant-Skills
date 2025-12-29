# JIRA Service Management Workflows

**Use this guide when:** Managing customer requests, tracking incidents, implementing ITIL processes.

**Not for:** Standard JIRA software workflows (see [workflow_guide.md](workflow_guide.md)).

**Prerequisites:** JIRA Service Management license.

**Audience:** Service desk agents, SRE teams, IT operations.

---

## Overview

JIRA Service Management extends JIRA with specialized workflows for IT service management, customer support, and other service desk scenarios.

## Request Workflow

The standard JSM request workflow for customer-facing service requests.

### States

```
Waiting for support → In progress → Waiting for customer → Resolved → Closed
         ↓                ↓                  ↓                 ↓
         └──────────────────────────────────┴─────────────────→ Cancelled
```

**Status Descriptions:**

- **Waiting for support** - Request received, awaiting agent action
- **In progress** - Agent actively working on request
- **Waiting for customer** - Pending customer response
- **Resolved** - Solution provided, awaiting customer confirmation
- **Closed** - Request completed and confirmed
- **Cancelled** - Request cancelled

### Common Transitions

| From | To | Transition Name | Notes |
|------|----|----|-------|
| Waiting for support | In progress | Start Progress | Agent starts work |
| In progress | Waiting for customer | Request feedback | Needs customer input |
| Waiting for customer | In progress | Resume | Customer responded |
| In progress | Resolved | Resolve | Mark as resolved |
| Resolved | Closed | Close | Auto or manual |
| Resolved | In progress | Reopen | Issue not resolved |
| Any | Cancelled | Cancel | Request cancelled |

### Working with Requests

```bash
# Start working on a request
python transition_issue.py REQ-123 --name "In progress"

# Request customer feedback
python transition_issue.py REQ-123 --name "Waiting for customer" \
  --comment "Please provide additional information"

# Resolve request
python resolve_issue.py REQ-123 --resolution "Done" \
  --comment "Issue resolved by restarting service"

# Close resolved request
python transition_issue.py REQ-123 --name "Closed"
```

## Incident Management Workflow

For managing incidents and outages.

### States

```
Open → In progress → Pending → Resolved → Closed
  ↓         ↓          ↓          ↓
  └─────────┴──────────┴──────────→ Cancelled
```

**Status Descriptions:**

- **Open** - Incident reported
- **In progress** - Investigation or fix in progress
- **Pending** - Waiting for external factor
- **Resolved** - Incident resolved
- **Closed** - Incident closed and documented
- **Cancelled** - False alarm or duplicate

### Priority and Severity

Incidents typically use priority and severity fields:

**Priority Values:**
- **Critical** (P1) - Complete outage, immediate response
- **High** (P2) - Significant impact, respond quickly
- **Medium** (P3) - Moderate impact, standard response
- **Low** (P4) - Minor impact, can wait

**Severity Levels:**
- **SEV1** - Critical business impact
- **SEV2** - Major functionality affected
- **SEV3** - Minor functionality affected
- **SEV4** - Cosmetic or low impact

### Managing Incidents

```bash
# Create critical incident
python create_issue.py --project INC --type Incident \
  --summary "Production database down" \
  --priority Critical \
  --custom-fields '{"customfield_10050": {"value": "SEV1"}}'

# Start incident response
python transition_issue.py INC-456 --name "In progress" \
  --comment "War room established, investigating root cause"

# Resolve incident
python resolve_issue.py INC-456 --resolution "Fixed" \
  --comment "Database cluster restored, monitoring for stability"
```

## Problem Management Workflow

For tracking and resolving underlying problems that cause incidents.

### States

```
New → Investigating → Known Error → Resolved → Closed
 ↓         ↓             ↓            ↓
 └─────────┴─────────────┴────────────→ Rejected
```

**Status Descriptions:**

- **New** - Problem identified
- **Investigating** - Root cause analysis in progress
- **Known Error** - Root cause identified, workaround available
- **Resolved** - Permanent solution implemented
- **Closed** - Problem closed
- **Rejected** - Not a real problem

### Problem Records

```bash
# Create problem record
python create_issue.py --project PROB --type Problem \
  --summary "Intermittent authentication failures" \
  --description "Multiple incidents (INC-100, INC-105) suggest underlying authentication issue"

# Move to Known Error
python transition_issue.py PROB-789 --name "Known Error" \
  --comment "Root cause: Token expiry not handled correctly. Workaround: Manual re-authentication" \
  --custom-fields '{"customfield_10060": "Restart authentication service"}'
```

## Change Management Workflow

For managing changes to IT infrastructure.

### States

```
Requested → Reviewing → Awaiting approval → Approved → Scheduled → Implementing → Done
     ↓          ↓              ↓              ↓          ↓            ↓
     └──────────┴──────────────┴──────────────┴──────────┴────────────→ Rejected/Cancelled
```

**Status Descriptions:**

- **Requested** - Change request submitted
- **Reviewing** - Change being reviewed
- **Awaiting approval** - Pending CAB/management approval
- **Approved** - Change approved, pending schedule
- **Scheduled** - Change scheduled for implementation
- **Implementing** - Change being implemented
- **Done** - Change completed successfully
- **Rejected** - Change request denied
- **Cancelled** - Change cancelled

### Change Requests

```bash
# Create change request
python create_issue.py --project CHG --type Change \
  --summary "Upgrade production database to v14" \
  --description "Scheduled maintenance window: Saturday 2AM-6AM" \
  --custom-fields '{"customfield_10070": "2024-02-10T02:00:00.000Z"}'

# Approve change
python transition_issue.py CHG-321 --name "Approved" \
  --comment "Approved by CAB on 2024-01-15"

# Complete change
python resolve_issue.py CHG-321 --resolution "Done" \
  --comment "Upgrade completed successfully, all systems operational"
```

## SLA Management

JSM workflows often include SLA (Service Level Agreement) tracking.

### SLA Fields

Common SLA-related custom fields:
- **Time to First Response** - Maximum time for initial response
- **Time to Resolution** - Maximum time to resolve
- **Breach Time** - When SLA will be breached

### Viewing SLA Status

SLA status is typically visible in the issue view and tracked automatically by JSM.

```bash
# Get issue with SLA fields
python get_issue.py REQ-123 --fields "customfield_10100,customfield_10101" --detailed
```

### SLA Best Practices

1. **Respond Quickly** - Update status to show work has started
2. **Add Comments** - Comments stop SLA clocks in some configurations
3. **Use Priorities** - Set correct priority to trigger appropriate SLA
4. **Monitor Breaches** - Use search to find issues approaching SLA breach

## Customer Communication

### Internal vs. Customer Comments

JSM supports internal comments (visible only to agents) and public comments (visible to customers).

```bash
# Add public comment (visible to customer)
python add_comment.py REQ-123 --body "We've identified the issue and are working on a fix"

# Internal comments require JSM-specific API (not covered by basic scripts)
```

### Request Participants

JSM requests track:
- **Reporter** - Customer who submitted request
- **Request participants** - Additional customers involved
- **Assignee** - Agent working on request
- **Organizations** - Customer organizations

## Automation Rules

JSM often includes automation rules that affect workflows:

### Common Automations

- **Auto-assign** - Requests automatically assigned based on criteria
- **Auto-resolve** - Requests auto-resolved after X days in "Waiting for customer"
- **Auto-close** - Resolved requests auto-closed after X days
- **Escalation** - Automatic escalation when SLA approaches breach

These automations affect workflow transitions and may override manual actions.

## Custom Workflows in JSM

Organizations often customize JSM workflows:

### Viewing Your Workflow

```bash
# Check available transitions to understand your workflow
python get_transitions.py REQ-123
```

### Common Customizations

- **Additional approval steps** - Manager approval, CAB approval
- **Specialized statuses** - "Awaiting vendor", "Scheduled maintenance"
- **Multiple resolution states** - Separate paths for different outcomes
- **Integration transitions** - Triggers for external systems

## Best Practices for JSM

1. **Use Request Types**
   - Create requests with appropriate type
   - Types determine workflow and fields

2. **Maintain SLAs**
   - Respond within SLA windows
   - Use correct priorities
   - Update status to reflect progress

3. **Communicate with Customers**
   - Add comments when status changes
   - Explain delays or issues
   - Confirm resolution

4. **Link Related Issues**
   - Link incidents to problems
   - Link changes to incidents
   - Track related requests

5. **Resolution Discipline**
   - Always set appropriate resolution
   - Add resolution comments
   - Close requests properly

## Troubleshooting JSM Workflows

### Can't Transition Request

**Problem:** Transition not available

**Common Causes:**
- Request type has different workflow
- User role doesn't have permission
- SLA or automation locked status

**Solution:**
```bash
# Check available transitions
python get_transitions.py REQ-123

# Contact JSM admin if needed
```

### Auto-transitions Overriding

**Problem:** Status changes automatically after manual transition

**Cause:** Automation rule is triggering

**Solution:**
- Review automation rules with JSM admin
- Adjust automation conditions
- May need to disable specific rules

### SLA Already Breached

**Problem:** Cannot resolve request, SLA breached

**Action:**
- Resolve anyway, document reason for breach
- Add detailed comment explaining delay
- Follow up with management if needed

## Resources

- [JSM Workflows Documentation](https://support.atlassian.com/jira-service-management-cloud/docs/configure-workflows/)
- [ITIL and JSM](https://www.atlassian.com/itsm/jira-service-management/itil)
- [SLA Documentation](https://support.atlassian.com/jira-service-management-cloud/docs/configure-slas/)
- [Automation Rules](https://support.atlassian.com/cloud-automation/docs/jira-automation/)
