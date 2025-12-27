# Jira Service Management (JSM) Best Practices Guide

Comprehensive guide to Jira Service Management best practices for effective IT service management, ITIL compliance, and customer support excellence.

---

## Table of Contents

1. [JSM vs JIRA Software](#jsm-vs-jira-software)
2. [ITIL Process Implementation](#itil-process-implementation)
3. [Service Desk Setup](#service-desk-setup)
4. [Request Type Design](#request-type-design)
5. [SLA Configuration](#sla-configuration)
6. [Queue Management](#queue-management)
7. [Customer Portal Optimization](#customer-portal-optimization)
8. [Approval Workflows](#approval-workflows)
9. [Change Management](#change-management)
10. [Knowledge Base Integration](#knowledge-base-integration)
11. [Customer Communication](#customer-communication)
12. [Assets & CMDB](#assets--cmdb)
13. [Automation & Efficiency](#automation--efficiency)
14. [Common Pitfalls](#common-pitfalls)
15. [Quick Reference Card](#quick-reference-card)

---

## JSM vs JIRA Software

Understanding when to use JSM vs standard JIRA Software is critical for effective service management.

### Feature Comparison

| Aspect | JIRA Software | Jira Service Management |
|--------|---------------|-------------------------|
| **Primary Users** | Developers, internal teams | Customers, employees, external users |
| **Issue Types** | Epic, Story, Bug, Task, Subtask | Request, Incident, Problem, Change, Service Request |
| **Views** | Boards, backlog, sprints | Queues, portal, agent view, customer portal |
| **SLAs** | Not supported | Full SLA support (time to first response, resolution) |
| **Customer Access** | No dedicated portal | Customer portal with self-service |
| **Knowledge Base** | Manual linking | Native Confluence integration, AI suggestions |
| **Automation** | Basic workflow automation | Advanced ITSM automation with SLA triggers |
| **Approvals** | Not built-in | Native approval workflows, CAB support |
| **Queues** | Not available | Priority queues, SLA-based queues |
| **ITIL Processes** | Not designed for ITIL | Built for ITIL 4 (Incident, Problem, Change) |
| **Reporting** | Development metrics | Service metrics, SLA reports, CSAT |
| **Pricing** | Per user | Per agent (customers free) |

### When to Use Each

**Use JIRA Software when:**
- Managing software development projects
- Running Agile/Scrum sprints
- Tracking engineering work (stories, bugs, tasks)
- Internal team collaboration only
- No customer-facing requirements

**Use Jira Service Management when:**
- Managing IT support, help desk, or service requests
- Customer-facing support operations
- ITIL process compliance required (Incident, Problem, Change)
- SLA tracking and compliance needed
- Multi-tier support structures
- External user access required
- Self-service portal needed
- Approval workflows required (HR, finance, procurement)
- Service catalog management

**Hybrid Approach:**
Many organizations use both - JSM for customer-facing support and JIRA Software for internal development, linking issues across projects.

---

## ITIL Process Implementation

Jira Service Management is designed to align with ITIL 4 best practices. Here's how to implement core ITIL processes.

### Core ITIL Processes in JSM

| ITIL Process | JSM Implementation | Key Features |
|--------------|-------------------|--------------|
| **Incident Management** | Incident request type | SLAs, priority-based workflows, escalation |
| **Service Request Management** | Service Request type | Catalog, fulfillment workflows, approvals |
| **Problem Management** | Problem request type | Root cause analysis, linking to incidents |
| **Change Management** | Change request type | CAB approvals, risk assessment, change calendar |
| **Asset Management** | Assets/CMDB integration | Asset linking, impact analysis, CI tracking |
| **Knowledge Management** | Confluence integration | Article suggestions, self-service portal |

### Incident Management Best Practices

**Lifecycle:**
1. **Detection** - Customer reports or monitoring alert
2. **Logging** - Create incident with priority/impact
3. **Categorization** - Auto-assign based on type/component
4. **Prioritization** - P1 (Critical) to P4 (Low)
5. **Diagnosis** - Investigation, workaround identification
6. **Resolution** - Fix applied, tested, verified
7. **Closure** - Customer confirmation, documentation

**Implementation:**
```bash
# Create incident with priority
python create_request.py \
  --service-desk 1 \
  --request-type 10 \
  --summary "Email service outage affecting 500 users" \
  --description "## Impact\n- Users cannot send/receive email\n- Started: 09:30 AM\n- Affected: Engineering dept" \
  --field priority=Critical

# Link affected assets
python link_asset.py SD-123 --assets AST-456

# Monitor SLA
python get_sla.py SD-123

# Add resolution notes
python add_request_comment.py SD-123 \
  --body "## Resolution\nRestarted mail server, confirmed service restored" \
  --internal
```

### Problem Management Best Practices

**When to Create a Problem:**
- 3+ incidents with same root cause in 30 days
- Single high-impact incident affecting critical service
- Trend analysis reveals recurring issue pattern
- Proactive identification of potential failure

**Problem Workflow:**
1. **Problem Detection** - From incident trends or proactive analysis
2. **Problem Logging** - Document symptoms, affected CIs
3. **Investigation** - Root cause analysis (5 Whys, fishbone)
4. **Resolution** - Create change request for permanent fix
5. **Closure** - Verify fix prevents recurrence

**Linking Pattern:**
```
Problem SD-200
  ├─ Related Incidents: SD-100, SD-105, SD-112 (links)
  └─ Permanent Fix: Change SD-201 (implements)
```

### Change Management Best Practices

**Change Types:**

| Type | Approval Required | Examples | Risk |
|------|------------------|----------|------|
| **Standard** | Pre-approved (low risk) | Password reset, software install from catalog | Low |
| **Normal** | CAB review required | Database upgrade, network configuration | Medium-High |
| **Emergency** | Post-implementation review | Hotfix for critical outage | High (justified) |

**Change Workflow:**
```
Request → Risk Assessment → Approval → Scheduled → Implemented → Review → Closed
```

**CAB (Change Advisory Board):**
- Meet weekly for normal changes
- Use async approvals in JSM for minor changes
- Emergency changes: Post-implementation review

### Service Request Management

**Common Categories:**
- **Access & Permissions** - New account, access request, password reset
- **Equipment & Software** - Laptop provisioning, software license
- **Information** - Reports, documentation requests
- **HR Services** - Onboarding, offboarding, PTO

**Fulfillment Model:**
1. Request submission (customer portal or on-behalf-of)
2. Auto-routing to fulfillment team
3. Approval (if required)
4. Fulfillment tasks (subtasks for multi-step)
5. Asset creation/linking (if physical item)
6. Completion notification

---

## Service Desk Setup

### Initial Setup Checklist

- [ ] Create service desk for each support domain (IT, HR, Facilities)
- [ ] Define project key (3-4 letters, e.g., ITS, HRSD, FAC)
- [ ] Configure business hours calendar
- [ ] Set up customer portal branding (logo, colors)
- [ ] Create request types (start with 5-10 core types)
- [ ] Define SLA goals (at least 2: response + resolution)
- [ ] Configure queues (Unassigned, My Queue, Breaching Soon)
- [ ] Set up automation rules (auto-assignment, notifications)
- [ ] Integrate knowledge base (Confluence)
- [ ] Train agents on workflows

### Service Desk Naming Conventions

**Good:**
- IT Support (ITS)
- HR Services (HRSD)
- Facilities Management (FAC)
- Customer Support (CUST)

**Bad:**
- Helpdesk Project (vague)
- Team A (non-descriptive)
- TEMP-2025 (temporary-sounding)

### Multi-Service Desk Strategy

**When to Create Separate Service Desks:**
- Different customer bases (internal IT vs external customers)
- Different SLA requirements (dev vs production support)
- Different agent teams (IT vs HR vs Facilities)
- Different approval workflows (finance vs IT)

**When to Use Single Service Desk:**
- Same customer base
- Shared agent pool
- Similar SLA requirements
- Use request types to categorize instead

---

## Request Type Design

Request types define the customer experience. Design them from the customer's perspective, not your internal org structure.

### Request Type Principles

**DO:**
- Use action-oriented names: "Request new laptop", "Report system outage"
- Keep to 8-15 request types per service desk (avoid overwhelming customers)
- Group similar requests: Hardware (Laptop, Monitor, Phone)
- Use customer-friendly language: "Reset my password" not "Password reset ticket"
- Hide internal fields (team, component) from customer view

**DON'T:**
- Mirror IT org structure: "Network Team Request" (customer doesn't care)
- Use jargon: "P1 incident escalation" (use "Report urgent issue")
- Duplicate fields: Don't ask for info you already know
- Require excessive fields: 3-5 fields maximum on create

### Request Type to Issue Type Mapping

**Pattern 1: One-to-One**
```
Request Type: "Report a Bug" → Issue Type: "Bug"
```
Use when workflow is unique to that request.

**Pattern 2: Many-to-One (Recommended)**
```
Request Types:               Issue Type:
├─ Request laptop       →
├─ Request software     →    "Service Request"
└─ Request phone        →
```
Use when multiple requests share same workflow but need different forms.

**Pattern 3: One-to-Many**
```
Request Type: "IT Help" → Issue Types: Bug, Task, Service Request (based on routing rules)
```
Use for generic intake, then auto-convert based on automation.

### Field Configuration Best Practices

**Essential Fields (always required):**
- Summary (rename to "What do you need?" or "Describe the issue")
- Description (provide template with sections)

**Conditional Fields:**
- Priority (auto-set based on keywords, don't show to customers)
- Category/Type (use dropdown with 3-5 options)
- Affected Service (if multi-service environment)
- Urgency/Impact (calculate priority automatically: P = U × I)

**Hidden Fields (set via automation):**
- Team (route based on request type)
- Component (set based on category selection)
- Labels (add based on keywords in summary/description)

### Request Type Examples

**Good Request Type - "Request New Laptop":**
```
Name: Request New Laptop
Description: "For new hires or laptop replacement"

Fields shown:
- Employee Name (auto-filled if customer)
- Laptop Type: [MacBook Pro, MacBook Air, Dell XPS, ThinkPad]
- Reason: [New Hire, Replacement, Upgrade]
- Start Date: [Date picker]

Fields hidden (auto-set):
- Team: Hardware Procurement
- Priority: Low
- Components: Hardware, Laptop
```

**Good Request Type - "Report System Outage":**
```
Name: Report System Outage
Description: "System or service is completely unavailable"

Fields shown:
- Affected System: [Email, VPN, CRM, Network, Other]
- How many users affected: [Just me, 1-10, 10-50, 50+]
- Business impact: [Can't work, Reduced productivity, Minor inconvenience]

Fields hidden (auto-set):
- Priority: Critical (if "50+ users" or "Can't work")
- Team: NOC
- SLA: 15min response / 4hr resolution
```

---

## SLA Configuration

Service Level Agreements define commitments to customers. Configure them carefully to balance ambition with achievability.

### Standard SLA Goals

#### Time to First Response

Response time = Time from request creation to first agent comment

| Priority | Target | Use Case |
|----------|--------|----------|
| **Critical (P1)** | 15 minutes | System outage, security incident |
| **High (P2)** | 1 hour | Service degraded, multiple users affected |
| **Medium (P3)** | 4 hours | Single user issue, moderate impact |
| **Low (P4)** | 8 hours | Feature request, how-to question |

#### Time to Resolution

Resolution time = Time from request creation to resolution

| Priority | Target | Use Case |
|----------|--------|----------|
| **Critical (P1)** | 4 hours | Must restore service same business day |
| **High (P2)** | 8 hours | Fix by end of business day |
| **Medium (P3)** | 24 hours | Fix within 1 business day |
| **Low (P4)** | 72 hours | Fix within 3 business days |

**Note:** These are starting points. Adjust based on:
- Team capacity and staffing
- Historical resolution time data
- Customer expectations
- Industry standards for your domain

### SLA Configuration Checklist

- [ ] **Define business hours calendar**
  - Set working days (Mon-Fri typical)
  - Set working hours (9am-5pm or 24/7)
  - Add holidays (country-specific)
  - Consider time zones for global teams

- [ ] **Configure SLA goals**
  - Create "Time to First Response" SLA
  - Create "Time to Resolution" SLA
  - Set priority-based conditions
  - Attach calendar to each goal

- [ ] **Set pause conditions**
  - Pause when status = "Waiting for Customer"
  - Pause when status = "Waiting for Third Party"
  - Don't pause for internal waits (confuses SLA tracking)

- [ ] **Set stop conditions**
  - Stop when status = "Resolved"
  - Stop when status = "Closed"
  - Stop when resolution field is set

- [ ] **Configure escalations**
  - At 75% of goal: Add comment, notify assignee
  - At 90% of goal: Escalate to manager, increase priority
  - At 100% (breach): Notify senior leadership, create incident

### SLA Best Practices

**Start Conservative:**
Begin with achievable goals (e.g., 2hr response instead of 30min). You can tighten SLAs once you establish baseline performance.

**Use Business Hours, Not 24/7:**
Unless you have 24/7 staffing, use business hours calendars. A request submitted Friday 5pm starts counting Monday 9am.

**Pause Wisely:**
Only pause SLA when genuinely blocked:
- Waiting for customer response ✓
- Waiting for vendor support ✓
- Waiting for approval ✓
- Internal investigation (don't pause) ✗
- Waiting for another team (don't pause) ✗

**Priority-Based SLAs:**
Different request types and priorities need different SLAs:
```bash
# P1 Incident: 15min response, 4hr resolution
SLA Goal 1:
  Conditions: Type = Incident AND Priority = Critical
  Response: 15m
  Resolution: 4h
  Calendar: 24/7 (for critical issues)

# P3 Service Request: 4hr response, 24hr resolution
SLA Goal 2:
  Conditions: Type = Service Request AND Priority = Medium
  Response: 4h
  Resolution: 24h
  Calendar: Business Hours
```

**Monitor and Adjust:**
Review SLA performance monthly:
- Breach rate should be <5% (occasional breach OK)
- If breach rate >10%: SLAs are too aggressive or team understaffed
- If breach rate <1%: SLAs may be too conservative (tighten)

### Global Teams and Time Zones

**Challenge:** Customer in Sydney submits request at 9am local (3pm PST), but US-based SLA calendar counts non-working hours.

**Solutions:**

**Option 1: Regional Service Desks**
```
IT Support APAC (24/7 calendar)
IT Support EMEA (EMEA business hours)
IT Support Americas (Americas business hours)
```

**Option 2: Follow-the-Sun Calendars**
Single service desk, but SLA calendar = 24/5 or 24/7 to cover all regions.

**Option 3: Customer Location Field**
- Add "Customer Region" field to request type
- Use automation to set SLA calendar based on region
- Requires JSM Premium or custom automation

### SLA Reporting

**Key Metrics:**
- **SLA Compliance %** - Percentage of requests meeting SLA (target: >95%)
- **Average Response Time** - By priority, request type
- **Average Resolution Time** - Trend over time (should decrease)
- **Breach Analysis** - Top reasons for SLA breach

```bash
# Generate monthly SLA report
python sla_report.py \
  --service-desk 1 \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --group-by priority \
  --output table

# Find breaching requests
python check_sla_breach.py --service-desk 1 --status breached

# Find at-risk requests (75%+ of SLA elapsed)
python check_sla_breach.py --service-desk 1 --status at-risk
```

---

## Queue Management

Queues organize incoming requests for agent teams. Design queues around agent workflows, not org charts.

### Standard Queue Structure

Every service desk should have these core queues:

| Queue | JQL Filter | Purpose |
|-------|-----------|---------|
| **Unassigned** | `assignee IS EMPTY AND status != Resolved` | New requests needing triage |
| **My Open Requests** | `assignee = currentUser() AND status NOT IN (Resolved, Closed)` | Agent's active work |
| **Breaching Soon** | `"Time to resolution" < 1h AND status != Resolved` | SLA at risk |
| **Waiting for Customer** | `status = "Waiting for Customer"` | Requests paused, pending customer response |
| **Escalated** | `priority = Critical OR "Flagged" = Impediment` | Urgent attention needed |
| **Recently Resolved** | `resolved >= -7d` | For quality review, CSAT tracking |

### Priority-Based Queues

Organize queues by priority for focused triaging:

| Queue | JQL Filter |
|-------|-----------|
| **P1 - Critical** | `priority = Critical AND status NOT IN (Resolved, Closed)` |
| **P2 - High** | `priority = High AND status NOT IN (Resolved, Closed)` |
| **P3/P4 - Normal/Low** | `priority IN (Medium, Low) AND status NOT IN (Resolved, Closed)` |

### Team-Based Queues

For multi-team service desks:

| Queue | JQL Filter |
|-------|-----------|
| **Network Team** | `"Team" = Network AND status NOT IN (Resolved, Closed)` |
| **Applications Team** | `"Team" = Applications AND status NOT IN (Resolved, Closed)` |
| **Hardware Team** | `"Team" = Hardware AND status NOT IN (Resolved, Closed)` |

**Tip:** Use a custom "Team" field (single select) set via automation based on request type or component.

### SLA-Optimized Queues

| Queue | JQL Filter | Agent Action |
|-------|-----------|--------------|
| **Breaching Now** | `"Time to first response" breached OR "Time to resolution" breached` | Immediate response |
| **Next Hour Breach** | `"Time to resolution" < 1h AND "Time to resolution" > 0` | Urgent work |
| **Today Breach** | `"Time to resolution" < 8h AND "Time to resolution" > 1h` | Prioritize |
| **On Track** | `"Time to resolution" >= 8h` | Normal workflow |

### Queue Organization Strategies

**Flat Structure (Small Teams, <50 requests/day):**
```
├─ Unassigned
├─ My Requests
├─ Breaching Soon
└─ Waiting for Customer
```

**Grouped by Priority (Medium Teams, 50-200 requests/day):**
```
High Priority
  ├─ P1 Unassigned
  ├─ P1 In Progress
  └─ P1 Breaching

Normal Priority
  ├─ P2/P3 Unassigned
  └─ P2/P3 In Progress

My Work
  └─ My Open Requests
```

**Grouped by Team (Large Teams, 200+ requests/day):**
```
Network Team
  ├─ Network - Unassigned
  ├─ Network - Breaching
  └─ Network - In Progress

Applications Team
  ├─ Apps - Unassigned
  ├─ Apps - Breaching
  └─ Apps - In Progress

All Teams
  ├─ P1 Critical (all teams)
  └─ Waiting for Customer
```

### Queue Management Best Practices

**Limit Queue Count:**
Maximum 10-15 queues per service desk. Too many queues = decision paralysis.

**Sort Order Matters:**
Configure default sort for each queue:
- Unassigned: `"Time to first response" ASC` (oldest/most urgent first)
- My Requests: `priority DESC, updated ASC` (high priority, stale items)
- Breaching Soon: `"Time to resolution" ASC` (soonest to breach)

**Color Coding:**
Use queue icons/colors to indicate urgency:
- Red: Breaching, P1 Critical
- Orange: High priority, at risk
- Blue: Normal priority
- Gray: Waiting states

**Avoid Status-Based Queues:**
Don't create queues for every status (To Do, In Progress, etc.). Use board columns for status views. Queues should be for triage, assignment, and SLA management.

**Monitor Queue Depth:**
Set thresholds and alerts:
- Unassigned queue >20 items for >1 hour → Alert manager
- Breaching Soon queue >5 items → All-hands triage
- Individual agent queue >30 items → Rebalance workload

### Triage Process

**Daily Triage Workflow:**
1. **Check Breaching Soon queue** (5 min)
   - Reassign or escalate items at risk
   - Add comments to extend SLA if justified

2. **Review Unassigned queue** (10 min)
   - Assign based on expertise, workload
   - Set priority if not auto-assigned
   - Add first response (starts SLA)

3. **Check My Open Requests** (throughout day)
   - Work high priority first
   - Update requests idle >24hrs
   - Transition to "Waiting for Customer" if blocked

4. **End-of-day review** (5 min)
   - Close resolved requests
   - Hand off in-progress work if OOO tomorrow
   - Check Waiting for Customer queue for responses

---

## Customer Portal Optimization

The customer portal is the face of your service desk. Optimize it for self-service and ease of use.

### Portal Design Principles

**Prioritize Self-Service:**
80% of common issues should be solvable via knowledge base. Design portal to surface KB articles before showing "Submit Request" button.

**Simplify Navigation:**
Group request types into 3-5 categories max:
- Get Help (incidents, how-to)
- Request Something (access, hardware)
- Report an Issue (bugs, problems)

**Mobile-First:**
40% of requests come from mobile. Test portal on phone, ensure forms work on small screens.

**Branding Consistency:**
Portal should match company branding (logo, colors) to build trust and recognition.

### Knowledge Base Integration

**Confluence Integration:**
Link JSM to Confluence space for knowledge base:
1. Create Confluence space: "IT Support KB"
2. Organize with labels: `password`, `vpn`, `email`, `onboarding`
3. Enable "Suggest articles" in JSM portal settings
4. Articles appear when customer types in search/summary

**Article Structure:**
```markdown
Title: How to Reset Your Password

<!-- Use clear, customer-friendly titles -->

## When to use this
- Forgot password
- Password expired
- Account locked

## Steps
1. Go to https://password.company.com
2. Click "Forgot Password"
3. Enter your email address
4. Check email for reset link (expires in 1 hour)
5. Click link, set new password

## Need Help?
If these steps don't work, [submit a request](link-to-request-type).

Labels: password, account, access
```

**AI-Powered Suggestions:**
Use JSM's built-in article suggestions:
```bash
# Get KB suggestions for a request
python suggest_kb.py SD-123

# Agent can then link articles to request
python add_request_comment.py SD-123 \
  --body "See this knowledge base article: [Reset Password](https://kb.company.com/reset-password)"
```

### Request Type Grouping

**Good Grouping:**
```
Hardware & Equipment
  ├─ Request Laptop
  ├─ Request Monitor
  └─ Request Phone

Software & Access
  ├─ Request Software License
  ├─ Request System Access
  └─ Reset Password

Get Help
  ├─ Report System Outage
  ├─ Report Bug
  └─ Ask a Question
```

**Bad Grouping:**
```
Team A Requests   ← Customer doesn't know teams
Team B Requests
Urgent Issues     ← Urgency is subjective
Everything Else   ← Too vague
```

### Form Field Optimization

**Progressive Disclosure:**
Show fields conditionally based on previous selections:
```
Request Type: Request Software
  ↓
Software Name: [Dropdown: Adobe Creative Cloud, Microsoft Office, Slack, Other]
  ↓ (if "Other")
Specify Software: [Text field]
```

**Smart Defaults:**
Pre-fill fields when possible:
- Requester: Auto-filled from logged-in customer
- Location: Auto-filled from user profile
- Department: Auto-filled from organization

**Helpful Descriptions:**
Add field descriptions to guide customers:
```
Field: Business Justification
Description: "Explain how this software will help your work.
             Example: 'Need Figma for UI design work on Project Apollo.'"
```

### Portal Customization

**Branding:**
```
Logo: Company logo (200x50px recommended)
Theme Color: Match brand (hex color)
Banner: Optional hero image for portal homepage
Announcement Banner: For service outages, maintenance
```

**Custom Messages:**
- Welcome message: "Welcome to IT Support. How can we help?"
- Footer: Links to company policy, privacy, terms
- Confirmation message: "We've received your request. Expect a response within 4 hours."

**Multilingual Support:**
For global organizations:
- Translate request type names/descriptions
- Translate knowledge base articles
- Use Atlassian's language packs for UI

---

## Approval Workflows

Approvals are critical for change management, access requests, and procurement workflows.

### Approval Types

| Type | When to Use | Example |
|------|-------------|---------|
| **Single Approver** | Manager approval, simple requests | PTO request, password reset |
| **Any of Group** | Any member of team can approve | Any IT admin can approve software |
| **All of Group** | Unanimous consent required | All CAB members for change |
| **Hierarchical** | Multi-stage approval | Manager → Director → VP |

### CAB (Change Advisory Board) Setup

**CAB Membership:**
- Change Manager (chair)
- Technical SMEs (network, apps, security)
- Business representatives
- Customer advocate

**CAB Meetings:**
- **Frequency:** Weekly for normal changes, ad-hoc for emergency
- **Agenda:** Review upcoming changes, risk assessment, schedule
- **Quorum:** Minimum attendees to approve (e.g., 3 of 5)

**Automated CAB Workflow:**
```bash
# Create change request
python create_request.py \
  --service-desk 1 \
  --request-type 12 \
  --summary "Upgrade database to PostgreSQL 15" \
  --description "## Change Details\n- Scheduled: 2025-02-15 02:00 AM\n- Duration: 2 hours\n- Rollback plan: Attached" \
  --field priority=High

# Auto-adds CAB members as approvers (via automation)
# CAB receives notification

# Check approval status
python get_approvals.py SD-300

# CAB members approve
python approve_request.py SD-300 --comment "Approved. Risk assessment complete."

# After all approvals, status → "Scheduled"
# Change calendar shows scheduled window
```

### Approval Workflow Patterns

**Pattern 1: Pre-Approval for Standard Changes**
```
Standard Change (low risk, pre-approved process)
  ↓
Auto-Approve via Automation
  ↓
Implement
  ↓
Post-Implementation Review
```

**Pattern 2: Manager Approval**
```
Service Request (access, equipment)
  ↓
Requester's Manager Notified
  ↓
Manager Approves/Declines
  ↓ (if approved)
Fulfillment Team Implements
```

**Pattern 3: CAB Approval (Normal Change)**
```
Normal Change
  ↓
Peer Review (technical validation)
  ↓
CAB Review (all members)
  ↓ (if approved)
Schedule on Change Calendar
  ↓
Implement
  ↓
Post-Implementation Review
```

**Pattern 4: Emergency Change**
```
Emergency Change (P1 outage fix)
  ↓
Implement Immediately (no pre-approval)
  ↓
Document Actions Taken
  ↓
Post-Implementation CAB Review
```

### Approval Best Practices

**Set Approval Timeouts:**
Auto-escalate if approval pending >2 days:
```
Automation Rule:
  WHEN: Approval pending for 48 hours
  THEN:
    - Send reminder to approver
    - Notify approver's manager
    - Comment on issue: "Approval timeout approaching"
```

**Provide Context for Approvers:**
Include all relevant info in request:
- What is being changed/requested
- Why it's needed (business justification)
- Risk assessment
- Rollback plan (for changes)
- Cost (for procurement)

**Track Approval Bottlenecks:**
```bash
# Find pending approvals by approver
python list_pending_approvals.py --user john.doe@company.com

# Find pending approvals by service desk
python list_pending_approvals.py --service-desk 1

# Identify approval bottlenecks
python jql_search.py "status = 'Awaiting Approval' AND created < -7d"
```

**Delegate Approvals:**
Allow approvers to delegate when OOO:
```
Approver: Jane Smith
Delegate (when OOO): John Doe
```

**Approval Comments:**
Require comments when declining:
```bash
python decline_request.py SD-300 \
  --comment "Declined. Risk assessment incomplete. Please provide rollback plan."
```

---

## Change Management

Change management reduces risk of service disruption from changes to IT systems.

### Change Risk Assessment

**Risk Calculation:**
```
Risk = Impact × Likelihood

Impact Scale (1-5):
1 = Single user, minimal impact
2 = Small team, minor inconvenience
3 = Department, reduced productivity
4 = Company-wide, significant impact
5 = Critical service down, revenue loss

Likelihood Scale (1-5):
1 = Very unlikely to cause issues (<10%)
2 = Unlikely (10-30%)
3 = Possible (30-50%)
4 = Likely (50-70%)
5 = Very likely (>70%)

Risk Score:
1-5: Low Risk (standard change, auto-approve)
6-12: Medium Risk (normal change, CAB review)
13-25: High Risk (extensive testing, senior approval)
```

**Automated Risk Scoring:**
```bash
# Use automation to calculate risk
Automation Rule:
  WHEN: Change request created
  THEN:
    - Calculate risk score: Impact × Likelihood
    - IF risk ≤ 5: Set type = "Standard", Auto-approve
    - IF risk 6-12: Set type = "Normal", Request CAB approval
    - IF risk ≥ 13: Set type = "High Risk", Notify senior management
```

### Change Calendar

**Purpose:**
Visualize scheduled changes, prevent conflicts, communicate maintenance windows.

**Best Practices:**
- Block blackout periods (end-of-quarter, holidays)
- Enforce separation: No changes within 24hrs of each other on same system
- Color-code by risk: Red (high), Yellow (normal), Green (standard)
- Integrate with monitoring: Auto-create change when deployment detected

**Example Change Schedule:**
```
Week of Feb 10-16, 2025

Mon 10th: [Standard] Database backup schedule change (2am-3am)
Tue 11th: BLACKOUT - End of quarter freeze
Wed 12th: [Normal] Network switch upgrade Bldg A (10pm-12am) [CAB Approved]
Thu 13th: [Standard] SSL certificate renewal (automated)
Fri 14th: BLACKOUT - No changes on Friday
Sat 15th: [Normal] Email server migration (6am-10am) [CAB Approved]
Sun 16th: Available
```

### Change Review and Retrospective

**Post-Implementation Review (PIR):**
Within 7 days of change implementation:
- Was change successful? (Yes/No)
- Any issues encountered?
- Was rollback plan needed?
- Actual vs. estimated downtime
- Lessons learned

**Change Success Metrics:**
- **Change Success Rate** - % of changes implemented without issues (target: >95%)
- **Emergency Change %** - % of changes that are emergency (target: <5%)
- **Average Change Lead Time** - Days from request to implementation (track trend)
- **Change-Related Incidents** - Incidents caused by changes (target: minimize)

---

## Knowledge Base Integration

A robust knowledge base reduces ticket volume by 30-50% through self-service.

### Knowledge Base Structure

**Recommended Confluence Space Structure:**
```
IT Support Knowledge Base
├─ Getting Started
│   ├─ New Employee Onboarding
│   ├─ Account Setup Guide
│   └─ IT Policies
├─ Common Issues
│   ├─ Password & Account
│   │   ├─ Reset Password
│   │   ├─ Unlock Account
│   │   └─ MFA Setup
│   ├─ Email & Calendar
│   │   ├─ Email Not Syncing
│   │   ├─ Calendar Permissions
│   │   └─ Out of Office Setup
│   ├─ Network & VPN
│   │   ├─ VPN Connection Issues
│   │   ├─ WiFi Troubleshooting
│   │   └─ Remote Desktop Setup
│   └─ Applications
│       ├─ Software Installation Guide
│       ├─ License Activation
│       └─ Common App Errors
└─ How-To Guides
    ├─ Request Access to Systems
    ├─ Set Up New Phone
    └─ Provision New Employee
```

### Article Writing Best Practices

**Good Article Structure:**
```markdown
# [Clear, Action-Oriented Title]

**Last Updated:** 2025-01-15
**Applies To:** All employees / Windows users / Mac users

## When to use this guide
[Clear description of when this article is relevant]

## Before you start
[Prerequisites, requirements]

## Steps
1. [Specific, numbered steps with screenshots]
2. [One action per step]
3. [Include expected outcomes]

## Troubleshooting
**Problem:** [Common issue]
**Solution:** [How to fix]

## Still need help?
If these steps don't work, [submit a request](link).

---
Labels: password, account, access, windows
```

**Article Do's and Don'ts:**

**DO:**
- Use screenshots with annotations (arrows, highlights)
- Write in 2nd person ("You can...", "Click...")
- Test steps before publishing
- Update articles when processes change
- Track article views and helpfulness ratings

**DON'T:**
- Use jargon or acronyms without explanation
- Write walls of text (use bullets, headings)
- Link to external sites that may change/break
- Create duplicate articles (merge similar content)

### Article Suggestion Strategy

**Make Articles Discoverable:**
1. **Labels/Tags:** Tag articles with keywords customers search
2. **Portal Search:** Configure portal search to prioritize KB
3. **Related Articles:** Link related articles at bottom
4. **Suggested Articles:** JSM auto-suggests based on request summary

**Example:**
```
Customer types: "can't login to email"

Auto-suggested articles:
1. Reset Your Password (90% match)
2. Unlock Your Account (85% match)
3. MFA Troubleshooting (70% match)

Customer clicks article, problem solved = No ticket created ✓
```

### Linking KB to Requests

**Agent Workflow:**
```bash
# Agent receives request: "How do I set up VPN?"

# Search KB
python search_kb.py --query "VPN setup" --service-desk 1

# Get article details
python get_kb_article.py 1234567

# Add KB link to request comment
python add_request_comment.py SD-123 \
  --body "Please follow this guide: [VPN Setup Guide](https://kb.company.com/vpn-setup)"

# Resolve request (self-service via KB)
python transition_request.py SD-123 --status Resolved
```

### Knowledge-Centered Service (KCS)

**KCS Principles:**
1. **Capture:** Document solution while resolving issue
2. **Structure:** Use consistent article format
3. **Reuse:** Link to articles instead of retyping
4. **Improve:** Update articles based on feedback
5. **Measure:** Track KB usage, deflection rate

**KCS Workflow:**
```
1. Receive Request: "Outlook won't send email"
2. Investigate: Resolve issue (proxy settings incorrect)
3. Search KB: No article exists
4. Create Article: "Fix Outlook Proxy Settings"
5. Link Article: Add to request comment
6. Next Request: Same issue → Link to article (2 min resolution)
```

### KB Metrics

| Metric | Target | Meaning |
|--------|--------|---------|
| **Ticket Deflection Rate** | 30-50% | % of KB views that prevent ticket |
| **Article Views** | High for top 20 | Which articles are most used |
| **Article Rating** | >4.0/5.0 | Customer helpfulness rating |
| **Search Success Rate** | >70% | % of searches finding relevant article |
| **Coverage** | >80% | % of issues with KB article |

---

## Customer Communication

Clear, empathetic communication builds trust and improves customer satisfaction.

### Communication Principles

**Be Human:**
- Avoid corporate jargon: "We're on it!" not "Your request has been escalated to Tier 2."
- Show empathy: "I understand this is frustrating..."
- Use customer's name: "Hi Sarah," not "Dear customer"

**Be Clear:**
- Explain in simple terms, avoid technical jargon
- Set expectations: "I'll update you within 2 hours"
- Confirm understanding: "Does that make sense?"

**Be Proactive:**
- Update customers every 24 hours (even if no progress)
- Notify before SLA breach: "Still working on this, expect resolution by 3pm"
- Explain delays: "Waiting for vendor support, I'll follow up tomorrow"

### Comment Templates

**First Response:**
```
Hi [Name],

Thanks for reporting this. I'm looking into it now and will have an update for you within [timeframe].

In the meantime, here's a workaround you can try: [if applicable]

- [Agent Name]
```

**Progress Update:**
```
Hi [Name],

Quick update: [what's been done so far]

Next steps: [what happens next]

I'll keep you posted. Expected resolution: [timeframe or date]

- [Agent Name]
```

**Resolution:**
```
Hi [Name],

Good news! This has been resolved. [Brief explanation of fix]

Can you please confirm it's working on your end?

If you have any other issues, just let me know.

- [Agent Name]
```

**Escalation:**
```
Hi [Name],

I've escalated this to our [team/specialist] for deeper investigation.

They'll reach out to you directly within [timeframe]. Your request reference is [SD-123].

I'll continue monitoring and will follow up if needed.

- [Agent Name]
```

### Public vs. Internal Comments

**Public Comments (Customer Visible):**
- Use for customer communication
- Professional, friendly tone
- Avoid internal jargon or team names
- Include next steps and ETAs

**Internal Comments (Agent-Only):**
- Use for troubleshooting notes
- Technical details, root cause analysis
- Handoff notes between shifts/agents
- SLA justifications

```bash
# Public comment (customer sees this)
python add_request_comment.py SD-123 \
  --body "Hi Sarah, I've restarted the service and it should be working now. Please let me know if you still have issues."

# Internal comment (agents only)
python add_request_comment.py SD-123 \
  --body "Root cause: Apache maxClients reached. Increased from 150 to 300. Monitoring for 24hrs." \
  --internal
```

### Notification Strategy

**When to Notify:**
- Request created (confirmation to customer)
- First response (agent assigned, working on it)
- Status change (Waiting for Customer, Resolved)
- Before SLA breach (75%, 90%)
- Resolution (request closed)

**When NOT to Notify:**
- Internal status changes (Triaging → In Progress)
- Internal comments
- Every 5 minutes (avoid spam)

**Notification Channels:**
- Email (default)
- Slack/Teams (via integration)
- SMS (for P1 critical)

### CSAT (Customer Satisfaction)

**Post-Resolution Survey:**
```
Your request [SD-123] has been resolved.

How satisfied were you with the support you received?
☆ ☆ ☆ ☆ ☆ (1-5 stars)

What could we improve? [Optional text]
```

**CSAT Best Practices:**
- Send survey within 1 hour of resolution (while fresh)
- Keep it short (1-2 questions max)
- Act on feedback (review low ratings weekly)
- Target: >4.0/5.0 average CSAT

---

## Assets & CMDB

Assets (Configuration Management Database) track IT assets and their relationships.

### When to Use Assets

**Use Cases:**
- **Hardware Tracking:** Laptops, servers, network devices
- **Software Licenses:** Track assignments, renewals, compliance
- **Impact Analysis:** "If this server goes down, what's affected?"
- **Change Management:** "What assets are affected by this change?"
- **Incident Management:** "Link affected assets to incident"

**Requirements:**
- JSM Assets app (free for <100 assets, paid for more)
- Or CMDB app (JSM Premium)

### Asset Structure

**Object Schemas:**
Organize assets by type:
- Hardware (laptops, desktops, servers, network)
- Software (licenses, applications)
- Services (email, CRM, ERP)

**Object Types:**
```
Hardware Schema
├─ Laptop
├─ Desktop
├─ Server
├─ Network Switch
└─ Phone

Software Schema
├─ Software License
└─ Application

Services Schema
├─ Business Service (CRM, Email, ERP)
└─ Technical Service (Database, Web Server)
```

**Attributes:**
```
Laptop Object:
- Serial Number (text, unique)
- Manufacturer (Dropdown: Apple, Dell, Lenovo)
- Model (text)
- Owner (User)
- Purchase Date (date)
- Warranty Expiration (date)
- Status (Dropdown: In Use, In Stock, Retired)
- Location (text)
```

### Asset Lifecycle

**Procurement → Assignment → Maintenance → Retirement**

1. **Procurement:**
```bash
# Service request: "Request Laptop"
python create_request.py --service-desk 1 --request-type 11 --summary "New laptop for John Doe"

# Approved, ordered, received

# Create asset when laptop arrives
python create_asset.py \
  --object-schema 1 \
  --object-type Laptop \
  --name "MacBook Pro - John Doe" \
  --attributes '{"Serial": "C02XY123", "Owner": "john.doe@company.com", "Status": "In Stock"}'

# Link asset to request
python link_asset.py SD-123 --assets AST-456
```

2. **Assignment:**
```bash
# Update asset status when assigned
python update_asset.py AST-456 \
  --attributes '{"Status": "In Use", "Assigned Date": "2025-01-15"}'
```

3. **Maintenance:**
```bash
# Incident: "Laptop screen broken"
python create_request.py --service-desk 1 --request-type 10 --summary "Laptop screen cracked"

# Link asset to incident
python link_asset.py SD-200 --assets AST-456

# After repair, update asset
python update_asset.py AST-456 \
  --attributes '{"Last Service Date": "2025-02-01", "Notes": "Screen replaced"}'
```

4. **Retirement:**
```bash
# Update asset when employee leaves
python update_asset.py AST-456 \
  --attributes '{"Status": "Retired", "Retirement Date": "2025-12-01"}'
```

### Impact Analysis

**Asset Relationships:**
```
Business Service: Email
  ├─ Depends On: Email Server (AST-100)
  │   ├─ Depends On: Database Server (AST-101)
  │   └─ Depends On: Network Switch (AST-102)
  └─ Used By: 500 employees
```

**Impact Analysis Example:**
```bash
# Incident: "Email server down"
python create_request.py --service-desk 1 --request-type 10 --summary "Email service unavailable"

# Link affected asset
python link_asset.py SD-300 --assets AST-100

# Find all affected assets/services
python find_affected_assets.py SD-300

Output:
- Email Server (AST-100) - DOWN
  - Database Server (AST-101) - Impact: Degraded
  - Network Switch (AST-102) - Impact: None
  - Email Business Service - Impact: 500 users affected
```

### Asset Best Practices

**Keep Assets Up-to-Date:**
- Audit assets quarterly (verify location, ownership)
- Auto-update via integrations (Jamf for Macs, Intune for Windows)
- Use barcode/QR code scanning for physical audits

**Link Assets to Requests:**
- Incidents: Always link affected assets
- Changes: Link assets being modified
- Service Requests: Link provisioned assets

**Use Assets for Reporting:**
- Hardware refresh cycle (laptops >3 years old)
- License compliance (seats assigned vs. purchased)
- Cost allocation (by department, project)

---

## Automation & Efficiency

Automation reduces manual work, improves consistency, and speeds up service delivery.

### Common Automation Patterns

**Auto-Assignment:**
```
WHEN: Request created
IF: Request Type = "Network Issue"
THEN:
  - Set Team = "Network"
  - Assign to round-robin from Network Team
  - Add component = "Network"
```

**Auto-Prioritization:**
```
WHEN: Request created
IF: Summary contains "outage" OR "down" OR "critical"
THEN:
  - Set Priority = Critical
  - Add label = "urgent"
  - Send Slack notification to #incidents
```

**SLA Breach Warning:**
```
WHEN: Time to resolution < 1 hour
IF: Status != Resolved
THEN:
  - Add comment: "⚠️ SLA breach in 1 hour"
  - Send notification to assignee
  - Notify manager
```

**Auto-Escalation:**
```
WHEN: Priority = Critical
IF: Unassigned for 15 minutes
THEN:
  - Send notification to all agents
  - Create Slack message in #incidents
  - Notify on-call engineer (PagerDuty)
```

**Auto-Close Resolved Requests:**
```
WHEN: Status = Resolved for 3 days
IF: No customer response
THEN:
  - Add comment: "Auto-closing due to no response. Reopen if needed."
  - Transition to Closed
```

**Waiting for Customer Reminder:**
```
WHEN: Status = "Waiting for Customer" for 7 days
THEN:
  - Add comment: "Following up - do you still need help with this?"
  - Send email to customer
  - If no response after 3 more days → Auto-close
```

### Integration Automations

**Slack Integration:**
```
WHEN: P1 Incident created
THEN:
  - Post to #incidents: "🚨 P1 Incident: [Summary] - [Link]"
  - Create Slack channel: #incident-sd-123
  - Invite on-call team
```

**Email Parsing:**
```
WHEN: Email received at support@company.com
THEN:
  - Create request from email
  - Set summary = Email subject
  - Set description = Email body
  - Set customer = Email sender
  - Auto-assign based on subject keywords
```

**Monitoring Integration:**
```
WHEN: Monitoring alert received (via webhook)
THEN:
  - Create P1 Incident
  - Summary = Alert name
  - Description = Alert details, affected hosts
  - Link affected assets (servers)
  - Notify on-call team
```

### Automation Best Practices

**Start Simple:**
Begin with 3-5 core automations, add more as needed.

**Test in Non-Production First:**
Use staging service desk to test automation before deploying to production.

**Audit Automation Rules:**
Review quarterly - disable unused rules, optimize slow rules.

**Avoid Automation Loops:**
Don't create rules that trigger each other infinitely:
```
Bad:
Rule 1: WHEN Status = "In Progress" THEN Set Priority = High
Rule 2: WHEN Priority = High THEN Set Status = "In Progress"
(infinite loop!)
```

**Log Automation Actions:**
Add comments when automation acts:
```
THEN: Add comment: "Automation: Auto-assigned to Network Team based on request type"
```

---

## Common Pitfalls

Avoid these common mistakes when implementing JSM.

### Anti-Patterns to Avoid

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Too Many Request Types** | 50+ request types overwhelms customers | Keep to 8-15 per service desk, use groups |
| **Status Sprawl** | 15+ statuses confuses agents | Simplify workflow: To Do → In Progress → Resolved |
| **Unrealistic SLAs** | 15min response, 1hr resolution for all | Tier SLAs by priority, use business hours |
| **No Self-Service** | All questions become tickets | Build robust KB, integrate with portal |
| **Manual Triage** | Agents manually assign every request | Use automation to route by type/keywords |
| **Field Overload** | 20+ fields on request form | Show 3-5 fields, hide rest or use automation |
| **Ignoring SLA Breaches** | Breach rate >20%, no action | Review weekly, adjust SLAs or staffing |
| **No Customer Communication** | Requests go days without update | Auto-remind agents, set update frequency |
| **Agent as Admin** | Every agent has admin permissions | Role-based access: Agents, Managers, Admins |
| **No Change Control** | Changes made without approval | Enforce approval workflow for normal changes |

### Red Flags

**In Service Desk:**
- Unassigned queue >50 items for >2 hours
- SLA breach rate >10% for 2 consecutive weeks
- CSAT score <3.5/5.0 for 2 consecutive months
- Same customer submits >5 requests on same topic (KB gap)

**In Workflows:**
- Requests stuck in "Waiting for Approval" >7 days (approval bottleneck)
- >30% of requests bypassing workflow (manual status changes)
- Average resolution time increasing month-over-month (capacity issue)

**In Knowledge Base:**
- KB article search success rate <50%
- Top 10 request types have no KB articles
- KB articles not updated in >6 months (stale content)

### Migration Pitfalls

**Moving from Another Tool:**

**DON'T:**
- Migrate all historical tickets (migrate last 3-6 months only)
- Replicate old workflows exactly (take opportunity to simplify)
- Launch all service desks at once (pilot with 1 team first)

**DO:**
- Start fresh with simplified workflows
- Train agents before go-live (2 weeks of hands-on)
- Run parallel for 2 weeks (old + new system)
- Migrate knowledge base early (before requests)

---

## Quick Reference Card

### Essential JQL for JSM

```jql
# My open requests
assignee = currentUser() AND resolution IS EMPTY

# Unassigned requests
assignee IS EMPTY AND status != Resolved

# SLA breaching
"Time to resolution" breached OR "Time to first response" breached

# Waiting for customer response
status = "Waiting for Customer" AND updated < -7d

# High priority incidents
type = Incident AND priority IN (Critical, High) AND status != Resolved

# Pending approvals
approvals = pending()

# Recently resolved for QA review
resolved >= -24h
```

### Key Metrics to Track

| Metric | Target | Frequency |
|--------|--------|-----------|
| **SLA Compliance** | >95% | Daily |
| **First Contact Resolution** | >70% | Weekly |
| **Average Response Time** | <2 hours | Weekly |
| **Average Resolution Time** | <24 hours | Weekly |
| **CSAT Score** | >4.0/5.0 | Monthly |
| **Ticket Deflection (KB)** | >30% | Monthly |
| **Reopened Request Rate** | <5% | Monthly |
| **Agent Utilization** | 70-85% | Weekly |

### Keyboard Shortcuts (JSM Portal)

| Key | Action |
|-----|--------|
| `c` | Create request |
| `j/k` | Navigate requests |
| `o` | Open selected request |
| `i` | Assign to me |
| `a` | Assign to someone else |
| `m` | Add comment |
| `e` | Edit request |
| `/` | Search |
| `?` | Show shortcuts |

### Priority Matrix

Use impact + urgency to calculate priority:

|  | **High Urgency** | **Medium Urgency** | **Low Urgency** |
|--|------------------|-------------------|-----------------|
| **High Impact** | P1 Critical | P2 High | P2 High |
| **Medium Impact** | P2 High | P3 Medium | P3 Medium |
| **Low Impact** | P3 Medium | P4 Low | P4 Low |

**Impact:** Number of users affected or business criticality
**Urgency:** Time sensitivity or business need

### Agent Daily Checklist

**Morning (15 min):**
- [ ] Check Breaching Soon queue → Triage at-risk requests
- [ ] Review Unassigned queue → Assign to self or team
- [ ] Check My Open Requests → Prioritize work for day

**Throughout Day:**
- [ ] Respond to new assignments within 1 hour
- [ ] Update requests idle >24 hours
- [ ] Link KB articles when relevant
- [ ] Use internal comments for handoff notes

**End of Day (10 min):**
- [ ] Close resolved requests (confirm with customer)
- [ ] Update in-progress requests with status
- [ ] Hand off urgent items if OOO tomorrow
- [ ] Check Waiting for Customer queue for responses

### Common CLI Commands

```bash
# Create incident
python create_request.py --service-desk 1 --request-type 10 \
  --summary "Email service down" --field priority=Critical

# Check SLA status
python get_sla.py SD-123

# Add customer comment
python add_request_comment.py SD-123 --body "We're working on this now"

# Add internal note
python add_request_comment.py SD-123 --body "Root cause: DNS failure" --internal

# Approve change
python approve_request.py SD-456 --comment "Approved by CAB"

# Link asset to request
python link_asset.py SD-123 --assets AST-789

# Generate SLA report
python sla_report.py --service-desk 1 --start-date 2025-01-01 --end-date 2025-01-31
```

---

## Additional Resources

### Official Documentation
- [JSM Cloud Documentation](https://support.atlassian.com/jira-service-management-cloud/)
- [ITIL 4 Foundation](https://www.axelos.com/certifications/itil-service-management/itil-4-foundation)
- [JSM Assets REST API](https://developer.atlassian.com/cloud/insight/rest/intro/)

### Best Practice Sources
- [Atlassian JSM Best Practices](https://support.atlassian.com/jira-service-management-cloud/docs/best-practices-for-jira-service-management/)
- [ITSM Best Practices 2025](https://atlassian.empyra.com/blog/itsm-best-practices-with-jira-service-management-2025)
- [Jira Service Management Setup Guide](https://mgtechsoft.com/blog/jira-service-management-setup-best-practices/)
- [JSM Queue Management Guide](https://deviniti.com/blog/customer-it-service/jira-queue-management/)
- [SLA Configuration Best Practices](https://deviniti.com/blog/enterprise-software/jira-service-management-sla/)
- [Change Management Guide](https://support.atlassian.com/jira-service-management-cloud/docs/best-practices-for-change-management/)
- [Request Type Design](https://www.praecipio.com/resources/articles/jira-service-management-request-type-best-practices)
- [Customer Portal Optimization](https://www.refined.com/blog/jsm-support-sites-ux-best-practices)

### Community Resources
- [Atlassian Community - JSM](https://community.atlassian.com/t5/Jira-Service-Management/ct-p/jira-service-desk)
- [JSM Automation Library](https://community.atlassian.com/t5/Automation-articles/tkb-p/automation-articles)

---

*Last updated: December 2025*
