# JSM vs Other Skills - Decision Tree

Use this guide to determine which skill to use for your task.

---

## Quick Decision

**Start here: What are you trying to do?**

### 1. Create/Update/Delete an issue

Standard fields like priority, assignee, status, labels.

**Answer**: Use **jira-issue** (works for both standard issues and JSM requests)

---

### 2. Transition an issue through workflow

**If standard JIRA workflow**: Use **jira-lifecycle**

**If JSM-specific approval/transition**: Use **jira-jsm**
- Requests requiring customer approval
- CAB (Change Advisory Board) approvals
- Service desk queue transitions

---

### 3. Search for issues with JQL

**Answer**: Use **jira-search** (works for both standard and JSM requests)

```bash
# Find high-priority incidents
python jql_search.py "project=SD AND type=Incident AND priority=High"

# Find SLA breaches
python jql_search.py "project=SD AND 'Time to resolution' breached"
```

---

### 4. Customer-facing support

Approvals, SLAs, service catalog, customer portal.

**Answer**: Use **jira-jsm**

---

### 5. IT asset management

**If using JSM Assets**: Use **jira-jsm**
- `create_asset.py`, `link_asset.py`, `find_affected_assets.py`

**If using standard custom fields**: Use **jira-issue**

---

### 6. Knowledge base integration

**Answer**: Use **jira-jsm**
- `search_kb.py`, `suggest_kb.py`

---

### 7. Sprint planning or backlog management

**Answer**: Use **jira-agile**

---

### 8. Developer workflow integration

Git branches, commit parsing, PR descriptions.

**Answer**: Use **jira-dev**

---

## Skill Compatibility Matrix

JSM requests (SD-* keys) are standard JIRA issues and work with all skills:

| Skill | Works with JSM? | Use Case |
|-------|-----------------|----------|
| **jira-issue** | Yes | CRUD operations on any request |
| **jira-lifecycle** | Yes | Workflow transitions |
| **jira-search** | Yes | Query and filter requests |
| **jira-relationships** | Yes | Link requests together |
| **jira-collaborate** | Yes | Comments, attachments, notifications |
| **jira-agile** | No | Sprint/backlog (not typical for JSM) |
| **jira-dev** | Limited | Git integration (rare for service requests) |

---

## Common Combinations

### Incident Resolution

1. **jira-jsm**: Create request, monitor SLA
2. **jira-issue**: Update priority, assign
3. **jira-collaborate**: Add comments, attachments
4. **jira-jsm**: Transition through workflow

### Change Management

1. **jira-jsm**: Create change request, get approvals
2. **jira-relationships**: Link to problem record
3. **jira-jsm**: Link affected assets
4. **jira-issue**: Update status, add labels

### Problem Investigation

1. **jira-jsm**: Create problem record
2. **jira-search**: Find related incidents
3. **jira-relationships**: Link incidents to problem
4. **jira-collaborate**: Add analysis comments

---

## NOT This Skill

| Task | Use Instead |
|------|-------------|
| Creating bugs/stories in Agile | **jira-issue** |
| Sprint planning or backlog | **jira-agile** |
| Developer workflow (Git, PRs) | **jira-dev** |
| Standard workflow transitions | **jira-lifecycle** |
| Bulk issue operations | **jira-bulk** |
| Custom field management | **jira-fields** |

---

## When to Use jira-jsm

Use jira-jsm when you encounter:

### Problem Indicators
- Keywords: "SLA", "service level", "breach", "approval", "change request"
- Issue keys like: `SD-123`, `INC-456` (service desk format)
- Workflow needs: customer-facing requests, ITIL processes

### Feature Triggers
- Need to track SLA compliance or generate SLA reports
- Managing approval workflows or CAB decisions
- Working with knowledge base for customer self-service
- Linking IT assets to requests or impact analysis
- Multi-tier support structure (agents, managers, customers)

---

*Last updated: December 2025*
