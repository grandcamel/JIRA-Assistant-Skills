# ITIL Workflows for JSM

**Quick Navigation**:
- Need to get started? See [QUICK_START.md](QUICK_START.md)
- Looking for examples? See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
- Want best practices? See [BEST_PRACTICES.md](BEST_PRACTICES.md)

---

Detailed ITIL process implementations using jira-jsm scripts.

## Overview

Jira Service Management aligns with ITIL 4 best practices:

| ITIL Process | JSM Implementation | Key Scripts |
|--------------|-------------------|-------------|
| Incident Management | Incident request type | `create_request.py`, `get_sla.py`, `transition_request.py` |
| Service Request | Service Request type | `create_request.py`, `approve_request.py` |
| Problem Management | Problem request type | `link_asset.py`, `add_request_comment.py` |
| Change Management | Change request type | `get_approvals.py`, `approve_request.py` |

---

## Incident Management

Complete incident lifecycle from creation to resolution.

### Lifecycle

1. **Detection** - Customer reports or monitoring alert
2. **Logging** - Create incident with priority/impact
3. **Categorization** - Auto-assign based on type/component
4. **Prioritization** - P1 (Critical) to P4 (Low)
5. **Diagnosis** - Investigation, workaround identification
6. **Resolution** - Fix applied, tested, verified
7. **Closure** - Customer confirmation, documentation

### Implementation

```bash
# 1. Customer reports incident
python create_request.py \
  --service-desk 1 \
  --request-type 10 \
  --summary "Cannot access shared drive" \
  --description "Error: Network path not found" \
  --field priority=High

# Output: Created SD-125

# 2. Auto-assign via queue or manually assign (use jira-issue skill)

# 3. Agent adds internal note
python add_request_comment.py SD-125 \
  --body "Checking network connectivity" \
  --internal

# 4. Add public update for customer
python add_request_comment.py SD-125 \
  --body "Our team is investigating. Expected resolution: 2 hours"

# 5. Link affected assets
python link_asset.py SD-125 --assets AST-789

# 6. Monitor SLA
python get_sla.py SD-125

# 7. Suggest knowledge base articles
python suggest_kb.py SD-125

# 8. Transition to resolved
python transition_request.py SD-125 --status Resolved

# 9. Verify SLA compliance
python check_sla_breach.py SD-125
```

### Priority Matrix

| Impact/Urgency | High Urgency | Medium Urgency | Low Urgency |
|----------------|--------------|----------------|-------------|
| High Impact | P1 Critical | P2 High | P2 High |
| Medium Impact | P2 High | P3 Medium | P3 Medium |
| Low Impact | P3 Medium | P4 Low | P4 Low |

---

## Service Request Fulfillment

### Lifecycle

1. Request submission (customer portal or on-behalf-of)
2. Auto-routing to fulfillment team
3. Approval (if required)
4. Fulfillment tasks (subtasks for multi-step)
5. Asset creation/linking (if physical item)
6. Completion notification

### Implementation

```bash
# 1. Create service request (new laptop)
python create_request.py \
  --service-desk 1 \
  --request-type 11 \
  --summary "New laptop for new hire" \
  --description "Start date: 2025-02-01\nName: Jane Smith"

# Output: Created SD-130

# 2. Request requires approval
python get_approvals.py SD-130

# 3. Manager approves
python approve_request.py SD-130 \
  --comment "Approved. Standard MacBook Pro configuration."

# 4. Procurement team adds participants
python add_participant.py SD-130 --users "procurement@example.com"

# 5. Create asset when laptop received
python create_asset.py \
  --object-schema 1 \
  --object-type Laptop \
  --name "MacBook Pro - Jane Smith" \
  --attributes '{"Serial": "C02XY456FVH7", "Owner": "jane.smith@example.com"}'

# 6. Link asset to request
python link_asset.py SD-130 --assets AST-200

# 7. Complete request
python transition_request.py SD-130 --status Completed
```

---

## Change Management

### Change Types

| Type | Approval | Examples | Risk |
|------|----------|----------|------|
| Standard | Pre-approved | Password reset, catalog software | Low |
| Normal | CAB review | Database upgrade, network config | Medium-High |
| Emergency | Post-review | Hotfix for critical outage | High (justified) |

### Change Workflow

```
Request -> Risk Assessment -> Approval -> Scheduled -> Implemented -> Review -> Closed
```

### Implementation

```bash
# 1. Submit change request
python create_request.py \
  --service-desk 1 \
  --request-type 12 \
  --summary "Database upgrade to PostgreSQL 15" \
  --description "## Change Details\n- Scheduled: 2025-02-15 02:00-04:00\n- Impact: 2hr downtime" \
  --field priority=Critical

# Output: Created SD-140

# 2. Add CAB (Change Advisory Board) as participants
python add_participant.py SD-140 \
  --users "cab-manager@example.com,tech-lead@example.com,ops-manager@example.com"

# 3. Monitor approval status
python get_approvals.py SD-140

# List pending approvals for CAB members
python list_pending_approvals.py --service-desk 1

# 4. CAB members approve
python approve_request.py SD-140 --comment "Approved. Risk assessment completed."

# 5. Link affected assets
python find_affected_assets.py SD-140
python link_asset.py SD-140 --assets AST-300,AST-301

# 6. Implement change
python transition_request.py SD-140 --status "In Progress"

# 7. Add implementation notes
python add_request_comment.py SD-140 \
  --body "## Implementation Log\n- 02:00: Backup completed\n- 02:15: Upgrade started" \
  --internal

# 8. Complete change
python transition_request.py SD-140 --status Completed
```

### Risk Assessment

```
Risk = Impact x Likelihood

Impact (1-5):
1 = Single user, minimal impact
2 = Small team, minor inconvenience
3 = Department, reduced productivity
4 = Company-wide, significant impact
5 = Critical service down, revenue loss

Likelihood (1-5):
1 = Very unlikely (<10%)
3 = Possible (30-50%)
5 = Very likely (>70%)

Risk Score:
1-5: Low (standard change)
6-12: Medium (normal change, CAB review)
13-25: High (extensive testing, senior approval)
```

---

## Problem Management

### When to Create a Problem

- 3+ incidents with same root cause in 30 days
- Single high-impact incident affecting critical service
- Trend analysis reveals recurring issue pattern
- Proactive identification of potential failure

### Problem Workflow

1. **Problem Detection** - From incident trends or proactive analysis
2. **Problem Logging** - Document symptoms, affected CIs
3. **Investigation** - Root cause analysis (5 Whys, fishbone)
4. **Resolution** - Create change request for permanent fix
5. **Closure** - Verify fix prevents recurrence

### Linking Pattern

```
Problem SD-200
  +-- Related Incidents: SD-100, SD-105, SD-112 (links)
  +-- Permanent Fix: Change SD-201 (implements)
```

### Implementation

```bash
# 1. Create problem record from recurring incidents
python create_request.py \
  --service-desk 1 \
  --request-type 13 \
  --summary "Root Cause: Intermittent network outages Building A" \
  --description "## Related Incidents\n- SD-100, SD-105, SD-112, SD-120"

# 2. Link related incidents (use jira-relationships skill)

# 3. Add analysis notes
python add_request_comment.py SD-145 \
  --body "## Analysis\nSwitch in closet 3A showing packet loss" \
  --internal

# 4. Find affected assets
python find_affected_assets.py SD-145

# 5. Create change request for permanent fix
python create_request.py \
  --service-desk 1 \
  --request-type 12 \
  --summary "Replace network switch Building A closet 3A" \
  --description "Permanent fix for problem SD-145"

# 6. Link problem to change (use jira-relationships skill)

# 7. Close problem after change implemented
python transition_request.py SD-145 --status Closed
```

---

## SLA Configuration for ITIL

### Standard SLA Goals

#### Time to First Response

| Priority | Target | Use Case |
|----------|--------|----------|
| Critical (P1) | 15 minutes | System outage, security incident |
| High (P2) | 1 hour | Service degraded, multiple users |
| Medium (P3) | 4 hours | Single user issue |
| Low (P4) | 8 hours | Feature request, how-to |

#### Time to Resolution

| Priority | Target | Use Case |
|----------|--------|----------|
| Critical (P1) | 4 hours | Restore service same day |
| High (P2) | 8 hours | Fix by end of business day |
| Medium (P3) | 24 hours | Fix within 1 business day |
| Low (P4) | 72 hours | Fix within 3 business days |

### SLA Monitoring

```bash
# Check SLA status for request
python get_sla.py SD-123

# Check for breaches across service desk
python check_sla_breach.py --service-desk 1

# Generate SLA compliance report
python sla_report.py --service-desk 1 \
  --start-date 2025-01-01 \
  --end-date 2025-01-31
```

---

## Knowledge Base Integration

### KCS (Knowledge-Centered Service) Workflow

1. **Receive Request**: "Outlook won't send email"
2. **Investigate**: Resolve issue (proxy settings incorrect)
3. **Search KB**: No article exists
4. **Create Article**: "Fix Outlook Proxy Settings"
5. **Link Article**: Add to request comment
6. **Next Request**: Same issue -> Link to article (2 min resolution)

### Using KB in Workflows

```bash
# Search for existing articles
python search_kb.py --query "VPN setup" --service-desk 1

# Get AI-powered suggestions for request
python suggest_kb.py SD-123

# Add KB link to request comment
python add_request_comment.py SD-123 \
  --body "Please follow this guide: [VPN Setup Guide](https://kb.company.com/vpn-setup)"
```

---

## Automation Patterns

### Common ITIL Automations

**Auto-Assignment (Incident)**:
```
WHEN: Request created
IF: Request Type = "Incident"
THEN: Assign to round-robin from Support Team
```

**SLA Breach Warning**:
```
WHEN: Time to resolution < 1 hour
IF: Status != Resolved
THEN: Add comment, notify assignee, notify manager
```

**Auto-Close Resolved**:
```
WHEN: Status = Resolved for 3 days
IF: No customer response
THEN: Add comment, transition to Closed
```

**Emergency Change Notification**:
```
WHEN: Change created
IF: Priority = Critical
THEN: Notify all CAB members, create Slack channel
```

---

*Last updated: December 2025*
