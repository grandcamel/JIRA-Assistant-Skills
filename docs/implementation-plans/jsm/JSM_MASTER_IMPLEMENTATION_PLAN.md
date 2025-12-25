# Jira Service Management (JSM) Skill - Master Implementation Plan

## Executive Summary

**Project:** Implement comprehensive Jira Service Management (JSM) support as a new `jira-jsm` skill
**Timeline:** 10-14 days with parallel execution (vs 10-12 weeks sequential)
**Total Effort:** ~85 hours across 6 phases
**Deliverables:** 45 scripts, 235+ tests, full ITSM/ITIL workflow support

---

## Current State

**From JSM Gap Analysis:**
- Current JSM API Coverage: **0%** of JSM-specific endpoints
- Only generic JIRA APIs (`/rest/api/3/`) currently used
- Excellent workflow documentation exists but not implemented

**Impact of Gap:**
- Cannot create requests with proper request types
- No SLA tracking or reporting
- No internal vs public comment distinction
- No queue management for agents
- No approval workflows for changes
- No knowledge base access
- No customer/organization management

---

## Proposed Skill Structure

```
.claude/skills/jira-jsm/
├── SKILL.md
├── scripts/
│   ├── # Phase 1: Service Desk Core
│   ├── list_service_desks.py
│   ├── get_service_desk.py
│   ├── list_request_types.py
│   ├── get_request_type.py
│   ├── get_request_type_fields.py
│   │
│   ├── # Phase 2: Request Management
│   ├── create_request.py
│   ├── get_request.py
│   ├── transition_request.py
│   ├── list_requests.py
│   ├── get_request_status.py
│   │
│   ├── # Phase 3: Customer & Organization
│   ├── create_customer.py
│   ├── list_customers.py
│   ├── add_customer.py
│   ├── remove_customer.py
│   ├── create_organization.py
│   ├── list_organizations.py
│   ├── get_organization.py
│   ├── delete_organization.py
│   ├── add_to_organization.py
│   ├── remove_from_organization.py
│   ├── get_participants.py
│   ├── add_participant.py
│   ├── remove_participant.py
│   │
│   ├── # Phase 4: SLA & Queues
│   ├── get_sla.py
│   ├── check_sla_breach.py
│   ├── sla_report.py
│   ├── list_queues.py
│   ├── get_queue.py
│   ├── get_queue_issues.py
│   │
│   ├── # Phase 5: Comments & Approvals
│   ├── add_request_comment.py
│   ├── get_request_comments.py
│   ├── get_approvals.py
│   ├── approve_request.py
│   ├── decline_request.py
│   ├── list_pending_approvals.py
│   │
│   ├── # Phase 6: Knowledge Base & Assets
│   ├── search_kb.py
│   ├── get_kb_article.py
│   ├── suggest_kb.py
│   ├── list_assets.py
│   ├── get_asset.py
│   ├── create_asset.py
│   ├── update_asset.py
│   ├── link_asset.py
│   └── find_affected_assets.py
│
├── references/
│   ├── jsm_api_reference.md
│   └── itil_workflows.md
│
└── tests/
    ├── conftest.py
    ├── test_service_desk.py
    ├── test_requests.py
    ├── test_customers.py
    ├── test_organizations.py
    ├── test_sla.py
    ├── test_queues.py
    ├── test_comments.py
    ├── test_approvals.py
    ├── test_kb.py
    └── test_assets.py
```

---

## Implementation Phases

### Phase 1: Service Desk Core (Foundation)
**Plan:** [JSM_PHASE1_SERVICE_DESK_CORE_IMPLEMENTATION_PLAN.md](./JSM_PHASE1_SERVICE_DESK_CORE_IMPLEMENTATION_PLAN.md)
| Metric | Target |
|--------|--------|
| Scripts | 5 |
| Tests | 30 |
| Effort | 8 hours |
| Priority | Critical |

**Scripts:**
- `list_service_desks.py` - List all JSM projects
- `get_service_desk.py` - Get service desk details with request types
- `list_request_types.py` - List available request types
- `get_request_type.py` - Get request type details
- `get_request_type_fields.py` - Get required/optional fields

**Why First:** Foundation for all JSM operations - must discover service desks and request types before creating requests.

---

### Phase 2: Request Management (Core)
**Plan:** [JSM_PHASE2_REQUEST_MANAGEMENT_IMPLEMENTATION_PLAN.md](./JSM_PHASE2_REQUEST_MANAGEMENT_IMPLEMENTATION_PLAN.md)
| Metric | Target |
|--------|--------|
| Scripts | 5 |
| Tests | 35 |
| Effort | 12 hours |
| Priority | Critical |

**Scripts:**
- `create_request.py` - Create via JSM API with request type
- `get_request.py` - Get request with SLA info
- `transition_request.py` - Transition with SLA awareness
- `list_requests.py` - List requests (customer or agent view)
- `get_request_status.py` - Get status change history

**Why Important:** This is the CORE of JSM - requests are the JSM equivalent of issues. Enables proper ITSM workflows.

---

### Phase 3: Customer & Organization Management
**Plan:** [JSM_PHASE3_CUSTOMER_ORGANIZATION_IMPLEMENTATION_PLAN.md](./JSM_PHASE3_CUSTOMER_ORGANIZATION_IMPLEMENTATION_PLAN.md)
| Metric | Target |
|--------|--------|
| Scripts | 13 |
| Tests | 45 |
| Effort | 15 hours |
| Priority | High |

**Scripts:**
- Customer CRUD (4 scripts)
- Organization CRUD (6 scripts)
- Request Participants (3 scripts)

**Why Important:** Required for customer-centric workflows and enterprise/B2B support scenarios.

---

### Phase 4: SLA & Queue Management
**Plan:** [JSM_PHASE4_SLA_QUEUE_IMPLEMENTATION_PLAN.md](./JSM_PHASE4_SLA_QUEUE_IMPLEMENTATION_PLAN.md)
| Metric | Target |
|--------|--------|
| Scripts | 6 |
| Tests | 35 |
| Effort | 14 hours |
| Priority | Critical |

**Scripts:**
- `get_sla.py` - Get SLA status for request
- `check_sla_breach.py` - Check if SLA is breached/approaching breach
- `sla_report.py` - Generate SLA compliance report
- `list_queues.py` - List all queues
- `get_queue.py` - Get queue details
- `get_queue_issues.py` - Get issues in a specific queue

**Why Critical:** Core to ITSM compliance and agent workflow.

---

### Phase 5: Comments & Approvals
**Plan:** [JSM_PHASE5_COMMENTS_APPROVALS_IMPLEMENTATION_PLAN.md](./JSM_PHASE5_COMMENTS_APPROVALS_IMPLEMENTATION_PLAN.md)
| Metric | Target |
|--------|--------|
| Scripts | 6 |
| Tests | 40 |
| Effort | 13 hours |
| Priority | Critical |

**Scripts:**
- `add_request_comment.py` - Add comment with public/internal flag
- `get_request_comments.py` - Get comments with visibility info
- `get_approvals.py` - Get pending approvals for request
- `approve_request.py` - Approve a request
- `decline_request.py` - Decline a request
- `list_pending_approvals.py` - List all pending approvals (agent view)

**Why Critical:** Customer communication and Change Management workflows depend on this.

---

### Phase 6: Knowledge Base & Assets
**Plan:** [JSM_PHASE6_KNOWLEDGE_ASSETS_IMPLEMENTATION_PLAN.md](./JSM_PHASE6_KNOWLEDGE_ASSETS_IMPLEMENTATION_PLAN.md)
| Metric | Target |
|--------|--------|
| Scripts | 9 |
| Tests | 50 |
| Effort | 17 hours |
| Priority | Medium |

**Scripts:**
- Knowledge Base (3 scripts)
- Assets/Insight CMDB (6 scripts)

**Why Medium:** Enables self-service deflection and mature ITSM implementations. Requires JSM Premium for Assets.

---

## Summary Metrics

| Phase | Scripts | Tests | Hours | Priority |
|-------|---------|-------|-------|----------|
| 1. Service Desk Core | 5 | 30 | 8 | Critical |
| 2. Request Management | 5 | 35 | 12 | Critical |
| 3. Customer & Organization | 13 | 45 | 15 | High |
| 4. SLA & Queues | 6 | 35 | 14 | Critical |
| 5. Comments & Approvals | 6 | 40 | 13 | Critical |
| 6. Knowledge Base & Assets | 9 | 50 | 17 | Medium |
| **TOTAL** | **45** | **235** | **85** | - |

---

## Parallel Execution Strategy

See [JSM_ORCHESTRATOR.md](./JSM_ORCHESTRATOR.md) for detailed parallel execution strategy.

### Wave Summary

| Wave | Phases | Parallel Agents | Duration |
|------|--------|-----------------|----------|
| 1 | 1, 3 (partial) | 2 | 2-3 days |
| 2 | 2, 3 (complete) | 2 | 3-4 days |
| 3 | 4, 5 | 2 | 3-4 days |
| 4 | 6 | 1 | 2-3 days |

**Total with parallelization:** 10-14 days

---

## Dependencies

### Phase Dependencies
```
Phase 1 → Phase 2 → Phase 4
    ↘           ↘
Phase 3 →→→→ Phase 5 → Phase 6
```

### External Dependencies
- JSM-enabled JIRA instance for testing
- JSM Premium license for Assets/CMDB features (Phase 6)
- Existing shared library infrastructure

### Skill Dependencies
- `jira-issue` - Integration for request-to-issue compatibility
- `jira-search` - Integration for JSM-aware search
- `jira-collaborate` - Integration for comment enhancement

---

## JiraClient Extensions

New methods to add to `shared/scripts/lib/jira_client.py`:

### Service Desk API Methods
```python
# Base URL: /rest/servicedeskapi

# Service Desk
def get_service_desks(self) -> List[Dict]
def get_service_desk(self, service_desk_id: int) -> Dict
def get_request_types(self, service_desk_id: int) -> List[Dict]
def get_request_type_fields(self, service_desk_id: int, request_type_id: int) -> Dict

# Requests
def create_request(self, service_desk_id: int, request_type_id: int, fields: Dict) -> Dict
def get_request(self, issue_key: str) -> Dict
def transition_request(self, issue_key: str, transition_id: str) -> None
def get_request_status(self, issue_key: str) -> Dict
def get_request_transitions(self, issue_key: str) -> List[Dict]

# SLA
def get_request_sla(self, issue_key: str) -> Dict
def get_sla_metric(self, issue_key: str, metric_id: str) -> Dict

# Comments
def add_request_comment(self, issue_key: str, body: str, public: bool = True) -> Dict
def get_request_comments(self, issue_key: str) -> List[Dict]

# Customers
def create_customer(self, email: str, display_name: str) -> Dict
def get_service_desk_customers(self, service_desk_id: int) -> List[Dict]
def add_customer_to_service_desk(self, service_desk_id: int, account_ids: List[str]) -> None

# Organizations
def get_organizations(self) -> List[Dict]
def create_organization(self, name: str) -> Dict
def get_organization_users(self, organization_id: int) -> List[Dict]
def add_users_to_organization(self, organization_id: int, account_ids: List[str]) -> None

# Participants
def get_request_participants(self, issue_key: str) -> List[Dict]
def add_request_participants(self, issue_key: str, account_ids: List[str]) -> None

# Approvals
def get_request_approvals(self, issue_key: str) -> List[Dict]
def approve_request(self, issue_key: str, approval_id: int, decision: str) -> Dict

# Queues
def get_queues(self, service_desk_id: int) -> List[Dict]
def get_queue_issues(self, service_desk_id: int, queue_id: int) -> List[Dict]

# Knowledge Base
def search_kb_articles(self, service_desk_id: int, query: str) -> List[Dict]
```

---

## Testing Strategy

### Unit Tests
- Mock API responses using `responses` library
- Test all error conditions
- Validate input/output formats
- Target: 85%+ coverage

### Live Integration Tests
- Create JSM test project (or use existing)
- Real API validation
- End-to-end workflow tests
- Add to `shared/tests/live_integration/`

### ITIL Workflow Tests
- Incident Management lifecycle
- Service Request workflow
- Change Management with approvals
- Problem Management linking

---

## Success Criteria

### Per Phase
- [ ] All tests passing
- [ ] Coverage ≥ 85%
- [ ] Scripts documented
- [ ] CLI help complete
- [ ] Integration points verified

### Overall Project
- [ ] 45 scripts implemented
- [ ] 235+ tests passing
- [ ] SKILL.md comprehensive
- [ ] GAP_ANALYSIS.md updated (JSM section complete)
- [ ] Integration with existing skills
- [ ] Live integration tests

---

## Risk Assessment

### Technical Risks
| Risk | Likelihood | Mitigation |
|------|------------|------------|
| JSM API differs between Cloud/Server | Medium | Test both, document differences |
| Request types vary by instance | High | Dynamic discovery via API |
| SLA configuration varies | High | Generic SLA display, configurable fields |
| Customer permissions complex | Medium | Document permission requirements |
| Assets API requires Premium license | High | Mark as optional, graceful degradation |

### Implementation Risks
| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Large scope creep | High | Phased implementation, strict scope |
| Testing requires JSM instance | Medium | Create test JSM project |
| ITIL expertise needed | Medium | Reference existing docs |

---

## Post-Implementation

### Documentation Updates
- [ ] Update `GAP_ANALYSIS.md` - Mark JSM gap as complete
- [ ] Update `CLAUDE.md` - Add jira-jsm skill
- [ ] Create `jira-jsm/SKILL.md` - Comprehensive skill documentation
- [ ] Update `jira-jsm/references/` - API reference and ITIL workflows

### Integration Updates
- [ ] Update `jira-issue` - JSM awareness for request types
- [ ] Update `jira-search` - JSM-aware search fields
- [ ] Update `jira-collaborate` - Comment visibility options

### Coverage Matrix Update

| Feature Category | Before | After |
|------------------|--------|-------|
| Issue/Request CRUD | 90% | 100% |
| Comments | 70% | 100% |
| SLA Tracking | 0% | 100% |
| Customer Management | 0% | 100% |
| Organizations | 0% | 100% |
| Queues | 0% | 100% |
| Approvals | 0% | 100% |
| Knowledge Base | 0% | 80% |
| Assets/CMDB | 0% | 70% |

---

## Quick Start

1. **Review Plans:**
   ```bash
   ls docs/implementation-plans/jsm/
   ```

2. **Check Orchestrator:**
   ```bash
   cat docs/implementation-plans/jsm/JSM_ORCHESTRATOR.md
   ```

3. **Start Wave 1:**
   Use Claude Code Task tool to spawn Phase 1 and Phase 3 agents in parallel.

4. **Monitor Progress:**
   Use MCP memory to track completion status.

5. **Continue Waves:**
   After each wave completes, start the next wave.

---

## References

- [Jira Service Management Cloud REST API](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-servicedesk/)
- [JSM Data Center REST API Reference](https://docs.atlassian.com/jira-servicedesk/REST/5.15.2/)
- [JSM API Changelog](https://developer.atlassian.com/cloud/jira/service-desk/changelog/)
- [JSM Gap Analysis](../../analysis/JSM_GAP_ANALYSIS.md)

---

**Document Version:** 1.0
**Created:** 2025-12-25
**Status:** Ready for Implementation
