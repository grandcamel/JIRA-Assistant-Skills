---
name: "jira-service-management"
description: "Complete ITSM/ITIL workflow support for JSM - service desks, requests, SLAs, customers, approvals, knowledge base. Use when managing service desk requests, tracking SLAs, or handling customer operations."
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# jira-jsm

Complete ITSM (IT Service Management) and ITIL workflow support for Jira Service Management (JSM).

## When to use this skill

Use jira-jsm when you encounter:

### Problem Indicators
- Keywords: "SLA", "service level", "breach", "approval", "change request", "incident"
- Issue keys like: `SD-123`, `INC-456` (service desk format vs standard `PROJ-123`)
- Workflow needs: customer-facing requests, ITIL processes, service catalogs
- User questions about: incidents, problems, changes, service requests (not bugs/stories)

### Feature Triggers
- Need to track SLA compliance or generate SLA reports
- Managing approval workflows or CAB (Change Advisory Board) decisions
- Working with knowledge base integration for customer self-service
- Linking IT assets to requests or impact analysis
- Multi-tier support structure (agents, managers, customers)

### Integration Scenarios
- Created a request and want to update it: Use **jira-issue** for standard updates
- Transitioning through approval workflow: Use **jira-jsm** for JSM-specific transitions
- Searching for requests with complex criteria: Use **jira-search** for JQL

### NOT This Skill
- Creating bugs/stories in Agile: Use **jira-issue**
- Sprint planning or backlog management: Use **jira-agile**
- Developer workflow integration: Use **jira-dev**
- Standard issue lifecycle management: Use **jira-lifecycle**

**Still unsure?** Check the [decision tree](references/DECISION_TREE.md)

## What this skill does

**IMPORTANT:** Always use the `jira` CLI. Never run Python scripts directly.

This skill provides comprehensive JSM operations organized into 6 key ITSM capabilities:

| Capability | Description | Key Scripts |
|------------|-------------|-------------|
| **Service Desk Core** | Manage service desks, portals, request types | `list_service_desks.py`, `get_request_type_fields.py` |
| **Request Management** | Create and manage customer-facing requests | `create_request.py`, `get_request.py`, `transition_request.py` |
| **Customer & Organization** | Manage customers, organizations, participants | `create_customer.py`, `add_participant.py` |
| **SLA & Queue** | Track SLAs, manage queues | `get_sla.py`, `sla_report.py`, `list_queues.py` |
| **Comments & Approvals** | Collaboration and approval workflows | `add_request_comment.py`, `approve_request.py` |
| **Knowledge Base & Assets** | KB search, asset management | `search_kb.py`, `suggest_kb.py`, `create_asset.py` |

## Quick Start

```bash
# 1. List service desks to find your ID
jira jsm service-desk list

# 2. List request types for your service desk
jira jsm request-type list 1

# 3. Create an incident (both summary AND description are required)
jira jsm request create 1 10 --summary "Email service down" --description "Production email server is not responding to connections"

# 4. Check SLA status
jira jsm sla get SD-123

# 5. Add a comment to a request (body is positional, before flags)
jira jsm request comment SD-123 "Looking into this issue now"

# 6. Add an internal comment (agent-only, not visible to customers)
jira jsm request comment SD-123 "Escalating to Tier 2 support" --internal

# 7. Approve a pending request (issue_key, approval_id)
jira jsm approval approve SD-124 1001 --comment "Approved" --yes

# 8. Preview approval without executing (dry-run)
jira jsm approval approve SD-124 1001 --dry-run
```

For detailed setup instructions, see [docs/QUICK_START.md](docs/QUICK_START.md).

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

## Common Options

All scripts support these common options:

| Option | Description | Example |
|--------|-------------|---------|
| `--help` | Show help and exit | `jira <command> --help` |
| `--profile PROFILE` | Use specific JIRA profile | `--profile production` |
| `--output FORMAT` | Output format: text, json, table | `--output json` |
| `--service-desk ID` | Service desk ID (numeric) | `--service-desk 1` |

## Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Operation completed |
| 1 | General Error | Unspecified error |
| 2 | Validation Error | Invalid input parameters |
| 3 | Authentication Error | Invalid or expired API token |
| 4 | Permission Error | User lacks permissions |
| 5 | Not Found | Resource not found |
| 6 | Conflict Error | Duplicate or state conflict |
| 7 | Rate Limit Error | API limit exceeded |

## Configuration

### Environment Variables

```bash
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"

# Optional: Default service desk
export JSM_DEFAULT_SERVICE_DESK="1"
```

### Profile Support

```bash
# Use production profile
jira jsm request create 1 10 --summary "Issue" --profile prod
```

For full configuration options, see [references/CONFIG_REFERENCE.md](references/CONFIG_REFERENCE.md).

## Finding Service Desk IDs

Service desk IDs are numeric identifiers required by most scripts.

```bash
# Method 1: List all service desks
jira jsm service-desk list

# Method 2: Get details by ID
jira jsm service-desk get 1
```

**Tip**: Store frequently used IDs in environment variables:
```bash
export IT_SERVICE_DESK=1
export HR_SERVICE_DESK=2
```

## Integration with Other Skills

JSM requests (SD-* keys) are standard JIRA issues and work with all skills:

| Skill | Integration | Example |
|-------|-------------|---------|
| jira-issue | CRUD operations | Update priority, assignee, labels |
| jira-lifecycle | Workflow transitions | Transition through approval workflow |
| jira-search | Query and filter | Find high-priority incidents, SLA breaches |
| jira-relationships | Link requests | Link incident to problem |
| jira-collaborate | Comments, attachments | Add rich comments, attach files |

## Troubleshooting

### "Service desk not found"
```bash
jira jsm service-desk list  # Find correct ID
```

### "Authentication failed"
Verify environment variables and API token. See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

### "SLA information not available"
Verify SLA is configured in JSM project settings.

For all troubleshooting scenarios, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## License Requirements

| Tier | Features |
|------|----------|
| **JSM Standard** | Service desks, requests, customers, SLAs, approvals, queues, KB |
| **JSM Premium** | Advanced SLA reporting, change management, problem management, CMDB |
| **JSM Assets** | Asset management, discovery, linking (free for up to 100 assets) |

## Version Compatibility

- **JIRA Cloud**: Fully supported (primary target)
- **JIRA Data Center 9.0+**: Supported with minor differences
- **JIRA Data Center 8.x**: Partial support

For Data Center specifics, see [references/DATACENTER_GUIDE.md](references/DATACENTER_GUIDE.md).

## Detailed Documentation

| Topic | Location | When to Read |
|-------|----------|--------------|
| Getting started | [docs/QUICK_START.md](docs/QUICK_START.md) | First time using jira-jsm |
| Usage examples | [docs/USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md) | Looking for code examples |
| ITIL workflows | [docs/ITIL_WORKFLOWS.md](docs/ITIL_WORKFLOWS.md) | Incident/change/problem workflows |
| Troubleshooting | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Encountering errors |
| Best practices | [docs/BEST_PRACTICES.md](docs/BEST_PRACTICES.md) | Improve service desk operations |
| Rate limits | [references/RATE_LIMITS.md](references/RATE_LIMITS.md) | HTTP 429 errors |
| API reference | [references/API_REFERENCE.md](references/API_REFERENCE.md) | Building integrations |
| Configuration | [references/CONFIG_REFERENCE.md](references/CONFIG_REFERENCE.md) | Multi-instance setup |
| Decision tree | [references/DECISION_TREE.md](references/DECISION_TREE.md) | Choosing the right skill |

## Related Skills

- **jira-issue** - Standard issue CRUD operations
- **jira-lifecycle** - Workflow transitions and status management
- **jira-search** - JQL searches and filters
- **jira-collaborate** - Comments, attachments, watchers, notifications
- **jira-relationships** - Issue linking (incidents to problems)
- **shared** - Common utilities, authentication, error handling

## References

- [JSM Cloud REST API Documentation](https://developer.atlassian.com/cloud/jira/service-desk/rest/intro/)
- [JSM Assets REST API](https://developer.atlassian.com/cloud/insight/rest/intro/)
- [ITIL Framework](https://www.axelos.com/certifications/itil-service-management)

---

**Note**: All scripts support `--help` flag for detailed usage information.
