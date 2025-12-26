# Automation Rules - TDD Implementation Plan

## Implementation Status

**Overall Status:** 🟡 READY FOR IMPLEMENTATION

**Current State:** Planning phase complete. Atlassian Automation Rule Management API is now GA (General Availability as of August 29, 2025).

**API Availability:** ✅ FULL API SUPPORT AVAILABLE

The Automation Rule Management API transitioned from experimental to general availability in August 2025, providing comprehensive CRUD operations for automation rules.

**Last Updated:** 2025-12-26

---

## Overview

**Objective:** Implement comprehensive Jira Automation rule management functionality using the official Atlassian Automation REST API with Test-Driven Development (TDD)

**API Documentation:**
- [Automation REST API Reference](https://developer.atlassian.com/cloud/automation/rest/)
- [API Changelog](https://developer.atlassian.com/cloud/automation/api/changelog/)
- [Authentication Guide](https://developer.atlassian.com/cloud/automation/security/authentication/)
- [API Base Paths](https://developer.atlassian.com/cloud/automation/api/base-paths/)

**Key Features:**
- List automation rules with filtering by trigger, state, and scope
- Get detailed rule configuration including components and connections
- Create new automation rules from scratch or templates
- Update existing rule configuration
- Enable/disable rules programmatically
- Search and invoke manual rules
- Template-based rule creation

**Approach:**
1. Write failing tests first for each feature
2. Implement minimum code to pass tests
3. Refactor while keeping tests green
4. Commit after each successful test suite
5. Update documentation as features complete

**Testing Stack:**
- **Framework:** pytest
- **Mocking:** unittest.mock / responses library
- **Coverage Target:** 85%+
- **Test Location:** `.claude/skills/jira-admin/tests/`

**Feature Priority:**
1. **Phase 1: Rule Discovery & Inspection** (List, Get, Search)
2. **Phase 2: Rule State Management** (Enable/Disable)
3. **Phase 3: Manual Rule Invocation** (Trigger manual rules)
4. **Phase 4: Rule Creation & Updates** (Create, Update from templates)
5. **Phase 5: Advanced Rule Management** (Custom rule creation, complex configurations)

---

## API Availability Assessment

### ✅ What IS Possible via REST API

The Atlassian Automation REST API (GA as of August 2025) provides the following capabilities:

#### 1. Rule Management (CRUD Operations)
- **List Rules:** `GET /rest/v1/rule/summary` - Get rule summaries with pagination
- **Search Rules:** `POST /rest/v1/rule/summary` - Search with filters (trigger, state, scope)
- **Get Rule:** `GET /rest/v1/rule/{ruleUuid}` - Full rule details with configuration
- **Create Rule:** `POST /rest/v1/rule` - Create new automation rules
- **Update Rule:** `PUT /rest/v1/rule/{ruleUuid}` - Update rule configuration
- **Update State:** `PUT /rest/v1/rule/{ruleUuid}/state` - Enable/disable rules
- **Update Scope:** `PUT /rest/v1/rule/{ruleUuid}/rule-scope` - Change rule scope

#### 2. Manual Rules
- **Search Manual Rules:** `GET/POST /rest/v1/rule/manual/search` - Find manually-triggered rules
- **Invoke Manual Rule:** `POST /rest/v1/rule/manual/{ruleId}/invocation` - Trigger manual rules with inputs

#### 3. Templates
- **Get Template:** `GET /rest/v1/template/{templateId}` - Template metadata
- **Search Templates:** `GET/POST /rest/v1/template/search` - Find available templates
- **Create from Template:** `POST /rest/v1/template/create` - Create rules from templates

### ⚠️ Limitations & Requirements

#### Authentication Requirements
- **API Token:** Required (Basic auth or Bearer token)
- **Scopes:** `manage:jira-automation` for write operations, `read:jira-work` for read operations
- **Permissions:** Jira Administrator permissions required for most rule management operations
- **Base URL:** Must use Automation API gateway (not standard Jira REST API)

#### API Constraints
- **Filtering:** Search supports trigger, state, and scope (single ARI) only in initial release
- **Pagination:** Cursor-based pagination with 1-100 results per page (default 50)
- **UUID Format:** Rules identified by UUID v7 format (not numeric IDs)
- **Product Context:** Requires product (jira/confluence) and cloudId in API path
- **Complex Rules:** Creating complex rules with advanced logic may require UI configuration
- **Audit Trail:** Rule execution history not available via API (UI only)

#### Known Deprecations
- **ruleId (numeric):** Deprecated in Dec 2024, removed Jan 2025 - use `ruleUuid` instead
- **Pagination Links:** Changed Aug 11, 2025 to relative query params only (no absolute URLs)

### ❌ What is NOT Possible via REST API

- **Rule Execution History:** No API for viewing rule execution logs/audit trail
- **Rule Analytics:** No API for rule performance metrics, error rates, etc.
- **Bulk Rule Operations:** No dedicated bulk enable/disable endpoint
- **Rule Import/Export:** No direct API for exporting/importing rule configurations (workaround: GET all rules as JSON)
- **Global Rule Throttling:** Server/DC only feature (set processing time limits)
- **Advanced Rule Builder:** Complex visual rule builder features (conditional logic trees, etc.) require UI

---

## JIRA API Reference

### Base Paths

The Automation REST API uses two base path formats:

1. **Primary (API Gateway):**
   ```
   https://api.atlassian.com/automation/public/{product}/{cloudId}/rest/v1/
   ```
   - Product: `jira` or `confluence`
   - CloudId: Found via `https://{sitename}/_edge/tenant_info`
   - Authentication: API token (Basic or Bearer)

2. **Site-Specific:**
   ```
   https://{sitename}/gateway/api/automation/public/{product}/{cloudId}/rest/v1/
   ```
   - Supports browser session authentication
   - Same API token authentication

### Endpoints Overview

| Method | Endpoint | Description | Priority |
|--------|----------|-------------|----------|
| GET | `/rest/v1/rule/summary` | List rule summaries (with pagination) | **Critical** |
| POST | `/rest/v1/rule/summary` | Search rules with filters | **Critical** |
| GET | `/rest/v1/rule/{ruleUuid}` | Get full rule details | **Critical** |
| POST | `/rest/v1/rule` | Create new rule | High |
| PUT | `/rest/v1/rule/{ruleUuid}` | Update rule configuration | High |
| PUT | `/rest/v1/rule/{ruleUuid}/state` | Enable/disable rule | **Critical** |
| PUT | `/rest/v1/rule/{ruleUuid}/rule-scope` | Update rule scope | Medium |
| GET/POST | `/rest/v1/rule/manual/search` | Search manual rules | Medium |
| POST | `/rest/v1/rule/manual/{ruleId}/invocation` | Invoke manual rule | Medium |
| GET | `/rest/v1/template/{templateId}` | Get template details | Medium |
| GET/POST | `/rest/v1/template/search` | Search templates | Medium |
| POST | `/rest/v1/template/create` | Create rule from template | High |

### Authentication

**API Token Generation:**
1. Visit https://id.atlassian.com/manage-profile/security/api-tokens
2. Create API token with scopes:
   - `manage:jira-automation` (for create/update/delete)
   - `read:jira-work` (for list/get operations)
3. User account must have Jira Administrator permissions

**Request Headers:**
```bash
# Basic Auth (recommended for simplicity)
Authorization: Basic base64(<email>:<token>)

# Bearer Token Auth (for scoped tokens)
Authorization: Bearer <token>
```

### Data Structures

#### Rule Summary Response
```json
{
  "values": [
    {
      "id": "ari:cloud:jira::site/12345678-abcd-1234-abcd-1234567890ab",
      "name": "Auto-assign issues to lead",
      "state": "ENABLED",
      "ruleScope": {
        "resources": [
          "ari:cloud:jira:12345678-abcd-1234-abcd-1234567890ab:project/10000"
        ]
      },
      "canManage": true,
      "trigger": {
        "type": "jira.issue.event.trigger:created"
      },
      "created": "2025-01-15T10:30:00.000Z",
      "updated": "2025-01-20T14:45:00.000Z"
    }
  ],
  "links": {
    "next": "?cursor=next_page_token",
    "prev": "?cursor=prev_page_token"
  },
  "hasMore": false
}
```

#### Full Rule Response
```json
{
  "id": "ari:cloud:jira::site/12345678-abcd-1234-abcd-1234567890ab",
  "name": "Auto-assign issues to lead",
  "description": "Automatically assigns new issues to project lead",
  "state": "ENABLED",
  "ruleScope": {
    "resources": [
      "ari:cloud:jira:12345678-abcd-1234-abcd-1234567890ab:project/10000"
    ]
  },
  "trigger": {
    "type": "jira.issue.event.trigger:created",
    "configuration": {
      "issueEvent": "issue_created"
    }
  },
  "components": [
    {
      "type": "jira.issue.assign",
      "value": "{{project.lead.accountId}}",
      "children": []
    }
  ],
  "connections": [],
  "canManage": true,
  "created": "2025-01-15T10:30:00.000Z",
  "updated": "2025-01-20T14:45:00.000Z",
  "authorAccountId": "557058:f58131cb-b67d-43c7-b30d-6b58d40bd077"
}
```

#### Manual Rule Invocation Request
```json
{
  "context": {
    "issue": {
      "key": "PROJ-123"
    }
  },
  "properties": {
    "customField1": "value1",
    "customField2": 42
  }
}
```

#### Template Search Response
```json
{
  "values": [
    {
      "id": "template-001",
      "name": "Assign issues to project lead",
      "description": "Automatically assigns new issues to the project lead",
      "category": "Issue Management",
      "tags": ["assignment", "automation"],
      "parameters": [
        {
          "name": "projectKey",
          "type": "string",
          "required": true,
          "description": "Project key to apply the rule"
        }
      ]
    }
  ]
}
```

---

## Proposed Script Structure

```
.claude/skills/jira-admin/
├── scripts/
│   ├── # Phase 1: Rule Discovery & Inspection
│   ├── list_automation_rules.py       # List all rules with filtering
│   ├── get_automation_rule.py         # Get detailed rule configuration
│   ├── search_automation_rules.py     # Search rules by trigger/state/scope
│   │
│   ├── # Phase 2: Rule State Management
│   ├── enable_automation_rule.py      # Enable a rule
│   ├── disable_automation_rule.py     # Disable a rule
│   ├── toggle_automation_rule.py      # Toggle rule state
│   │
│   ├── # Phase 3: Manual Rule Invocation
│   ├── list_manual_rules.py           # List manually-triggered rules
│   ├── invoke_manual_rule.py          # Trigger a manual rule
│   │
│   ├── # Phase 4: Rule Creation & Updates
│   ├── list_automation_templates.py   # List available templates
│   ├── get_automation_template.py     # Get template details
│   ├── create_rule_from_template.py   # Create rule from template
│   ├── update_automation_rule.py      # Update rule configuration
│   │
│   └── # Phase 5: Advanced Rule Management
│       ├── create_automation_rule.py  # Create custom rule from scratch
│       ├── update_rule_scope.py       # Change rule scope (project/global)
│       └── export_automation_rules.py # Export rules as JSON
│
└── tests/
    ├── conftest.py
    ├── test_rule_discovery.py
    ├── test_rule_state_management.py
    ├── test_manual_rules.py
    ├── test_rule_templates.py
    └── test_rule_creation.py
```

---

## Phase 1: Rule Discovery & Inspection

### Feature 1.1: List Automation Rules

**Script:** `list_automation_rules.py`

**JIRA API:**
- `GET /rest/v1/rule/summary` - List rule summaries
- Supports pagination via cursor

**Shared Library Integration:**
```python
# Add to jira_client.py
def get_automation_rules(self, limit=50, cursor=None, product='jira'):
    """List automation rules with pagination"""

def search_automation_rules(self, filters=None, limit=50, product='jira'):
    """Search rules with filters (trigger, state, scope)"""
```

**Test File:** `tests/test_rule_discovery.py`

**Test Cases:**
```python
def test_list_automation_rules_basic():
    """Test listing all automation rules"""

def test_list_automation_rules_with_pagination():
    """Test pagination through rules"""

def test_list_automation_rules_project_scoped():
    """Test filtering by project scope"""

def test_list_automation_rules_by_state():
    """Test filtering by enabled/disabled state"""

def test_list_automation_rules_empty():
    """Test when no rules exist"""

def test_list_automation_rules_authentication_error():
    """Test authentication failure handling"""

def test_list_automation_rules_permission_denied():
    """Test permission error handling"""
```

**CLI Interface:**
```bash
# List all rules
python list_automation_rules.py

# List rules for specific project
python list_automation_rules.py --project PROJ

# List only enabled rules
python list_automation_rules.py --state enabled

# List only disabled rules
python list_automation_rules.py --state disabled

# Pagination
python list_automation_rules.py --limit 10
python list_automation_rules.py --cursor "next_page_token"

# Output formats
python list_automation_rules.py --output table
python list_automation_rules.py --output json
python list_automation_rules.py --output csv

# With profile
python list_automation_rules.py --profile development
```

**Output Format:**
```
Automation Rules
================

ID: ari:cloud:jira::site/12345...
Name: Auto-assign to lead
State: ENABLED
Scope: Project PROJ
Trigger: Issue Created
Created: 2025-01-15
Updated: 2025-01-20

ID: ari:cloud:jira::site/67890...
Name: Comment on status change
State: DISABLED
Scope: Global
Trigger: Issue Transitioned
Created: 2025-01-10
Updated: 2025-01-18

Total: 2 rules
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Supports pagination
- [ ] Filters by state (enabled/disabled)
- [ ] Filters by project scope
- [ ] Table/JSON/CSV output formats
- [ ] Profile support

---

### Feature 1.2: Get Automation Rule Details

**Script:** `get_automation_rule.py`

**JIRA API:**
- `GET /rest/v1/rule/{ruleUuid}` - Get full rule configuration

**Shared Library Integration:**
```python
# Add to jira_client.py
def get_automation_rule(self, rule_id, product='jira'):
    """Get detailed automation rule configuration"""
```

**Test Cases:**
```python
def test_get_automation_rule_basic():
    """Test getting rule details"""

def test_get_automation_rule_with_components():
    """Test rule with actions/conditions"""

def test_get_automation_rule_with_connections():
    """Test rule with external connections"""

def test_get_automation_rule_not_found():
    """Test invalid rule ID error"""

def test_get_automation_rule_permission_denied():
    """Test permission error"""
```

**CLI Interface:**
```bash
# Get rule by ID
python get_automation_rule.py "ari:cloud:jira::site/12345..."

# Get rule by name (requires search first)
python get_automation_rule.py --name "Auto-assign to lead"

# Output formats
python get_automation_rule.py RULE_ID --output json
python get_automation_rule.py RULE_ID --output yaml

# Show only specific sections
python get_automation_rule.py RULE_ID --show-trigger
python get_automation_rule.py RULE_ID --show-components
python get_automation_rule.py RULE_ID --show-connections
```

**Acceptance Criteria:**
- [ ] All 5 tests pass
- [ ] Shows full rule configuration
- [ ] JSON/YAML output
- [ ] Error handling for invalid IDs

---

### Feature 1.3: Search Automation Rules

**Script:** `search_automation_rules.py`

**JIRA API:**
- `POST /rest/v1/rule/summary` - Search with filters

**Test Cases:**
```python
def test_search_by_trigger_type():
    """Test filtering by trigger (e.g., issue_created)"""

def test_search_by_state():
    """Test filtering by enabled/disabled"""

def test_search_by_scope():
    """Test filtering by project ARI"""

def test_search_combined_filters():
    """Test multiple filters together"""

def test_search_no_results():
    """Test when search returns empty"""
```

**CLI Interface:**
```bash
# Search by trigger type
python search_automation_rules.py --trigger "jira.issue.event.trigger:created"

# Search by state
python search_automation_rules.py --state enabled

# Search by scope
python search_automation_rules.py --scope "ari:cloud:jira:...:project/10000"

# Combined search
python search_automation_rules.py --trigger "issue_created" --state enabled --project PROJ
```

**Acceptance Criteria:**
- [ ] All 5 tests pass
- [ ] Filter by trigger, state, scope
- [ ] Combined filter support

---

### Phase 1 Completion

- [ ] **Phase 1 Summary:**
  - [ ] 3 scripts implemented
  - [ ] 17 tests passing
  - [ ] Coverage ≥ 85%
  - **Commit:** `feat(jira-admin): implement automation rule discovery (17/17 tests passing)`

---

## Phase 2: Rule State Management

### Feature 2.1: Enable/Disable Automation Rules

**Scripts:** `enable_automation_rule.py`, `disable_automation_rule.py`, `toggle_automation_rule.py`

**JIRA API:**
- `PUT /rest/v1/rule/{ruleUuid}/state` - Update rule state

**Shared Library Integration:**
```python
# Add to jira_client.py
def update_automation_rule_state(self, rule_id, state, product='jira'):
    """Enable or disable an automation rule

    Args:
        rule_id: Rule UUID (ARI format)
        state: 'ENABLED' or 'DISABLED'
        product: 'jira' or 'confluence'
    """
```

**Test Cases:**
```python
def test_enable_automation_rule():
    """Test enabling a disabled rule"""

def test_disable_automation_rule():
    """Test disabling an enabled rule"""

def test_toggle_automation_rule_enabled_to_disabled():
    """Test toggling from enabled to disabled"""

def test_toggle_automation_rule_disabled_to_enabled():
    """Test toggling from disabled to enabled"""

def test_enable_already_enabled_rule():
    """Test idempotency - enabling already enabled rule"""

def test_disable_already_disabled_rule():
    """Test idempotency - disabling already disabled rule"""

def test_update_state_invalid_rule_id():
    """Test error for invalid rule ID"""

def test_update_state_permission_denied():
    """Test permission error handling"""

def test_bulk_enable_rules():
    """Test enabling multiple rules (if supported)"""
```

**CLI Interface:**
```bash
# Enable a rule
python enable_automation_rule.py "ari:cloud:jira::site/12345..."
python enable_automation_rule.py --name "Auto-assign to lead"

# Disable a rule
python disable_automation_rule.py "ari:cloud:jira::site/12345..."
python disable_automation_rule.py --name "Auto-assign to lead"

# Toggle rule state
python toggle_automation_rule.py "ari:cloud:jira::site/12345..."

# Dry run mode
python enable_automation_rule.py RULE_ID --dry-run

# Confirmation for critical changes
python disable_automation_rule.py RULE_ID --confirm

# Bulk operations (enable multiple rules)
python enable_automation_rule.py --project PROJ --all
python disable_automation_rule.py --project PROJ --all --confirm
```

**Output Format:**
```
Rule State Updated
==================

Rule ID: ari:cloud:jira::site/12345...
Name: Auto-assign to lead
Previous State: DISABLED
New State: ENABLED
Updated: 2025-12-26T10:30:00Z

Success: Rule has been enabled.
```

**Acceptance Criteria:**
- [ ] All 9 tests pass
- [ ] Enable/disable/toggle operations
- [ ] Idempotent operations
- [ ] Dry-run mode support
- [ ] Confirmation prompts for bulk operations
- [ ] Clear success/error messages

---

### Phase 2 Completion

- [ ] **Phase 2 Summary:**
  - [ ] 3 scripts implemented
  - [ ] 9 tests passing
  - [ ] Coverage ≥ 85%
  - **Commit:** `feat(jira-admin): implement automation rule state management (9/9 tests passing)`

---

## Phase 3: Manual Rule Invocation

### Feature 3.1: List Manual Rules

**Script:** `list_manual_rules.py`

**JIRA API:**
- `GET/POST /rest/v1/rule/manual/search` - Search manual rules

**Shared Library Integration:**
```python
# Add to jira_client.py
def get_manual_automation_rules(self, context_type='issue', limit=50, product='jira'):
    """List manually-triggered automation rules

    Args:
        context_type: 'issue', 'alert', etc.
        limit: Max results per page
        product: 'jira' or 'confluence'
    """
```

**Test Cases:**
```python
def test_list_manual_rules_for_issues():
    """Test listing manual rules for issue context"""

def test_list_manual_rules_for_alerts():
    """Test listing manual rules for alert context"""

def test_list_manual_rules_empty():
    """Test when no manual rules exist"""

def test_list_manual_rules_pagination():
    """Test pagination through manual rules"""
```

**CLI Interface:**
```bash
# List all manual rules
python list_manual_rules.py

# List for specific context type
python list_manual_rules.py --context issue
python list_manual_rules.py --context alert

# Output formats
python list_manual_rules.py --output table
python list_manual_rules.py --output json
```

**Acceptance Criteria:**
- [ ] All 4 tests pass
- [ ] Filter by context type
- [ ] Pagination support

---

### Feature 3.2: Invoke Manual Rule

**Script:** `invoke_manual_rule.py`

**JIRA API:**
- `POST /rest/v1/rule/manual/{ruleId}/invocation` - Trigger manual rule

**Shared Library Integration:**
```python
# Add to jira_client.py
def invoke_manual_automation_rule(self, rule_id, context, properties=None, product='jira'):
    """Invoke a manual automation rule

    Args:
        rule_id: Rule ID (not UUID)
        context: Context object (e.g., {"issue": {"key": "PROJ-123"}})
        properties: Optional input properties
        product: 'jira' or 'confluence'
    """
```

**Test Cases:**
```python
def test_invoke_manual_rule_on_issue():
    """Test invoking rule on an issue"""

def test_invoke_manual_rule_with_properties():
    """Test passing custom properties to rule"""

def test_invoke_manual_rule_invalid_context():
    """Test error for invalid context"""

def test_invoke_manual_rule_not_found():
    """Test error for invalid rule ID"""

def test_invoke_manual_rule_permission_denied():
    """Test permission error"""
```

**CLI Interface:**
```bash
# Invoke rule on an issue
python invoke_manual_rule.py RULE_ID --issue PROJ-123

# With custom properties
python invoke_manual_rule.py RULE_ID --issue PROJ-123 \
  --property '{"priority": "High", "assignee": "john@example.com"}'

# Dry run to preview
python invoke_manual_rule.py RULE_ID --issue PROJ-123 --dry-run

# From JSON file
python invoke_manual_rule.py RULE_ID --context-file context.json
```

**Acceptance Criteria:**
- [ ] All 5 tests pass
- [ ] Issue context support
- [ ] Custom properties
- [ ] Dry-run mode
- [ ] JSON file input

---

### Phase 3 Completion

- [ ] **Phase 3 Summary:**
  - [ ] 2 scripts implemented
  - [ ] 9 tests passing
  - [ ] Coverage ≥ 85%
  - **Commit:** `feat(jira-admin): implement manual automation rule invocation (9/9 tests passing)`

---

## Phase 4: Rule Creation & Updates

### Feature 4.1: List Automation Templates

**Script:** `list_automation_templates.py`

**JIRA API:**
- `GET/POST /rest/v1/template/search` - Search templates

**Shared Library Integration:**
```python
# Add to jira_client.py
def get_automation_templates(self, category=None, limit=50, product='jira'):
    """List available automation rule templates"""
```

**Test Cases:**
```python
def test_list_templates_all():
    """Test listing all templates"""

def test_list_templates_by_category():
    """Test filtering by category"""

def test_list_templates_pagination():
    """Test pagination"""
```

**CLI Interface:**
```bash
# List all templates
python list_automation_templates.py

# Filter by category
python list_automation_templates.py --category "Issue Management"

# Output formats
python list_automation_templates.py --output table --verbose
```

**Acceptance Criteria:**
- [ ] All 3 tests pass
- [ ] Category filtering
- [ ] Verbose mode with descriptions

---

### Feature 4.2: Create Rule from Template

**Script:** `create_rule_from_template.py`

**JIRA API:**
- `GET /rest/v1/template/{templateId}` - Get template details
- `POST /rest/v1/template/create` - Create rule from template

**Shared Library Integration:**
```python
# Add to jira_client.py
def get_automation_template(self, template_id, product='jira'):
    """Get template details"""

def create_automation_rule_from_template(self, template_id, parameters, product='jira'):
    """Create rule from template with parameters"""
```

**Test Cases:**
```python
def test_create_rule_from_template_basic():
    """Test creating rule from template"""

def test_create_rule_from_template_with_params():
    """Test providing template parameters"""

def test_create_rule_from_template_invalid_template():
    """Test error for invalid template ID"""

def test_create_rule_from_template_missing_params():
    """Test validation of required parameters"""
```

**CLI Interface:**
```bash
# Create from template
python create_rule_from_template.py TEMPLATE_ID --project PROJ

# With custom name
python create_rule_from_template.py TEMPLATE_ID --project PROJ \
  --name "Custom Rule Name"

# With parameters
python create_rule_from_template.py TEMPLATE_ID --project PROJ \
  --param projectKey=PROJ \
  --param assignee="john@example.com"

# From JSON config
python create_rule_from_template.py TEMPLATE_ID --config template_config.json

# Dry run
python create_rule_from_template.py TEMPLATE_ID --project PROJ --dry-run
```

**Acceptance Criteria:**
- [ ] All 4 tests pass
- [ ] Template parameter support
- [ ] JSON config file
- [ ] Dry-run mode

---

### Feature 4.3: Update Automation Rule

**Script:** `update_automation_rule.py`

**JIRA API:**
- `PUT /rest/v1/rule/{ruleUuid}` - Update rule configuration

**Shared Library Integration:**
```python
# Add to jira_client.py
def update_automation_rule(self, rule_id, rule_config, product='jira'):
    """Update automation rule configuration

    Args:
        rule_id: Rule UUID
        rule_config: Updated rule configuration (name, description, components, etc.)
        product: 'jira' or 'confluence'
    """
```

**Test Cases:**
```python
def test_update_rule_name():
    """Test updating rule name"""

def test_update_rule_description():
    """Test updating rule description"""

def test_update_rule_components():
    """Test updating rule actions/conditions"""

def test_update_rule_not_found():
    """Test error for invalid rule ID"""

def test_update_rule_permission_denied():
    """Test permission error"""
```

**CLI Interface:**
```bash
# Update rule name
python update_automation_rule.py RULE_ID --name "New Rule Name"

# Update description
python update_automation_rule.py RULE_ID --description "Updated description"

# Update from JSON config
python update_automation_rule.py RULE_ID --config updated_rule.json

# Dry run
python update_automation_rule.py RULE_ID --config updated_rule.json --dry-run
```

**Acceptance Criteria:**
- [ ] All 5 tests pass
- [ ] Update name, description
- [ ] JSON config support
- [ ] Dry-run mode

---

### Phase 4 Completion

- [ ] **Phase 4 Summary:**
  - [ ] 3 scripts implemented
  - [ ] 12 tests passing
  - [ ] Coverage ≥ 85%
  - **Commit:** `feat(jira-admin): implement automation rule creation and updates (12/12 tests passing)`

---

## Phase 5: Advanced Rule Management

### Feature 5.1: Create Custom Automation Rule

**Script:** `create_automation_rule.py`

**JIRA API:**
- `POST /rest/v1/rule` - Create new rule

**Shared Library Integration:**
```python
# Add to jira_client.py
def create_automation_rule(self, name, trigger, components, scope, description=None, product='jira'):
    """Create custom automation rule from scratch

    Args:
        name: Rule name
        trigger: Trigger configuration
        components: List of actions/conditions
        scope: Rule scope (project ARI or global)
        description: Optional description
        product: 'jira' or 'confluence'
    """
```

**Test Cases:**
```python
def test_create_rule_basic():
    """Test creating simple rule"""

def test_create_rule_with_conditions():
    """Test rule with conditions"""

def test_create_rule_with_multiple_actions():
    """Test rule with multiple actions"""

def test_create_rule_project_scoped():
    """Test project-scoped rule"""

def test_create_rule_global_scoped():
    """Test global-scoped rule"""

def test_create_rule_invalid_trigger():
    """Test validation of trigger type"""
```

**CLI Interface:**
```bash
# Create simple rule
python create_automation_rule.py \
  --name "Auto-assign on create" \
  --project PROJ \
  --trigger issue_created \
  --action assign \
  --action-config '{"assignee": "{{project.lead}}"}'

# From JSON file (recommended for complex rules)
python create_automation_rule.py --config rule_definition.json

# Dry run
python create_automation_rule.py --config rule_definition.json --dry-run
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Basic trigger/action support
- [ ] JSON config for complex rules
- [ ] Project/global scope

---

### Feature 5.2: Update Rule Scope

**Script:** `update_rule_scope.py`

**JIRA API:**
- `PUT /rest/v1/rule/{ruleUuid}/rule-scope` - Update rule scope

**Shared Library Integration:**
```python
# Add to jira_client.py
def update_automation_rule_scope(self, rule_id, scope, product='jira'):
    """Update automation rule scope (project/global)"""
```

**Test Cases:**
```python
def test_update_scope_to_project():
    """Test changing to project scope"""

def test_update_scope_to_global():
    """Test changing to global scope"""

def test_update_scope_invalid_ari():
    """Test validation of ARI format"""
```

**CLI Interface:**
```bash
# Change to project scope
python update_rule_scope.py RULE_ID --project PROJ

# Change to global scope
python update_rule_scope.py RULE_ID --global

# Dry run
python update_rule_scope.py RULE_ID --project PROJ --dry-run
```

**Acceptance Criteria:**
- [ ] All 3 tests pass
- [ ] Project/global scope changes
- [ ] ARI validation

---

### Feature 5.3: Export Automation Rules

**Script:** `export_automation_rules.py`

**JIRA API:**
- Uses existing list/get endpoints

**Test Cases:**
```python
def test_export_all_rules():
    """Test exporting all rules as JSON"""

def test_export_project_rules():
    """Test exporting project-specific rules"""

def test_export_with_full_config():
    """Test including full rule configuration"""
```

**CLI Interface:**
```bash
# Export all rules
python export_automation_rules.py --output all_rules.json

# Export project rules
python export_automation_rules.py --project PROJ --output proj_rules.json

# Export with full config (for backup/migration)
python export_automation_rules.py --full --output backup.json
```

**Acceptance Criteria:**
- [ ] All 3 tests pass
- [ ] JSON export
- [ ] Full configuration export

---

### Phase 5 Completion

- [ ] **Phase 5 Summary:**
  - [ ] 3 scripts implemented
  - [ ] 12 tests passing
  - [ ] Coverage ≥ 85%
  - **Commit:** `feat(jira-admin): implement advanced automation rule management (12/12 tests passing)`

---

## Integration & Documentation

### Configuration Updates

**Add to `.claude/skills/shared/config/config.schema.json`:**
```json
{
  "automation": {
    "cloudId": "string",
    "product": "jira",
    "baseUrl": "https://api.atlassian.com/automation/public"
  }
}
```

**Add to `config_manager.py`:**
```python
def get_automation_client(profile=None):
    """Get Automation API client with proper authentication"""
    config = get_config(profile)
    cloud_id = config.get('automation', {}).get('cloudId')

    if not cloud_id:
        # Fetch from tenant_info endpoint
        cloud_id = _fetch_cloud_id(config)

    return AutomationClient(
        email=config['jira_email'],
        token=config['jira_api_token'],
        cloud_id=cloud_id,
        product=config.get('automation', {}).get('product', 'jira')
    )
```

### Shared Library Additions

Create new module: `.claude/skills/shared/scripts/lib/automation_client.py`

```python
"""Atlassian Automation REST API client"""

class AutomationClient:
    """Client for Automation API with proper base path handling"""

    def __init__(self, email, token, cloud_id, product='jira', use_gateway=False):
        """Initialize Automation API client

        Args:
            email: User email for authentication
            token: API token
            cloud_id: Atlassian cloud ID
            product: 'jira' or 'confluence'
            use_gateway: Use site gateway instead of api.atlassian.com
        """
        self.cloud_id = cloud_id
        self.product = product

        if use_gateway:
            # Extract site from email or require site_url
            self.base_url = f"https://{site}/gateway/api/automation/public/{product}/{cloud_id}"
        else:
            self.base_url = f"https://api.atlassian.com/automation/public/{product}/{cloud_id}"

        # Rest of implementation...
```

### Documentation Tasks

- [ ] **Docs 1:** Create `SKILL.md` for jira-admin automation features
  - Include authentication setup guide
  - Document cloudId retrieval
  - List all scripts with examples
  - **Commit:** `docs(jira-admin): add SKILL.md for automation rules`

- [ ] **Docs 2:** Update `CLAUDE.md` with automation patterns
  - Add automation_client.py usage
  - Document cloudId configuration
  - Add common automation patterns
  - **Commit:** `docs: add automation rules patterns to CLAUDE.md`

- [ ] **Docs 3:** Create automation examples in `assets/`
  - Example rule configurations (JSON)
  - Common automation patterns
  - Template usage examples
  - **Commit:** `docs(jira-admin): add automation rule examples`

- [ ] **Docs 4:** Update GAP_ANALYSIS.md
  - Mark automation rules as implemented
  - Document API limitations
  - **Commit:** `docs: mark automation rules as complete in GAP_ANALYSIS.md`

---

## Alternative Approaches (If Needed)

### If API Access is Restricted

**Workaround 1: Automation Web Requests**
- Use "Send web request" action within automation rules
- Trigger rules via webhook
- Limited to rule execution, not management

**Workaround 2: Atlassian Connect App**
- Build Connect app with automation permissions
- Use app context for API access
- Requires app installation

**Workaround 3: Forge Apps**
- Build Forge app with automation module
- Access internal APIs via Forge bridge
- Requires Forge development setup

**Workaround 4: UI Automation**
- Use Selenium/Playwright for UI automation
- Fragile and not recommended
- Last resort only

### Recommendation

The Automation Rule Management API is now GA (General Availability), so direct API access is the recommended approach. No alternative methods needed.

---

## Success Metrics

### Completion Criteria

**Tests:**
- [ ] 59+ unit tests passing
- [ ] Coverage ≥ 85%
- [ ] Live integration tests (if test instance available)

**Scripts:**
- [ ] 14 new scripts implemented
- [ ] All scripts have `--help`
- [ ] All scripts support `--profile`
- [ ] All mutation scripts have `--dry-run`
- [ ] All scripts have `--output` format options

**Documentation:**
- [ ] SKILL.md complete with examples
- [ ] CLAUDE.md updated with patterns
- [ ] API limitations documented
- [ ] Authentication guide complete

**Shared Library:**
- [ ] `automation_client.py` implemented
- [ ] `config_manager.py` updated for cloudId
- [ ] Error handling for automation API errors

---

## Summary Metrics

| Phase | Scripts | Tests | Priority |
|-------|---------|-------|----------|
| 1. Rule Discovery & Inspection | 3 | 17 | **Critical** |
| 2. Rule State Management | 3 | 9 | **Critical** |
| 3. Manual Rule Invocation | 2 | 9 | High |
| 4. Rule Creation & Updates | 3 | 12 | High |
| 5. Advanced Rule Management | 3 | 12 | Medium |
| **TOTAL** | **14** | **59** | - |

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Admin permissions required | High | High | Document permission requirements clearly |
| CloudId retrieval complexity | Medium | Medium | Implement helper to fetch from tenant_info |
| API token scope configuration | Medium | High | Provide detailed scope setup guide |
| Complex rule creation via API | High | Medium | Focus on templates; document UI for complex rules |
| Pagination cursor handling | Low | Low | Implement robust pagination logic |
| API rate limiting | Medium | Medium | Implement retry with backoff |

### Permission Requirements

**Required Permissions:**
- **Jira Administrators** global permission (for full rule management)
- **Project Administrator** (for project-scoped rules only)

**Required API Token Scopes:**
- `manage:jira-automation` - For create/update/delete operations
- `read:jira-work` - For list/get operations

**CloudId Requirement:**
- All API calls require Atlassian Cloud ID
- Can be retrieved from `https://{sitename}/_edge/tenant_info`
- Should be cached in configuration

### Known Limitations

1. **Complex Rule Creation:** Very complex rules with nested conditions may require UI
2. **Execution History:** No API for rule execution logs (UI only)
3. **Bulk Operations:** No dedicated bulk enable/disable endpoint (must loop)
4. **Analytics:** No API for rule performance metrics
5. **Audit Trail:** Limited audit information in API responses

---

## Effort Estimates

| Phase | Estimated Hours | Dependencies |
|-------|----------------|--------------|
| Setup (automation_client.py) | 4h | JiraClient, config_manager |
| Phase 1 (Discovery) | 6h | automation_client |
| Phase 2 (State Management) | 4h | Phase 1 |
| Phase 3 (Manual Rules) | 5h | Phase 1 |
| Phase 4 (Creation/Updates) | 8h | Phase 1 |
| Phase 5 (Advanced) | 6h | Phase 4 |
| Documentation | 4h | All phases |
| **TOTAL** | **37h** | - |

---

## Example CLI Usage

### Scenario 1: List and Enable a Rule

```bash
# List all automation rules for project
python list_automation_rules.py --project PROJ

# Find disabled rule
python list_automation_rules.py --project PROJ --state disabled

# Enable specific rule
python enable_automation_rule.py "ari:cloud:jira::site/12345..." --confirm

# Verify state change
python get_automation_rule.py "ari:cloud:jira::site/12345..."
```

### Scenario 2: Create Rule from Template

```bash
# List available templates
python list_automation_templates.py --category "Issue Management"

# Get template details
python get_automation_template.py TEMPLATE_ID

# Create rule from template
python create_rule_from_template.py TEMPLATE_ID \
  --project PROJ \
  --name "Auto-assign critical bugs" \
  --param projectKey=PROJ \
  --param priority=Critical
```

### Scenario 3: Export Rules for Backup

```bash
# Export all rules with full configuration
python export_automation_rules.py --full --output backup_$(date +%Y%m%d).json

# Export only project rules
python export_automation_rules.py --project PROJ --output proj_automation.json
```

### Scenario 4: Invoke Manual Rule

```bash
# List manual rules
python list_manual_rules.py --context issue

# Invoke on specific issue
python invoke_manual_rule.py RULE_ID --issue PROJ-123

# With custom properties
python invoke_manual_rule.py RULE_ID --issue PROJ-123 \
  --property '{"comment": "Automated escalation"}'
```

---

## Implementation Notes

### CloudId Retrieval

Add utility function to shared library:

```python
def get_cloud_id(site_url, email, token):
    """Retrieve Atlassian Cloud ID for a site

    Makes request to https://{site}/_edge/tenant_info
    Caches result in config for future use
    """
    tenant_url = f"{site_url}/_edge/tenant_info"
    response = requests.get(tenant_url, auth=(email, token))
    return response.json()['cloudId']
```

### Base URL Construction

```python
def get_automation_base_url(cloud_id, product='jira', use_gateway=False, site_url=None):
    """Construct Automation API base URL

    Args:
        cloud_id: Atlassian cloud ID
        product: 'jira' or 'confluence'
        use_gateway: Use site gateway (for session auth)
        site_url: Required if use_gateway=True

    Returns:
        Base URL for Automation API
    """
    if use_gateway:
        if not site_url:
            raise ValueError("site_url required for gateway auth")
        return f"{site_url}/gateway/api/automation/public/{product}/{cloud_id}"
    else:
        return f"https://api.atlassian.com/automation/public/{product}/{cloud_id}"
```

### Error Handling

Add to `error_handler.py`:

```python
class AutomationError(JiraError):
    """Base class for Automation API errors"""

class AutomationNotFoundError(AutomationError):
    """Rule or template not found"""

class AutomationPermissionError(AutomationError):
    """Insufficient permissions for automation management"""

class AutomationValidationError(AutomationError):
    """Invalid rule configuration"""
```

---

## Sources & References

- [Automation REST API Reference](https://developer.atlassian.com/cloud/automation/rest/)
- [API Changelog - Rule Management GA Announcement](https://developer.atlassian.com/cloud/automation/api/changelog/)
- [Automation Rule Management API EAP Announcement](https://community.atlassian.com/forums/Automation-articles/Automation-Rule-Management-API-is-now-in-Open-EAP-Try-it-out-and/ba-p/3066541)
- [API Base Paths Documentation](https://developer.atlassian.com/cloud/automation/api/base-paths/)
- [Authentication Guide](https://developer.atlassian.com/cloud/automation/security/authentication/)
- [How to extend Automation for Jira with REST API calls](https://support.atlassian.com/automation/kb/how-to-extend-automation-for-jira-with-rest-api-calls/)
- [Automation for Jira via REST API - Developer Community](https://community.developer.atlassian.com/t/automation-for-jira-via-rest-api/46087)
- [Official REST API Feature Request (AUTO-51)](https://jira.atlassian.com/browse/AUTO-51)
- [Having problems with Jira scope for rule management API](https://community.atlassian.com/forums/Jira-Service-Management/Having-problems-with-Jira-scope-for-rule-management-API/qaq-p/3135618)

---

**Document Version:** 1.0
**Created:** 2025-12-26
**Status:** Ready for Implementation
**API Status:** ✅ General Availability (GA as of August 29, 2025)
