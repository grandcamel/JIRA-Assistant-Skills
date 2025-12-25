---
name: jira-jsm
version: 1.0.0
description: Complete ITSM/ITIL workflow support for Jira Service Management
category: jira
tags: [jsm, itsm, itil, service-desk, sla, approvals, customers, assets, knowledge-base]
author: Claude Code
requires:
  - jira-issue
  - shared
---

# jira-jsm

Complete ITSM (IT Service Management) and ITIL workflow support for Jira Service Management (JSM).

## When to use this skill

Use this skill when you need to:
- Create and manage service desk requests (incidents, service requests, changes)
- Track and monitor SLA compliance and breach detection
- Manage customers, organizations, and participants
- Handle approval workflows (approve/decline requests)
- Work with queues and request types
- Link and manage IT assets (requires JSM Assets license)
- Search and suggest knowledge base articles
- Implement ITIL processes (Incident, Problem, Change, Service Request Management)

**JSM vs Standard JIRA**: Use jira-jsm for service desk operations (customer-facing requests, SLAs, approvals). Use jira-issue for standard issue CRUD operations (create, update, delete).

## What this skill does

This skill provides comprehensive JSM operations organized into key ITSM capabilities:

### 1. Service Desk Core

Manage JSM service desks and portals:
- **Create Service Desks**: Initialize new service desks for different teams
- **List Service Desks**: View all available service desks
- **Get Service Desk Details**: Retrieve metadata, portal settings, and configuration
- **Request Types**: List available request types (Incident, Service Request, Change)
- **Request Type Fields**: Get custom fields for specific request types

### 2. Request Management

Create and manage customer-facing service requests:
- **Create Requests**: Submit new incidents, service requests, or changes
  - Support for request-type-specific fields
  - On-behalf-of customer creation
  - Participant management from creation
- **Get Request Details**: View request status, fields, and metadata
- **Get Request Status**: Track request lifecycle and current state
- **Transition Requests**: Move requests through workflow states
- **List Requests**: View all requests for a service desk with filtering

### 3. Customer & Organization Management

Manage service desk customers and organizational structure:
- **Create Customers**: Add users as service desk customers
- **List Customers**: View all customers for a service desk
- **Add Customers**: Associate existing users with service desks
- **Remove Customers**: Disassociate customers from service desks
- **Create Organizations**: Define customer organizations (departments, companies)
- **List Organizations**: View all organizations
- **Get Organization Details**: Retrieve organization metadata and members
- **Delete Organizations**: Remove organizations
- **Add to Organization**: Associate customers with organizations
- **Remove from Organization**: Disassociate customers from organizations
- **Participants**: Manage request participants (CC list)
  - Add participants to requests
  - Remove participants
  - List all participants

### 4. SLA & Queue Management

Track service level agreements and manage queues:
- **Get SLA Information**: View SLA metrics for requests
  - Time to first response
  - Time to resolution
  - Remaining time and breach warnings
- **Check SLA Breach**: Detect SLA violations and at-risk requests
- **SLA Reporting**: Generate SLA compliance reports
- **List Queues**: View all queues for a service desk
- **Get Queue Details**: Retrieve queue configuration
- **Get Queue Issues**: View requests in specific queues with JQL filtering

### 5. Comments & Approvals

Collaboration and approval workflows:
- **Add Request Comments**: Comment on requests
  - Public comments (visible to customers)
  - Internal comments (agent-only visibility)
- **Get Request Comments**: View comment history with filtering
- **Approval Management**: Handle approval workflows
  - Get approval status for requests
  - List pending approvals (by user or service desk)
  - Approve requests with comments
  - Decline requests with reasons

### 6. Knowledge Base & Assets

Knowledge management and asset tracking:
- **Knowledge Base**:
  - Search knowledge base articles
  - Get article details
  - Suggest articles for requests (AI-powered)
- **Assets** (requires JSM Assets/Insight license):
  - Create assets (laptops, servers, licenses)
  - List assets by object schema
  - Get asset details
  - Update asset attributes
  - Link assets to requests
  - Find affected assets for requests

## Available Scripts (45 total)

### Service Desk Core (6 scripts)
- `create_service_desk.py` - Create new service desk
- `list_service_desks.py` - List all service desks
- `get_service_desk.py` - Get service desk details
- `list_request_types.py` - List available request types
- `get_request_type.py` - Get request type details
- `get_request_type_fields.py` - Get custom fields for request type

### Request Management (5 scripts)
- `create_request.py` - Create service request
- `get_request.py` - Get request details
- `get_request_status.py` - Get request status/lifecycle
- `transition_request.py` - Transition request through workflow
- `list_requests.py` - List requests with filtering

### Customer Management (7 scripts)
- `create_customer.py` - Create new customer
- `list_customers.py` - List service desk customers
- `add_customer.py` - Add customer to service desk
- `remove_customer.py` - Remove customer from service desk
- `add_participant.py` - Add participant to request
- `remove_participant.py` - Remove participant from request
- `get_participants.py` - List request participants

### Organization Management (6 scripts)
- `create_organization.py` - Create customer organization
- `list_organizations.py` - List all organizations
- `get_organization.py` - Get organization details
- `delete_organization.py` - Delete organization
- `add_to_organization.py` - Add customer to organization
- `remove_from_organization.py` - Remove customer from organization

### SLA & Queue Management (6 scripts)
- `get_sla.py` - Get SLA information for request
- `check_sla_breach.py` - Check for SLA breaches
- `sla_report.py` - Generate SLA compliance report
- `list_queues.py` - List service desk queues
- `get_queue.py` - Get queue details
- `get_queue_issues.py` - Get requests in queue

### Comments & Approvals (6 scripts)
- `add_request_comment.py` - Add comment to request
- `get_request_comments.py` - Get request comments
- `get_approvals.py` - Get approval status for request
- `list_pending_approvals.py` - List pending approvals
- `approve_request.py` - Approve request
- `decline_request.py` - Decline request

### Knowledge Base & Assets (9 scripts)
- `search_kb.py` - Search knowledge base articles
- `get_kb_article.py` - Get knowledge base article
- `suggest_kb.py` - Get KB article suggestions for request
- `create_asset.py` - Create new asset
- `list_assets.py` - List assets
- `get_asset.py` - Get asset details
- `update_asset.py` - Update asset attributes
- `link_asset.py` - Link asset to request
- `find_affected_assets.py` - Find assets affected by request

## Quick Start (5 minutes)

### 1. List Available Service Desks
```bash
# View all service desks
python list_service_desks.py

# Example output:
# ID  Key   Name          Project Key
# 1   ITS   IT Support    ITS
# 2   HR    HR Services   HR
# 3   FAC   Facilities    FAC
```

### 2. View Request Types
```bash
# List request types for IT Support
python list_request_types.py --service-desk 1

# Example output:
# ID   Name                Description
# 10   Incident            Report a system issue
# 11   Service Request     Request IT services
# 12   Change Request      Request system changes
```

### 3. Create Your First Request
```bash
# Create an incident
python create_request.py \
  --service-desk 1 \
  --request-type 10 \
  --summary "Email service down" \
  --description "Cannot send or receive emails since 9am"

# Output: Created request SD-123
```

### 4. Track SLA Compliance
```bash
# Check SLA status
python get_sla.py SD-123

# Example output:
# Request: SD-123
# SLA: Time to First Response
#   Status: ✓ Completed
#   Goal: 4h
#   Elapsed: 45m
#   Remaining: N/A
#
# SLA: Time to Resolution
#   Status: ⚠ At Risk
#   Goal: 8h
#   Elapsed: 6h 30m
#   Remaining: 1h 30m
```

### 5. Manage Approvals
```bash
# List pending approvals
python list_pending_approvals.py --user self

# Approve a request
python approve_request.py SD-124 --comment "Approved for deployment"
```

## Usage Examples

### Service Desk Operations

```bash
# Create new service desk
python create_service_desk.py --project-key FAC --name "Facilities Services"

# Get service desk details
python get_service_desk.py --service-desk 1
python get_service_desk.py --project-key ITS  # By project key

# List request types
python list_request_types.py --service-desk 1

# Get request type fields
python get_request_type_fields.py --service-desk 1 --request-type 10
```

### Creating and Managing Requests

```bash
# Create basic incident
python create_request.py \
  --service-desk 1 \
  --request-type 10 \
  --summary "Network outage in Building A"

# Create with description and priority
python create_request.py \
  --service-desk 1 \
  --request-type 10 \
  --summary "VPN connection failing" \
  --description "## Issue\nCannot connect to VPN since morning" \
  --field priority=High

# Create on behalf of customer
python create_request.py \
  --service-desk 1 \
  --request-type 11 \
  --summary "New laptop request" \
  --on-behalf-of user@example.com

# Get request details
python get_request.py SD-123
python get_request.py SD-123 --output json

# Get request status
python get_request_status.py SD-123

# Transition request
python transition_request.py SD-123 --status "In Progress"

# List all requests
python list_requests.py --service-desk 1
python list_requests.py --service-desk 1 --filter "status='Waiting for support'"
```

### Customer Management

```bash
# Create customer
python create_customer.py \
  --service-desk 1 \
  --email user@example.com \
  --name "John Doe"

# List customers
python list_customers.py --service-desk 1
python list_customers.py --service-desk 1 --filter "john"

# Add existing user as customer
python add_customer.py --service-desk 1 --user user@example.com

# Remove customer
python remove_customer.py --service-desk 1 --user user@example.com

# Manage participants (CC list)
python add_participant.py SD-123 --users "user1@example.com,user2@example.com"
python get_participants.py SD-123
python remove_participant.py SD-123 --users "user1@example.com"
```

### Organization Management

```bash
# Create organization
python create_organization.py --service-desk 1 --name "Engineering Team"

# List organizations
python list_organizations.py --service-desk 1

# Get organization details
python get_organization.py 100

# Add customers to organization
python add_to_organization.py \
  --organization 100 \
  --users "user1@example.com,user2@example.com"

# Remove from organization
python remove_from_organization.py \
  --organization 100 \
  --users "user1@example.com"

# Delete organization
python delete_organization.py 100
```

### SLA Monitoring

```bash
# Get SLA information
python get_sla.py SD-123
python get_sla.py SD-123 --output json

# Get specific SLA metric
python get_sla.py SD-123 --sla-id 1

# Check for SLA breaches
python check_sla_breach.py SD-123

# Generate SLA report
python sla_report.py --service-desk 1
python sla_report.py --service-desk 1 --start-date 2025-01-01 --end-date 2025-01-31
python sla_report.py --service-desk 1 --group-by priority
```

Example SLA report output:
```
SLA Report: IT Support (Jan 2025)
Total Requests: 145

By Priority:
  Critical: 12 requests
    - Breached: 1 (8%)
    - At Risk: 2 (17%)
    - On Track: 9 (75%)
  High: 45 requests
    - Breached: 3 (7%)
    - At Risk: 8 (18%)
    - On Track: 34 (76%)
  Medium: 88 requests
    - Breached: 5 (6%)
    - At Risk: 12 (14%)
    - On Track: 71 (81%)

Average Resolution Time: 4h 35m
SLA Compliance: 94%
```

### Queue Management

```bash
# List queues
python list_queues.py --service-desk 1

# Get queue details
python get_queue.py 500

# Get issues in queue
python get_queue_issues.py 500
python get_queue_issues.py 500 --max-results 50
python get_queue_issues.py 500 --filter "priority=High"
```

### Comments and Approvals

```bash
# Add public comment (visible to customer)
python add_request_comment.py SD-123 --body "We're investigating the issue"

# Add internal comment (agent-only)
python add_request_comment.py SD-123 \
  --body "Root cause: DNS server failure" \
  --internal

# Get comments
python get_request_comments.py SD-123
python get_request_comments.py SD-123 --public-only
python get_request_comments.py SD-123 --internal-only

# Get approval status
python get_approvals.py SD-124

# List pending approvals
python list_pending_approvals.py --user self
python list_pending_approvals.py --service-desk 1

# Approve request
python approve_request.py SD-124 --comment "Approved for production deployment"

# Decline request
python decline_request.py SD-124 --comment "Insufficient budget allocation"
```

### Knowledge Base

```bash
# Search knowledge base
python search_kb.py --query "password reset"
python search_kb.py --query "VPN" --service-desk 1

# Get article details
python get_kb_article.py 1234567

# Get AI-powered article suggestions for request
python suggest_kb.py SD-123
python suggest_kb.py SD-123 --max-results 5
```

Example KB suggestion output:
```
Knowledge Base Suggestions for SD-123

1. How to Reset Your Password
   Confidence: 95%
   URL: https://example.atlassian.net/wiki/spaces/KB/pages/123

2. VPN Connection Troubleshooting
   Confidence: 87%
   URL: https://example.atlassian.net/wiki/spaces/KB/pages/456

3. Common Network Issues
   Confidence: 72%
   URL: https://example.atlassian.net/wiki/spaces/KB/pages/789
```

### Asset Management (requires JSM Assets license)

```bash
# Create asset
python create_asset.py \
  --object-schema 1 \
  --object-type Laptop \
  --name "MacBook Pro M3" \
  --attributes '{"Serial Number": "C02XY123FVH6", "Owner": "john.doe@example.com"}'

# List assets
python list_assets.py --object-schema 1
python list_assets.py --object-schema 1 --object-type Laptop

# Get asset details
python get_asset.py AST-123

# Update asset
python update_asset.py AST-123 \
  --attributes '{"Status": "In Use", "Location": "Office 3A"}'

# Link asset to request
python link_asset.py SD-123 --assets AST-123,AST-456

# Find affected assets
python find_affected_assets.py SD-123
```

## Common ITIL Workflows

### Incident Management

Complete incident lifecycle from creation to resolution:

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

### Service Request Fulfillment

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

### Change Management with Approvals

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

### Problem Management

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

## Integration with Other Skills

### jira-issue
Standard issue operations for JSM requests:
```bash
# Create request (jira-jsm)
python create_request.py --service-desk 1 --request-type 10 --summary "Issue"

# Update fields (jira-issue)
python update_issue.py SD-123 --priority Critical --assignee self

# Add labels (jira-issue)
python update_issue.py SD-123 --labels outage,network
```

### jira-lifecycle
Workflow transitions for JSM requests:
```bash
# Get available transitions (jira-lifecycle)
python get_transitions.py SD-123

# Transition with comment (jira-lifecycle)
python transition_issue.py SD-123 --status "In Progress" \
  --comment "Started investigating"
```

### jira-search
Find JSM requests with JQL:
```bash
# Find high-priority incidents (jira-search)
python jql_search.py "project=SD AND type='Service Request' AND priority=High"

# Find SLA-breached requests (jira-search)
python jql_search.py "project=SD AND 'Time to resolution' breached"

# Find requests in specific queue
python jql_search.py "project=SD AND status='Waiting for support'"
```

### jira-relationships
Link JSM requests:
```bash
# Link incident to problem (jira-relationships)
python link_issues.py SD-100 SD-145 --type "relates to"

# Link change to problem (jira-relationships)
python link_issues.py SD-150 SD-145 --type "fixes"
```

### jira-collaborate
Advanced collaboration features:
```bash
# Add rich formatted comment (jira-collaborate)
python add_comment.py SD-123 \
  --body "## Update\n- Fixed DNS\n- Verified connectivity" \
  --format markdown

# Notify specific users (jira-collaborate)
python send_notification.py SD-123 \
  --users "manager@example.com" \
  --subject "Request Completed" \
  --body "Your request has been resolved"

# Upload attachments (jira-collaborate)
python upload_attachment.py SD-123 --file error-log.txt
```

## Configuration

### Settings Files
JSM scripts use shared configuration from:
- `.claude/settings.json` - Global settings
- `.claude/settings.local.json` - Local overrides (gitignored)

### Environment Variables
```bash
# JIRA connection
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"

# Optional: Default service desk
export JSM_DEFAULT_SERVICE_DESK="1"
```

### Profile Support
All scripts support `--profile` flag for managing multiple JIRA instances:
```bash
# Use production profile
python create_request.py --profile prod --service-desk 1 --request-type 10 --summary "Issue"

# Use staging profile
python create_request.py --profile staging --service-desk 1 --request-type 10 --summary "Test"
```

## JSM API Endpoints Reference

### Service Desk APIs
- `GET /rest/servicedeskapi/servicedesk` - List service desks
- `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}` - Get service desk
- `POST /rest/servicedeskapi/servicedesk` - Create service desk

### Request APIs
- `POST /rest/servicedeskapi/request` - Create request
- `GET /rest/servicedeskapi/request/{issueKey}` - Get request
- `GET /rest/servicedeskapi/request/{issueKey}/status` - Get request status
- `POST /rest/servicedeskapi/request/{issueKey}/transition` - Transition request

### Customer APIs
- `POST /rest/servicedeskapi/servicedesk/{serviceDeskId}/customer` - Add customer
- `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/customer` - List customers
- `DELETE /rest/servicedeskapi/servicedesk/{serviceDeskId}/customer` - Remove customer

### Organization APIs
- `POST /rest/servicedeskapi/organization` - Create organization
- `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/organization` - List organizations
- `POST /rest/servicedeskapi/organization/{organizationId}/user` - Add user to org

### SLA APIs
- `GET /rest/servicedeskapi/request/{issueKey}/sla` - Get SLA information
- `GET /rest/servicedeskapi/request/{issueKey}/sla/{slaId}` - Get specific SLA

### Approval APIs
- `GET /rest/servicedeskapi/request/{issueKey}/approval` - Get approvals
- `POST /rest/servicedeskapi/request/{issueKey}/approval/{approvalId}` - Approve/decline

### Queue APIs
- `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/queue` - List queues
- `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/queue/{queueId}/issue` - Get queue issues

### Assets APIs (requires JSM Assets/Insight license)
- `POST /rest/insight/1.0/object/create` - Create asset
- `GET /rest/insight/1.0/object/{objectId}` - Get asset
- `PUT /rest/insight/1.0/object/{objectId}` - Update asset

## Troubleshooting

### "Service desk not found"
**Problem**: Service desk ID or key is incorrect
**Solution**:
```bash
# List all service desks to find correct ID
python list_service_desks.py
```

### "Request type not found"
**Problem**: Request type ID doesn't exist for service desk
**Solution**:
```bash
# List request types for service desk
python list_request_types.py --service-desk 1
```

### "Customer does not have permission"
**Problem**: User is not a customer of the service desk
**Solution**:
```bash
# Add user as customer first
python add_customer.py --service-desk 1 --user user@example.com
```

### "SLA information not available"
**Problem**: Request doesn't have SLA configured or SLA feature disabled
**Solution**:
- Verify SLA is configured in JSM project settings
- Check request type has SLA goals defined
- Ensure JSM license includes SLA features

### "Assets API not available" (403 Forbidden)
**Problem**: JSM Assets/Insight app not installed or licensed
**Solution**:
- Install "Assets - For Jira Service Management" app from Atlassian Marketplace
- Verify Assets license is active
- Alternative: Use standard JIRA custom fields for asset tracking

### "Approval not found"
**Problem**: Request doesn't have approval workflow configured
**Solution**:
- Verify request type has approval step in workflow
- Check automation rules for approval creation
- Manually add approvers if needed

### Cloud vs Data Center API Differences

**JSM Cloud** (this implementation):
- Uses `/rest/servicedeskapi/*` endpoints
- Customer management via email addresses
- Assets require separate "Assets - For JSM" app

**JSM Data Center**:
- Some endpoints differ (e.g., `/rest/servicedesk/1/*`)
- Customer management may use usernames instead of email
- Assets/Insight may be built-in depending on version

**Migration tip**: When moving between Cloud and Data Center, update:
1. API endpoint paths in shared library
2. Customer/user identifier format (email vs username)
3. Assets API endpoints if using built-in Insight

## Best Practices

### 1. SLA Management
- Monitor SLA compliance regularly with `sla_report.py`
- Set up alerts for at-risk requests using `check_sla_breach.py`
- Use queues to prioritize SLA-critical requests

### 2. Customer Experience
- Always add meaningful comments when transitioning requests
- Use public comments for customer communication
- Use internal comments for agent collaboration
- Suggest knowledge base articles to help customers self-serve

### 3. Approval Workflows
- Add all approvers as participants for visibility
- Include clear justification in approval requests
- Use `list_pending_approvals.py` to track approval bottlenecks

### 4. Asset Management
- Link assets to requests for complete audit trail
- Keep asset attributes up-to-date
- Use `find_affected_assets.py` for impact analysis

### 5. Organization Structure
- Group customers by department/team using organizations
- Use organizations for bulk notifications
- Maintain organization membership regularly

## Performance Tips

### Bulk Operations
```bash
# Add multiple participants at once
python add_participant.py SD-123 --users "user1@example.com,user2@example.com,user3@example.com"

# Link multiple assets
python link_asset.py SD-123 --assets AST-1,AST-2,AST-3

# Filter large result sets
python list_requests.py --service-desk 1 --filter "created >= -7d"
```

### Pagination
```bash
# Limit results for better performance
python list_customers.py --service-desk 1 --max-results 50

# Use start index for pagination
python list_customers.py --service-desk 1 --start 50 --max-results 50
```

### Caching
```bash
# Cache service desk and request type lookups
# Store frequently used IDs in environment variables
export ITS_SERVICE_DESK=1
export INCIDENT_REQUEST_TYPE=10

python create_request.py \
  --service-desk $ITS_SERVICE_DESK \
  --request-type $INCIDENT_REQUEST_TYPE \
  --summary "Issue"
```

## Related Skills

- **jira-issue** - Standard issue CRUD operations
- **jira-lifecycle** - Workflow transitions and status management
- **jira-search** - JQL searches and filters
- **jira-collaborate** - Comments, attachments, watchers, notifications
- **jira-relationships** - Issue linking (incidents to problems, changes to problems)
- **shared** - Common utilities, authentication, error handling, formatters

## License Requirements

### JSM Features by License Tier

**JSM Standard** (included):
- Service desks and portals
- Request management
- Customers and organizations
- SLA tracking
- Basic approvals
- Queues
- Knowledge base integration

**JSM Premium** (additional):
- Advanced SLA reporting
- Enhanced approval workflows
- Change management workflows
- Problem management
- CMDB integration

**JSM Assets/Insight** (separate app):
- Asset and configuration management
- Asset discovery
- Asset linking to requests
- Impact analysis
- Note: Free for up to 100 assets in Cloud

## Version Compatibility

- **JIRA Cloud**: Fully supported (primary target)
- **JIRA Data Center 9.0+**: Supported with minor API endpoint differences
- **JIRA Data Center 8.x**: Partial support (some JSM APIs may differ)

## References

- [JSM Cloud REST API Documentation](https://developer.atlassian.com/cloud/jira/service-desk/rest/intro/)
- [JSM Assets REST API](https://developer.atlassian.com/cloud/insight/rest/intro/)
- [ITIL Framework](https://www.axelos.com/certifications/itil-service-management)
- [JSM Automation Rules](https://support.atlassian.com/jira-service-management-cloud/docs/automation-rules/)

---

**Note**: All scripts support `--help` flag for detailed usage information and parameter descriptions.
