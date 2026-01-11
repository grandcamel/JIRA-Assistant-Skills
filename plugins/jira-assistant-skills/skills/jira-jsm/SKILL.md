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

**IMPORTANT:** Always use the `jira-as` CLI. Never run Python scripts directly.

This skill provides comprehensive JSM operations organized into 6 key ITSM capabilities:

| Capability | Description | Key Commands |
|------------|-------------|--------------|
| **Service Desk Core** | Manage service desks, portals, request types | `jira-as jsm service-desk list`, `jira-as jsm request-type fields` |
| **Request Management** | Create and manage customer-facing requests | `jira-as jsm request create`, `jira-as jsm request get`, `jira-as jsm request transition` |
| **Customer & Organization** | Manage customers, organizations, participants | `jira-as jsm customer create`, `jira-as jsm participant add` |
| **SLA & Queue** | Track SLAs, manage queues | `jira-as jsm sla get`, `jira-as jsm sla report`, `jira-as jsm queue list` |
| **Comments & Approvals** | Collaboration and approval workflows | `jira-as jsm request comment`, `jira-as jsm approval approve` |
| **Knowledge Base & Assets** | KB search, asset management | `jira-as jsm kb search`, `jira-as jsm kb suggest`, `jira-as jsm asset create` |

## Quick Start

```bash
# 1. List service desks to find your ID
jira-as jsm service-desk list

# 2. List request types for your service desk
jira-as jsm request-type list 1

# 3. Create an incident (both summary AND description are required)
jira-as jsm request create 1 10 --summary "Email service down" --description "Production email server is not responding to connections"

# 4. Check SLA status
jira-as jsm sla get SD-123

# 5. Add a comment to a request (body is positional, before flags)
jira-as jsm request comment SD-123 "Looking into this issue now"

# 6. Add an internal comment (agent-only, not visible to customers)
jira-as jsm request comment SD-123 "Escalating to Tier 2 support" --internal

# 7. Approve a pending request (issue_key, approval_id)
jira-as jsm approval approve SD-124 1001 --comment "Approved" --yes

# 8. Preview approval without executing (dry-run)
jira-as jsm approval approve SD-124 1001 --dry-run
```

For detailed setup instructions, see [docs/QUICK_START.md](docs/QUICK_START.md).

## Available Commands

All commands support `--help` for full documentation.

### Service Desk Core
| Command | Description |
|---------|-------------|
| `jira-as jsm service-desk create` | Create new service desk |
| `jira-as jsm service-desk list` | List all service desks |
| `jira-as jsm service-desk get` | Get service desk details |
| `jira-as jsm request-type list` | List available request types |
| `jira-as jsm request-type get` | Get request type details |
| `jira-as jsm request-type fields` | Get custom fields for request type |

### Request Management
| Command | Description |
|---------|-------------|
| `jira-as jsm request create` | Create service request |
| `jira-as jsm request get` | Get request details |
| `jira-as jsm request status` | Get request status/lifecycle |
| `jira-as jsm request transition` | Transition request through workflow |
| `jira-as jsm request list` | List requests with filtering |

### Customer Management
| Command | Description |
|---------|-------------|
| `jira-as jsm customer create` | Create new customer |
| `jira-as jsm customer list` | List service desk customers |
| `jira-as jsm customer add` | Add customer to service desk |
| `jira-as jsm customer remove` | Remove customer from service desk |
| `jira-as jsm participant add` | Add participant to request |
| `jira-as jsm participant remove` | Remove participant from request |
| `jira-as jsm participant list` | List request participants |

### Organization Management
| Command | Description |
|---------|-------------|
| `jira-as jsm organization create` | Create customer organization |
| `jira-as jsm organization list` | List all organizations |
| `jira-as jsm organization get` | Get organization details |
| `jira-as jsm organization delete` | Delete organization |
| `jira-as jsm organization add-customer` | Add customer to organization |
| `jira-as jsm organization remove-customer` | Remove customer from organization |

### SLA & Queue Management
| Command | Description |
|---------|-------------|
| `jira-as jsm sla get` | Get SLA information for request |
| `jira-as jsm sla check-breach` | Check for SLA breaches |
| `jira-as jsm sla report` | Generate SLA compliance report |
| `jira-as jsm queue list` | List service desk queues |
| `jira-as jsm queue get` | Get queue details |
| `jira-as jsm queue issues` | Get requests in queue |

### Comments & Approvals
| Command | Description |
|---------|-------------|
| `jira-as jsm request comment` | Add comment to request |
| `jira-as jsm request comments` | Get request comments |
| `jira-as jsm approval list` | Get approval status for request |
| `jira-as jsm approval pending` | List pending approvals |
| `jira-as jsm approval approve` | Approve request |
| `jira-as jsm approval decline` | Decline request |

### Knowledge Base & Assets
| Command | Description |
|---------|-------------|
| `jira-as jsm kb search` | Search knowledge base articles |
| `jira-as jsm kb get` | Get knowledge base article |
| `jira-as jsm kb suggest` | Get KB article suggestions for request |
| `jira-as jsm asset create` | Create new asset |
| `jira-as jsm asset list` | List assets |
| `jira-as jsm asset get` | Get asset details |
| `jira-as jsm asset update` | Update asset attributes |
| `jira-as jsm asset link` | Link asset to request |
| `jira-as jsm asset affected` | Find assets affected by request |

## Common Options

All scripts support these common options:

| Option | Description | Example |
|--------|-------------|---------|
| `--help` | Show help and exit | `jira-as <command> --help` |
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
```

For full configuration options, see [references/CONFIG_REFERENCE.md](references/CONFIG_REFERENCE.md).

## Finding Service Desk IDs

Service desk IDs are numeric identifiers required by most scripts.

```bash
# Method 1: List all service desks
jira-as jsm service-desk list

# Method 2: Get details by ID
jira-as jsm service-desk get 1
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
jira-as jsm service-desk list  # Find correct ID
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

