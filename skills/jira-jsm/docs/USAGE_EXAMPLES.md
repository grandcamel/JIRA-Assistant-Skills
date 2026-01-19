# JSM Usage Examples

**Quick Navigation**:
- Need to get started? See [QUICK_START.md](QUICK_START.md)
- Have an error? See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Want best practices? See [BEST_PRACTICES.md](BEST_PRACTICES.md)

---

Comprehensive examples organized by workflow category.

## Service Desk Operations

### List and Manage Service Desks

```bash
# List all service desks
python list_service_desks.py

# Create new service desk
python create_service_desk.py --project-key FAC --name "Facilities Services"

# Get service desk details
python get_service_desk.py --service-desk 1
python get_service_desk.py --project-key ITS  # By project key
```

### Request Types

```bash
# List request types for service desk
python list_request_types.py --service-desk 1

# Get request type details
python get_request_type.py --service-desk 1 --request-type 10

# Get custom fields for request type
python get_request_type_fields.py --service-desk 1 --request-type 10
```

---

## Request Management

### Creating Requests

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
```

### Managing Requests

```bash
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

---

## Customer Management

### Managing Customers

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
```

### Managing Participants (CC List)

```bash
# Add participants to request
python add_participant.py SD-123 --users "user1@example.com,user2@example.com"

# List participants
python get_participants.py SD-123

# Remove participant
python remove_participant.py SD-123 --users "user1@example.com"
```

---

## Organization Management

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

---

## SLA Monitoring

### Tracking SLA Status

```bash
# Get SLA information
python get_sla.py SD-123
python get_sla.py SD-123 --output json

# Get specific SLA metric
python get_sla.py SD-123 --sla-id 1

# Check for SLA breaches
python check_sla_breach.py SD-123
```

### SLA Reporting

```bash
# Generate SLA report
python sla_report.py --service-desk 1

# Report for specific date range
python sla_report.py --service-desk 1 \
  --start-date 2025-01-01 \
  --end-date 2025-01-31

# Report grouped by priority
python sla_report.py --service-desk 1 --group-by priority
```

Example output:
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
    - On Track: 34 (76%)

Average Resolution Time: 4h 35m
SLA Compliance: 94%
```

---

## Queue Management

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

---

## Comments and Approvals

### Adding Comments

```bash
# Add public comment (visible to customer) - default behavior
jira-as jsm request comment SD-123 "We're investigating the issue"

# Add internal comment (agent-only, not visible to customers)
jira-as jsm request comment SD-123 "Root cause: DNS server failure" --internal

# Get comments
jira-as jsm request comments SD-123
jira-as jsm request comments SD-123 --public-only
```

### Managing Approvals

```bash
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

---

## Knowledge Base

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

Example suggestion output:
```
Knowledge Base Suggestions for SD-123

1. How to Reset Your Password
   Confidence: 95%
   URL: https://example.atlassian.net/wiki/spaces/KB/pages/123

2. VPN Connection Troubleshooting
   Confidence: 87%
   URL: https://example.atlassian.net/wiki/spaces/KB/pages/456
```

---

## Asset Management (JSM Assets License)

### Managing Assets

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
```

### Linking Assets to Requests

```bash
# Link asset to request
python link_asset.py SD-123 --assets AST-123,AST-456

# Find affected assets
python find_affected_assets.py SD-123
```

---

## Integration with Other Skills

### jira-issue (Standard Issue Operations)

```bash
# Create request (jira-jsm)
python create_request.py --service-desk 1 --request-type 10 --summary "Issue"

# Update fields (jira-issue)
python update_issue.py SD-123 --priority Critical --assignee self

# Add labels (jira-issue)
python update_issue.py SD-123 --labels outage,network
```

### jira-lifecycle (Workflow Transitions)

```bash
# Get available transitions (jira-lifecycle)
python get_transitions.py SD-123

# Transition with comment (jira-lifecycle)
python transition_issue.py SD-123 --status "In Progress" \
  --comment "Started investigating"
```

### jira-search (JQL Queries)

```bash
# Find high-priority incidents (jira-search)
python jql_search.py "project=SD AND type='Service Request' AND priority=High"

# Find SLA-breached requests (jira-search)
python jql_search.py "project=SD AND 'Time to resolution' breached"

# Find requests in specific queue
python jql_search.py "project=SD AND status='Waiting for support'"
```

### jira-relationships (Issue Linking)

```bash
# Link incident to problem (jira-relationships)
python link_issues.py SD-100 SD-145 --type "relates to"

# Link change to problem (jira-relationships)
python link_issues.py SD-150 SD-145 --type "fixes"
```

### jira-collaborate (Comments and Attachments)

```bash
# Add rich formatted comment (jira-collaborate)
python add_comment.py SD-123 \
  --body "## Update\n- Fixed DNS\n- Verified connectivity" \
  --format markdown

# Upload attachments (jira-collaborate)
python upload_attachment.py SD-123 --file error-log.txt
```

---

## Bulk Operations Examples

### Processing Multiple Requests

```bash
# Add delays for bulk operations
for issue in SD-{100..200}; do
    python transition_request.py $issue --status "Resolved"
    sleep 0.5  # 500ms delay
done
```

### Pagination

```bash
# Limit results per request
python list_requests.py --service-desk 1 --max-results 50 --start 0
python list_requests.py --service-desk 1 --max-results 50 --start 50
```

---

*Last updated: December 2025*
