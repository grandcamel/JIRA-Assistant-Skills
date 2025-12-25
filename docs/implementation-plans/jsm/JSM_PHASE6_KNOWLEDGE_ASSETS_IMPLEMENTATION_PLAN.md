# JSM Phase 6: Knowledge Base & Assets - TDD Implementation Plan

## Overview

**Objective:** Implement Knowledge Base and Assets/Insight CMDB integration using Test-Driven Development (TDD)

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
- **Test Location:** `.claude/skills/jira-jsm/tests/`

**Feature Priority:**
1. **Phase 6.1: Knowledge Base Search** (Self-service deflection)
2. **Phase 6.2: KB Article Retrieval** (Content access)
3. **Phase 6.3: KB Suggestions for Requests** (Automated recommendations)
4. **Phase 6.4: Asset Management** (CMDB operations)
5. **Phase 6.5: Asset Linking** (Request-Asset relationships)
6. **Phase 6.6: Affected Asset Discovery** (Incident impact analysis)

**Implementation Timeline:**
- **Phase 4 Priority** (per JSM Gap Analysis)
- Lower priority than core request management (Phase 1), customers/queues (Phase 2), and approvals (Phase 3)
- Knowledge Base: Medium impact (enables self-service)
- Assets/Insight: High impact for mature ITSM implementations

---

## JIRA Service Management API Reference

### Knowledge Base Endpoints (Service Desk API)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rest/servicedeskapi/servicedesk/{serviceDeskId}/knowledgebase/article` | Search KB articles for service desk |
| GET | `/rest/servicedeskapi/knowledgebase/article` | Get all KB articles |

**Note:** Knowledge Base integration uses Confluence API underneath. JSM provides simplified endpoints.

### Knowledge Base Search Request

```bash
GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/knowledgebase/article?query=authentication&highlight=true
```

**Query Parameters:**
| Parameter | Description |
|-----------|-------------|
| `query` | Search term (searches title and content) |
| `highlight` | Include highlighted excerpts (default: false) |
| `start` | Starting index for pagination (default: 0) |
| `limit` | Maximum results per page (default: 10) |

### Knowledge Base Article Response

```json
{
  "size": 2,
  "start": 0,
  "limit": 10,
  "isLastPage": true,
  "_links": {
    "self": "https://example.atlassian.net/rest/servicedeskapi/servicedesk/1/knowledgebase/article?query=authentication"
  },
  "values": [
    {
      "id": "131073",
      "title": "How to reset your password",
      "excerpt": "If you forgot your <em>password</em>, follow these steps...",
      "source": {
        "type": "confluence",
        "pageId": "131073"
      },
      "_links": {
        "self": "https://example.atlassian.net/wiki/spaces/KB/pages/131073"
      }
    }
  ]
}
```

---

### Assets/Insight API Endpoints (Separate API)

**API Base:** `/rest/insight/1.0/` (requires JSM Premium or Assets license)

**Important:** Assets (formerly Insight) is a separate product with its own API structure.

#### Object Schema Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rest/insight/1.0/objectschema/list` | List all object schemas |
| GET | `/rest/insight/1.0/objectschema/{id}` | Get schema details |

#### Object Type Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rest/insight/1.0/objectschema/{schemaId}/objecttypes/flat` | List all object types in schema |
| GET | `/rest/insight/1.0/objecttype/{id}` | Get object type details |
| GET | `/rest/insight/1.0/objecttype/{id}/attributes` | Get attributes for object type |

#### Object (Asset) Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rest/insight/1.0/object/{id}` | Get object/asset details |
| POST | `/rest/insight/1.0/object/create` | Create new object/asset |
| PUT | `/rest/insight/1.0/object/{id}` | Update object/asset |
| DELETE | `/rest/insight/1.0/object/{id}` | Delete object/asset |
| GET | `/rest/insight/1.0/iql/objects` | Search objects using IQL (Insight Query Language) |

#### Connected Tickets Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rest/insight/1.0/objectconnectedtickets/{objectId}/tickets` | Get issues linked to asset |

### IQL Search Request (Asset Search)

```bash
GET /rest/insight/1.0/iql/objects?objectSchemaId=1&iql=objectType="Server"&page=1&resultsPerPage=25
```

**Query Parameters:**
| Parameter | Description |
|-----------|-------------|
| `objectSchemaId` | Required: Schema ID to search within |
| `iql` | Insight Query Language (e.g., `objectType="Server" AND Status="Active"`) |
| `page` | Page number (1-based) |
| `resultsPerPage` | Results per page (default: 25, max: 100) |
| `includeAttributes` | Include all attributes (default: true) |

### Asset Object Response

```json
{
  "id": "10001",
  "objectKey": "ASSET-123",
  "label": "web-server-01",
  "objectType": {
    "id": "5",
    "name": "Server",
    "icon": {
      "id": "1",
      "name": "Server",
      "url16": "...",
      "url48": "..."
    }
  },
  "attributes": [
    {
      "id": "100",
      "objectTypeAttribute": {
        "id": "10",
        "name": "IP Address",
        "type": 0
      },
      "objectAttributeValues": [
        {
          "value": "192.168.1.100"
        }
      ]
    },
    {
      "id": "101",
      "objectTypeAttribute": {
        "id": "11",
        "name": "Status",
        "type": 1
      },
      "objectAttributeValues": [
        {
          "value": "Active"
        }
      ]
    }
  ],
  "_links": {
    "self": "/rest/insight/1.0/object/10001"
  }
}
```

### Create Asset Request Body

```json
{
  "objectTypeId": "5",
  "attributes": [
    {
      "objectTypeAttributeId": "10",
      "objectAttributeValues": [
        {
          "value": "192.168.1.101"
        }
      ]
    },
    {
      "objectTypeAttributeId": "11",
      "objectAttributeValues": [
        {
          "value": "Active"
        }
      ]
    }
  ]
}
```

### Link Asset to Issue

Assets are linked to issues using standard JIRA issue links or via custom fields:

**Option 1: Custom Field (Recommended)**
```json
{
  "fields": {
    "customfield_10050": ["ASSET-123", "ASSET-124"]
  }
}
```

**Option 2: Issue Links API**
```json
{
  "type": {
    "name": "Relates"
  },
  "inwardIssue": {
    "key": "REQ-123"
  },
  "outwardIssue": {
    "key": "ASSET-456"
  }
}
```

**IQL (Insight Query Language) Examples:**

```
objectType = "Server"
objectType = "Server" AND Status = "Active"
objectType IN ("Server", "Database")
"IP Address" = "192.168.1.100"
"IP Address" LIKE "192.168.1.*"
Created >= "2025-01-01"
```

---

## Test Infrastructure Setup

### Initial Setup Tasks

- [ ] **Setup 6.1:** Create JSM skill directory structure
  - [ ] Create `.claude/skills/jira-jsm/` directory
  - [ ] Create `scripts/` subdirectory (if not exists)
  - [ ] Create `tests/` subdirectory (if not exists)
  - [ ] Update `SKILL.md` with KB and Assets sections
  - **Commit:** `feat(jira-jsm): add Phase 6 KB and Assets infrastructure`

- [ ] **Setup 6.2:** Create test infrastructure
  - [ ] Update `tests/conftest.py` with KB and Assets fixtures
  - [ ] Mock KB article response fixture
  - [ ] Mock Asset object response fixture
  - [ ] Mock Asset schema/type response fixtures
  - **Commit:** `feat(jira-jsm): add Phase 6 KB and Assets infrastructure`

- [ ] **Setup 6.3:** Add JiraClient methods for KB and Assets
  - [ ] `search_knowledge_base(service_desk_id, query, highlight)` - Search KB
  - [ ] `get_kb_articles()` - Get all KB articles
  - [ ] `list_asset_schemas()` - List object schemas
  - [ ] `list_asset_types(schema_id)` - List object types
  - [ ] `search_assets(schema_id, iql, page, per_page)` - IQL search
  - [ ] `get_asset(object_id)` - Get asset details
  - [ ] `create_asset(object_type_id, attributes)` - Create asset
  - [ ] `update_asset(object_id, attributes)` - Update asset
  - [ ] `get_asset_connected_tickets(object_id)` - Get linked issues
  - **Commit:** `feat(jira-jsm): add Phase 6 KB and Assets infrastructure`

---

## Phase 6.1: Search Knowledge Base

### Feature 6.1.1: Search KB Articles

**Script:** `search_kb.py`

**JIRA API:**
- `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/knowledgebase/article`

**Test File:** `tests/test_search_kb.py`

**Test Cases:**
```python
def test_search_kb_basic():
    """Test basic KB search with query term."""
    # Should return matching articles

def test_search_kb_with_highlighting():
    """Test search with excerpts highlighting."""
    # Should include <em> tags around matches

def test_search_kb_pagination():
    """Test handling paginated results."""
    # Should fetch multiple pages if needed

def test_search_kb_no_results():
    """Test behavior when no articles match."""
    # Should display helpful "no results" message

def test_search_kb_invalid_service_desk():
    """Test error when service desk doesn't exist."""
    # Should raise NotFoundError

def test_search_kb_format_text():
    """Test human-readable output format."""
    # Should show formatted table with titles and excerpts

def test_search_kb_format_json():
    """Test JSON output format."""
    # Should return valid JSON with article details
```

**CLI Interface:**
```bash
# Basic search
python search_kb.py --service-desk 1 --query "password reset"

# With highlighting
python search_kb.py --service-desk 1 --query "authentication" --highlight

# Pagination
python search_kb.py --service-desk 1 --query "login" --limit 50

# JSON output
python search_kb.py --service-desk 1 --query "vpn" --output json
```

**Output Example:**
```
Knowledge Base Search Results (3 articles):

Title: How to reset your password
Excerpt: If you forgot your password, follow these steps to reset it...
URL: https://example.atlassian.net/wiki/spaces/KB/pages/131073

Title: Password policy requirements
Excerpt: All passwords must meet the following security requirements...
URL: https://example.atlassian.net/wiki/spaces/KB/pages/131074

Title: Troubleshooting login issues
Excerpt: If you cannot log in, check your password and account status...
URL: https://example.atlassian.net/wiki/spaces/KB/pages/131075
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Supports query terms with proper encoding
- [ ] Optional highlighting for search terms
- [ ] Pagination handling for large result sets
- [ ] Clear output with article titles, excerpts, and links

**Commits:**
1. `test(jira-jsm): add failing tests for KB search`
2. `feat(jira-jsm): implement search_kb.py (7/7 tests passing)`

---

## Phase 6.2: Get KB Article

### Feature 6.2.1: Get KB Article Details

**Script:** `get_kb_article.py`

**JIRA API:**
- `GET /rest/servicedeskapi/knowledgebase/article/{articleId}`
- Uses Confluence API underneath for full content

**Test File:** `tests/test_get_kb_article.py`

**Test Cases:**
```python
def test_get_kb_article_by_id():
    """Test fetching article by ID."""
    # Should return full article content

def test_get_kb_article_with_metadata():
    """Test including metadata (author, created, updated)."""
    # Should show article metadata

def test_get_kb_article_format_text():
    """Test plain text output."""
    # Should format article content as text

def test_get_kb_article_format_html():
    """Test HTML output preservation."""
    # Should preserve HTML formatting

def test_get_kb_article_not_found():
    """Test error when article doesn't exist."""
    # Should raise NotFoundError

def test_get_kb_article_no_permission():
    """Test error when user lacks access."""
    # Should raise PermissionError
```

**CLI Interface:**
```bash
# Get by article ID
python get_kb_article.py --article-id 131073

# With metadata
python get_kb_article.py --article-id 131073 --show-metadata

# HTML format
python get_kb_article.py --article-id 131073 --format html
```

**Output Example:**
```
Knowledge Base Article: How to reset your password

Author: john.doe@company.com
Created: 2025-01-10
Last Updated: 2025-01-15
Space: IT Support

Content:
────────────────────────────────────────────────────────────
If you forgot your password, follow these steps to reset it:

1. Go to the login page
2. Click "Forgot password?"
3. Enter your email address
4. Check your email for reset link
5. Create a new password

Note: Passwords must be at least 8 characters and include
      uppercase, lowercase, and numbers.
────────────────────────────────────────────────────────────
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Retrieves full article content
- [ ] Optional metadata display
- [ ] Supports text and HTML output formats
- [ ] Clear error messages for not found/permission issues

**Commits:**
1. `test(jira-jsm): add failing tests for get KB article`
2. `feat(jira-jsm): implement get_kb_article.py (6/6 tests passing)`

---

## Phase 6.3: Suggest KB Articles for Request

### Feature 6.3.1: AI-Powered KB Suggestions

**Script:** `suggest_kb.py`

**JIRA API:**
- `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/knowledgebase/article` with derived query
- Uses request summary/description to generate search terms

**Test File:** `tests/test_suggest_kb.py`

**Test Cases:**
```python
def test_suggest_kb_from_summary():
    """Test suggesting articles based on request summary."""
    # Should extract keywords and search KB

def test_suggest_kb_from_description():
    """Test suggesting from request description."""
    # Should parse description for keywords

def test_suggest_kb_ranking():
    """Test ranking suggestions by relevance."""
    # Should sort by best match

def test_suggest_kb_max_suggestions():
    """Test limiting number of suggestions."""
    # Should respect max_suggestions parameter

def test_suggest_kb_no_matches():
    """Test when no relevant articles found."""
    # Should display helpful message

def test_suggest_kb_cache_results():
    """Test caching suggestions for similar requests."""
    # Should cache results for performance

def test_suggest_kb_auto_attach():
    """Test automatically attaching suggestions to request as comment."""
    # Should add internal comment with KB links
```

**CLI Interface:**
```bash
# Suggest for a request
python suggest_kb.py --request REQ-123

# Limit suggestions
python suggest_kb.py --request REQ-123 --max-suggestions 3

# Auto-attach as comment
python suggest_kb.py --request REQ-123 --attach-comment

# Use custom query
python suggest_kb.py --request REQ-123 --query "vpn connection"
```

**Output Example:**
```
KB Article Suggestions for REQ-123: "Cannot access VPN"

Suggested articles based on request content:

1. [90% match] How to connect to company VPN
   URL: https://example.atlassian.net/wiki/spaces/KB/pages/131080
   Excerpt: Step-by-step guide for VPN setup on all platforms...

2. [75% match] Troubleshooting VPN connection issues
   URL: https://example.atlassian.net/wiki/spaces/KB/pages/131081
   Excerpt: Common VPN problems and solutions...

3. [60% match] VPN client installation guide
   URL: https://example.atlassian.net/wiki/spaces/KB/pages/131082
   Excerpt: Download and install the VPN client software...

Run with --attach-comment to add these suggestions to the request.
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Extracts keywords from summary and description
- [ ] Ranks suggestions by relevance
- [ ] Limits results to top N suggestions
- [ ] Optional auto-attachment as internal comment
- [ ] Helpful output when no matches found

**Commits:**
1. `test(jira-jsm): add failing tests for KB suggestions`
2. `feat(jira-jsm): implement suggest_kb.py (7/7 tests passing)`

---

## Phase 6.4: List Assets

### Feature 6.4.1: List and Search Assets

**Script:** `list_assets.py`

**JIRA API:**
- `GET /rest/insight/1.0/iql/objects` - IQL search
- `GET /rest/insight/1.0/objectschema/list` - List schemas
- `GET /rest/insight/1.0/objectschema/{id}/objecttypes/flat` - List types

**Test File:** `tests/test_list_assets.py`

**Test Cases:**
```python
def test_list_assets_all():
    """Test listing all assets in schema."""
    # Should return all objects

def test_list_assets_by_type():
    """Test filtering by object type."""
    # Should use IQL: objectType="Server"

def test_list_assets_by_attribute():
    """Test filtering by attribute value."""
    # Should use IQL: Status="Active"

def test_list_assets_complex_query():
    """Test complex IQL query."""
    # Should support AND/OR/IN operators

def test_list_assets_pagination():
    """Test paginated results."""
    # Should handle multiple pages

def test_list_assets_format_table():
    """Test table output format."""
    # Should show key attributes in columns

def test_list_assets_format_json():
    """Test JSON output format."""
    # Should return complete asset objects

def test_list_assets_invalid_schema():
    """Test error when schema doesn't exist."""
    # Should raise NotFoundError
```

**CLI Interface:**
```bash
# List all assets in schema
python list_assets.py --schema-id 1

# Filter by object type
python list_assets.py --schema-id 1 --type Server

# Filter by attribute
python list_assets.py --schema-id 1 --type Server --filter 'Status="Active"'

# Complex IQL query
python list_assets.py --schema-id 1 --iql 'objectType="Server" AND Status="Active" AND "IP Address" LIKE "192.168.*"'

# JSON output
python list_assets.py --schema-id 1 --type Database --output json
```

**Output Example:**
```
Assets in Schema "IT Infrastructure" (25 total):

Object Type: Server
─────────────────────────────────────────────────────────────
Key           Label            IP Address      Status    Location
────────────  ───────────────  ──────────────  ────────  ────────
ASSET-101     web-server-01    192.168.1.100   Active    DC-1
ASSET-102     web-server-02    192.168.1.101   Active    DC-1
ASSET-103     db-server-01     192.168.1.110   Active    DC-2
ASSET-104     app-server-01    192.168.1.120   Inactive  DC-1

Total: 4 servers (3 active, 1 inactive)
```

**Acceptance Criteria:**
- [ ] All 8 tests pass
- [ ] Lists assets with IQL query support
- [ ] Filters by object type and attributes
- [ ] Pagination for large result sets
- [ ] Table and JSON output formats
- [ ] Shows key attributes in readable format

**Commits:**
1. `test(jira-jsm): add failing tests for list assets`
2. `feat(jira-jsm): implement list_assets.py (8/8 tests passing)`

---

## Phase 6.5: Get Asset Details

### Feature 6.5.1: View Asset Information

**Script:** `get_asset.py`

**JIRA API:**
- `GET /rest/insight/1.0/object/{id}` - Get asset details
- `GET /rest/insight/1.0/objectconnectedtickets/{objectId}/tickets` - Get linked issues

**Test File:** `tests/test_get_asset.py`

**Test Cases:**
```python
def test_get_asset_by_id():
    """Test fetching asset by object ID."""
    # Should return complete asset details

def test_get_asset_by_key():
    """Test fetching asset by object key (ASSET-123)."""
    # Should search and return asset

def test_get_asset_with_linked_issues():
    """Test including linked JIRA issues."""
    # Should show connected tickets

def test_get_asset_format_text():
    """Test human-readable output."""
    # Should format attributes clearly

def test_get_asset_format_json():
    """Test JSON output."""
    # Should return complete asset object

def test_get_asset_not_found():
    """Test error when asset doesn't exist."""
    # Should raise NotFoundError
```

**CLI Interface:**
```bash
# Get by object ID
python get_asset.py --id 10001

# Get by object key
python get_asset.py --key ASSET-123

# Include linked issues
python get_asset.py --key ASSET-123 --show-linked-issues

# JSON output
python get_asset.py --key ASSET-123 --output json
```

**Output Example:**
```
Asset: ASSET-123 (web-server-01)
Object Type: Server

Attributes:
─────────────────────────────────────────────
IP Address:        192.168.1.100
Status:            Active
Location:          Data Center 1
Owner:             IT Operations
Serial Number:     SN12345678
Purchase Date:     2023-05-15
Warranty Expiry:   2026-05-15
OS:                Ubuntu 22.04 LTS

Linked Issues (3):
─────────────────────────────────────────────
INC-456: Server high CPU usage
REQ-789: Install monitoring agent
CHG-101: OS security patch update

Last Updated: 2025-01-15 10:30:00
Updated By: john.doe@company.com
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Retrieves asset by ID or key
- [ ] Displays all attributes clearly
- [ ] Optional linked issues display
- [ ] Text and JSON output formats

**Commits:**
1. `test(jira-jsm): add failing tests for get asset`
2. `feat(jira-jsm): implement get_asset.py (6/6 tests passing)`

---

## Phase 6.6: Create/Update Asset

### Feature 6.6.1: Create New Asset

**Script:** `create_asset.py`

**JIRA API:**
- `POST /rest/insight/1.0/object/create`

**Test File:** `tests/test_create_asset.py`

**Test Cases:**
```python
def test_create_asset_minimal():
    """Test creating asset with required fields only."""
    # Should create with objectTypeId and required attributes

def test_create_asset_all_attributes():
    """Test creating asset with all attributes."""
    # Should accept all provided attributes

def test_create_asset_from_json():
    """Test creating from JSON template."""
    # Should read template and create asset

def test_create_asset_validate_attributes():
    """Test validation of required attributes."""
    # Should check required fields before creation

def test_create_asset_invalid_type():
    """Test error when object type doesn't exist."""
    # Should raise ValidationError

def test_create_asset_duplicate_key():
    """Test handling duplicate unique attributes."""
    # Should raise DuplicateError
```

**CLI Interface:**
```bash
# Interactive creation (prompts for attributes)
python create_asset.py --schema-id 1 --type Server

# From JSON template
python create_asset.py --template server_template.json

# Command-line attributes
python create_asset.py --schema-id 1 --type Server \
  --attr "IP Address=192.168.1.105" \
  --attr "Status=Active" \
  --attr "Location=DC-1"

# Dry run
python create_asset.py --template server_template.json --dry-run
```

**Template Example (server_template.json):**
```json
{
  "objectTypeId": "5",
  "attributes": [
    {
      "name": "IP Address",
      "value": "192.168.1.105"
    },
    {
      "name": "Status",
      "value": "Active"
    },
    {
      "name": "Location",
      "value": "Data Center 1"
    },
    {
      "name": "Owner",
      "value": "IT Operations"
    }
  ]
}
```

**Output Example:**
```
Creating asset in schema "IT Infrastructure"...

Object Type: Server
Attributes:
  IP Address: 192.168.1.105
  Status: Active
  Location: Data Center 1
  Owner: IT Operations

✓ Asset created successfully!

Asset Key: ASSET-125
Asset ID: 10025
URL: https://example.atlassian.net/jira/servicedesk/assets/object/10025
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Creates assets with required and optional attributes
- [ ] Supports JSON templates
- [ ] Interactive mode for attribute entry
- [ ] Validates attributes before creation
- [ ] Dry-run mode for preview

**Commits:**
1. `test(jira-jsm): add failing tests for create asset`
2. `feat(jira-jsm): implement create_asset.py (6/6 tests passing)`

---

### Feature 6.6.2: Update Existing Asset

**Script:** `update_asset.py`

**JIRA API:**
- `PUT /rest/insight/1.0/object/{id}`

**Test File:** `tests/test_update_asset.py`

**Test Cases:**
```python
def test_update_asset_single_attribute():
    """Test updating one attribute."""
    # Should update specified attribute only

def test_update_asset_multiple_attributes():
    """Test updating multiple attributes."""
    # Should update all specified attributes

def test_update_asset_from_json():
    """Test updating from JSON template."""
    # Should apply all changes from template

def test_update_asset_validate_changes():
    """Test validation of attribute changes."""
    # Should validate values before updating

def test_update_asset_not_found():
    """Test error when asset doesn't exist."""
    # Should raise NotFoundError

def test_update_asset_read_only_attribute():
    """Test error when trying to update read-only field."""
    # Should raise ValidationError
```

**CLI Interface:**
```bash
# Update single attribute
python update_asset.py --key ASSET-123 --attr "Status=Inactive"

# Update multiple attributes
python update_asset.py --key ASSET-123 \
  --attr "Status=Inactive" \
  --attr "Location=DC-2" \
  --attr "Owner=john.doe@company.com"

# From JSON template
python update_asset.py --key ASSET-123 --template update_template.json

# Dry run
python update_asset.py --key ASSET-123 --attr "Status=Inactive" --dry-run
```

**Output Example:**
```
Updating asset ASSET-123 (web-server-01)...

Changes:
  Status: Active → Inactive
  Location: DC-1 → DC-2
  Owner: IT Operations → john.doe@company.com

✓ Asset updated successfully!

View asset: python get_asset.py --key ASSET-123
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Updates single or multiple attributes
- [ ] Supports JSON templates
- [ ] Shows before/after changes clearly
- [ ] Validates attribute values
- [ ] Dry-run mode for preview

**Commits:**
1. `test(jira-jsm): add failing tests for update asset`
2. `feat(jira-jsm): implement update_asset.py (6/6 tests passing)`

---

## Phase 6.7: Link Asset to Request

### Feature 6.7.1: Create Asset-Request Relationships

**Script:** `link_asset.py`

**JIRA API:**
- `PUT /rest/api/3/issue/{issueIdOrKey}` - Update custom field with asset references
- Or `POST /rest/api/3/issueLink` - Create issue link

**Test File:** `tests/test_link_asset.py`

**Test Cases:**
```python
def test_link_asset_to_request():
    """Test linking asset to request via custom field."""
    # Should update asset custom field

def test_link_multiple_assets():
    """Test linking multiple assets to request."""
    # Should add all assets to custom field array

def test_link_asset_add_comment():
    """Test adding comment about linked asset."""
    # Should create internal comment with asset details

def test_unlink_asset():
    """Test removing asset link from request."""
    # Should remove asset from custom field

def test_link_asset_invalid_request():
    """Test error when request doesn't exist."""
    # Should raise NotFoundError

def test_link_asset_invalid_asset():
    """Test error when asset doesn't exist."""
    # Should raise NotFoundError
```

**CLI Interface:**
```bash
# Link single asset
python link_asset.py --request REQ-123 --asset ASSET-456

# Link multiple assets
python link_asset.py --request REQ-123 --assets ASSET-456,ASSET-457,ASSET-458

# Add comment about link
python link_asset.py --request REQ-123 --asset ASSET-456 --comment "Primary server affected"

# Unlink asset
python link_asset.py --request REQ-123 --asset ASSET-456 --unlink
```

**Output Example:**
```
Linking assets to REQ-123: "VPN connection issue"...

Assets:
  ASSET-456: vpn-gateway-01 (VPN Gateway)
  ASSET-457: firewall-01 (Network Firewall)

✓ Assets linked successfully!

View request: python get_request.py REQ-123
View assets: python get_asset.py --key ASSET-456
```

**Acceptance Criteria:**
- [ ] All 6 tests pass
- [ ] Links assets via custom field
- [ ] Supports multiple asset linking
- [ ] Optional comment about relationship
- [ ] Unlink functionality
- [ ] Clear confirmation messages

**Commits:**
1. `test(jira-jsm): add failing tests for link asset`
2. `feat(jira-jsm): implement link_asset.py (6/6 tests passing)`

---

## Phase 6.8: Find Affected Assets by Incident

### Feature 6.8.1: Impact Analysis and Asset Discovery

**Script:** `find_affected_assets.py`

**JIRA API:**
- `GET /rest/insight/1.0/iql/objects` - IQL search with filters
- `GET /rest/api/3/issue/{issueIdOrKey}` - Get incident details

**Test File:** `tests/test_find_affected_assets.py`

**Test Cases:**
```python
def test_find_assets_by_location():
    """Test finding assets in same location as incident."""
    # Should use location attribute from incident

def test_find_assets_by_service():
    """Test finding assets providing same service."""
    # Should search by service type

def test_find_assets_by_dependency():
    """Test finding dependent assets (upstream/downstream)."""
    # Should traverse asset dependencies

def test_find_assets_by_similar_issue():
    """Test finding assets with similar recent issues."""
    # Should search connected tickets

def test_find_assets_rank_by_impact():
    """Test ranking assets by potential impact."""
    # Should prioritize critical assets

def test_find_assets_format_report():
    """Test generating impact analysis report."""
    # Should create detailed report

def test_find_assets_no_matches():
    """Test when no affected assets found."""
    # Should display helpful message
```

**CLI Interface:**
```bash
# Find by incident
python find_affected_assets.py --incident INC-456

# Find by location
python find_affected_assets.py --incident INC-456 --by-location

# Find by service type
python find_affected_assets.py --incident INC-456 --service "Web Server"

# Include dependencies
python find_affected_assets.py --incident INC-456 --include-dependencies

# Generate impact report
python find_affected_assets.py --incident INC-456 --generate-report
```

**Output Example:**
```
Analyzing incident INC-456: "Web server outage in DC-1"

Directly Affected Assets (3):
─────────────────────────────────────────────
ASSET-101  web-server-01    Critical   DC-1   Active
ASSET-102  web-server-02    Critical   DC-1   Active
ASSET-103  load-balancer-01 High       DC-1   Active

Potentially Affected Assets (5):
─────────────────────────────────────────────
ASSET-104  app-server-01    Medium     DC-1   Active
ASSET-105  app-server-02    Medium     DC-1   Active
ASSET-106  db-server-01     High       DC-1   Active
ASSET-110  monitoring-srv   Low        DC-1   Active
ASSET-115  backup-server    Low        DC-2   Active

Impact Summary:
  Critical assets: 2
  High priority: 2
  Medium priority: 2
  Low priority: 2

Recommended Actions:
  1. Check status of web-server-01 and web-server-02
  2. Verify load balancer configuration
  3. Monitor database server for performance impact
  4. Consider failover to DC-2 if issue persists
```

**Acceptance Criteria:**
- [ ] All 7 tests pass
- [ ] Finds assets by location, service, dependencies
- [ ] Ranks assets by criticality/impact
- [ ] Generates detailed impact analysis
- [ ] Provides actionable recommendations
- [ ] Clear categorization (direct vs. potential impact)

**Commits:**
1. `test(jira-jsm): add failing tests for find affected assets`
2. `feat(jira-jsm): implement find_affected_assets.py (7/7 tests passing)`

---

## Integration Notes

### Knowledge Base Integration

**Requirements:**
- Service desk must have Confluence space linked
- KB articles must be in linked Confluence space
- User must have read access to Confluence pages

**Configuration:**
```python
# In profile config
{
  "use_service_management": true,
  "service_desk_id": 1,
  "kb_auto_suggest": true  # Automatically suggest KB articles for new requests
}
```

**Integration Points:**
1. **create_request.py** - Add KB suggestions to new requests
2. **add_request_comment.py** - Suggest KB articles when adding comments
3. **get_request.py** - Show related KB articles with `--suggest-kb` flag

### Assets/Insight Integration

**Requirements:**
- JSM Premium license OR separate Assets/Insight license
- Assets product installed and configured
- At least one object schema created
- User must have Assets permission (typically JSM agents)

**Configuration:**
```python
# In profile config
{
  "use_service_management": true,
  "assets_enabled": true,
  "default_asset_schema_id": 1,
  "asset_custom_field": "customfield_10050"  # Assets custom field ID
}
```

**Integration Points:**
1. **create_request.py** - Add `--assets` flag to link assets during creation
2. **get_request.py** - Show linked assets with `--show-assets` flag
3. **transition_request.py** - Auto-suggest affected assets when resolving incidents
4. **add_worklog.py** - Reference asset work in worklog comments

### Cross-Feature Integration

**Incident → Assets → KB Workflow:**
```bash
# 1. Find affected assets
python find_affected_assets.py --incident INC-456

# 2. Link assets to incident
python link_asset.py --request INC-456 --assets ASSET-101,ASSET-102

# 3. Search KB for asset-specific troubleshooting
python search_kb.py --service-desk 1 --query "web server troubleshooting"

# 4. Add resolution with KB article reference
python add_request_comment.py INC-456 \
  --body "Issue resolved. See KB article: https://..." \
  --public
```

---

## Success Metrics

### Completion Criteria

**Tests:**
- [ ] 51 unit tests passing (7+6+7+8+6+6+6+5)
- [ ] Coverage: 85%+ for all scripts
- [ ] Live integration tests for KB and Assets APIs

**Scripts:**
- [ ] 8 new scripts implemented
  - [ ] search_kb.py
  - [ ] get_kb_article.py
  - [ ] suggest_kb.py
  - [ ] list_assets.py
  - [ ] get_asset.py
  - [ ] create_asset.py
  - [ ] update_asset.py
  - [ ] link_asset.py
  - [ ] find_affected_assets.py
- [ ] All scripts have `--help`
- [ ] All scripts support `--profile`
- [ ] Mutation scripts have `--dry-run`

**Documentation:**
- [ ] SKILL.md updated with KB and Assets sections
- [ ] JSM_GAP_ANALYSIS.md updated (Categories K & L)
- [ ] All scripts have comprehensive docstrings
- [ ] KB and Assets workflow examples

**Integration:**
- [ ] Update create_request.py with `--assets` and `--suggest-kb` flags
- [ ] Update get_request.py with `--show-assets` and `--show-kb` flags
- [ ] No breaking changes to existing scripts

### Progress Tracking

**Test Status:** 0/51 tests passing

**Phase Status:**
- [ ] Phase 6.1: KB Search (7 tests)
- [ ] Phase 6.2: Get KB Article (6 tests)
- [ ] Phase 6.3: Suggest KB (7 tests)
- [ ] Phase 6.4: List Assets (8 tests)
- [ ] Phase 6.5: Get Asset (6 tests)
- [ ] Phase 6.6: Create/Update Asset (12 tests)
- [ ] Phase 6.7: Link Asset (6 tests)
- [ ] Phase 6.8: Find Affected Assets (7 tests)
- [ ] Integration (KB + Assets)
- [ ] Documentation
- [ ] Live integration tests

---

## Script Summary

| Script | Phase | Tests | Status | Description |
|--------|-------|-------|--------|-------------|
| `search_kb.py` | 6.1 | 7 | ⏸️ | Search KB articles by query |
| `get_kb_article.py` | 6.2 | 6 | ⏸️ | Retrieve full KB article content |
| `suggest_kb.py` | 6.3 | 7 | ⏸️ | AI-powered KB suggestions for requests |
| `list_assets.py` | 6.4 | 8 | ⏸️ | List/search assets with IQL |
| `get_asset.py` | 6.5 | 6 | ⏸️ | View asset details and linked issues |
| `create_asset.py` | 6.6a | 6 | ⏸️ | Create new asset/CMDB object |
| `update_asset.py` | 6.6b | 6 | ⏸️ | Update asset attributes |
| `link_asset.py` | 6.7 | 6 | ⏸️ | Link assets to requests |
| `find_affected_assets.py` | 6.8 | 7 | ⏸️ | Impact analysis for incidents |
| **Total** | - | **59** | 0 ⏸️ | - |

---

## JiraClient Methods to Add

```python
# In shared/scripts/lib/jira_client.py

# Knowledge Base Methods
def search_knowledge_base(self, service_desk_id: int, query: str,
                          highlight: bool = False, start: int = 0,
                          limit: int = 10) -> dict:
    """Search KB articles for a service desk.

    Args:
        service_desk_id: Service desk ID
        query: Search query string
        highlight: Include highlighted excerpts
        start: Starting index for pagination
        limit: Maximum results per page

    Returns:
        KB search results with articles
    """
    params = {
        'query': query,
        'highlight': highlight,
        'start': start,
        'limit': limit
    }
    return self.get(
        f'/rest/servicedeskapi/servicedesk/{service_desk_id}/knowledgebase/article',
        params=params
    )

def get_kb_articles(self) -> dict:
    """Get all KB articles accessible to user.

    Returns:
        All KB articles
    """
    return self.get('/rest/servicedeskapi/knowledgebase/article')


# Assets/Insight Methods
def list_asset_schemas(self) -> list:
    """List all object schemas in Assets.

    Returns:
        List of object schemas
    """
    result = self.get('/rest/insight/1.0/objectschema/list')
    return result.get('objectschemas', [])

def list_asset_types(self, schema_id: int) -> list:
    """List all object types in a schema.

    Args:
        schema_id: Object schema ID

    Returns:
        List of object types
    """
    result = self.get(
        f'/rest/insight/1.0/objectschema/{schema_id}/objecttypes/flat'
    )
    return result.get('objectTypes', [])

def search_assets(self, schema_id: int, iql: str = None,
                  page: int = 1, per_page: int = 25) -> dict:
    """Search assets using IQL (Insight Query Language).

    Args:
        schema_id: Object schema ID to search within
        iql: IQL query (e.g., 'objectType="Server" AND Status="Active"')
        page: Page number (1-based)
        per_page: Results per page (max 100)

    Returns:
        Search results with asset objects
    """
    params = {
        'objectSchemaId': schema_id,
        'page': page,
        'resultsPerPage': min(per_page, 100),
        'includeAttributes': True
    }
    if iql:
        params['iql'] = iql

    return self.get('/rest/insight/1.0/iql/objects', params=params)

def get_asset(self, object_id: int) -> dict:
    """Get asset details by object ID.

    Args:
        object_id: Object/asset ID

    Returns:
        Asset object with all attributes
    """
    return self.get(f'/rest/insight/1.0/object/{object_id}')

def create_asset(self, object_type_id: int, attributes: list) -> dict:
    """Create a new asset/CMDB object.

    Args:
        object_type_id: Object type ID
        attributes: List of attribute dicts with objectTypeAttributeId and values

    Returns:
        Created asset object
    """
    payload = {
        'objectTypeId': object_type_id,
        'attributes': attributes
    }
    return self.post('/rest/insight/1.0/object/create', data=payload)

def update_asset(self, object_id: int, attributes: list) -> dict:
    """Update an existing asset.

    Args:
        object_id: Object/asset ID
        attributes: List of attribute dicts to update

    Returns:
        Updated asset object
    """
    payload = {
        'objectId': object_id,
        'attributes': attributes
    }
    return self.put(f'/rest/insight/1.0/object/{object_id}', data=payload)

def get_asset_connected_tickets(self, object_id: int) -> list:
    """Get JIRA issues linked to an asset.

    Args:
        object_id: Object/asset ID

    Returns:
        List of connected issue keys
    """
    result = self.get(
        f'/rest/insight/1.0/objectconnectedtickets/{object_id}/tickets'
    )
    return result.get('tickets', [])
```

---

## Helper Functions

### IQL Query Builder

```python
# In jira-jsm/scripts/lib/iql_utils.py (new file)

from typing import List, Dict

class IQLQueryBuilder:
    """Builder for Insight Query Language (IQL) queries."""

    def __init__(self):
        self.conditions = []

    def object_type(self, type_name: str) -> 'IQLQueryBuilder':
        """Add object type condition.

        Args:
            type_name: Object type name

        Returns:
            Self for chaining
        """
        self.conditions.append(f'objectType="{type_name}"')
        return self

    def attribute_equals(self, attr_name: str, value: str) -> 'IQLQueryBuilder':
        """Add attribute equals condition.

        Args:
            attr_name: Attribute name
            value: Attribute value

        Returns:
            Self for chaining
        """
        self.conditions.append(f'"{attr_name}"="{value}"')
        return self

    def attribute_like(self, attr_name: str, pattern: str) -> 'IQLQueryBuilder':
        """Add attribute LIKE condition.

        Args:
            attr_name: Attribute name
            pattern: Pattern with * wildcards

        Returns:
            Self for chaining
        """
        self.conditions.append(f'"{attr_name}" LIKE "{pattern}"')
        return self

    def attribute_in(self, attr_name: str, values: List[str]) -> 'IQLQueryBuilder':
        """Add attribute IN condition.

        Args:
            attr_name: Attribute name
            values: List of possible values

        Returns:
            Self for chaining
        """
        value_list = ', '.join(f'"{v}"' for v in values)
        self.conditions.append(f'"{attr_name}" IN ({value_list})')
        return self

    def build(self) -> str:
        """Build final IQL query string.

        Returns:
            IQL query string
        """
        return ' AND '.join(self.conditions)


def parse_iql_filter(filter_str: str) -> str:
    """Parse user-friendly filter to IQL.

    Examples:
        >>> parse_iql_filter('Status=Active')
        '"Status"="Active"'
        >>> parse_iql_filter('IP like 192.168.*')
        '"IP" LIKE "192.168.*"'

    Args:
        filter_str: User-friendly filter string

    Returns:
        IQL query string
    """
    # Simple parser - can be extended
    if '=' in filter_str and ' like ' not in filter_str.lower():
        parts = filter_str.split('=', 1)
        return f'"{parts[0].strip()}"="{parts[1].strip()}"'
    elif ' like ' in filter_str.lower():
        parts = filter_str.lower().split(' like ', 1)
        return f'"{parts[0].strip()}" LIKE "{parts[1].strip()}"'
    return filter_str
```

### KB Keyword Extraction

```python
# In jira-jsm/scripts/lib/kb_utils.py (new file)

import re
from typing import List

def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """Extract keywords from text for KB search.

    Args:
        text: Text to extract keywords from (summary, description)
        max_keywords: Maximum number of keywords to extract

    Returns:
        List of keywords
    """
    # Remove common words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
        'to', 'from', 'in', 'on', 'at', 'for', 'with', 'by', 'of', 'i',
        'my', 'me', 'we', 'our', 'you', 'your', 'it', 'its', 'this', 'that'
    }

    # Extract words (alphanumeric sequences)
    words = re.findall(r'\b[a-z0-9]+\b', text.lower())

    # Filter stop words and short words
    keywords = [w for w in words if w not in stop_words and len(w) > 2]

    # Count frequency
    word_freq = {}
    for word in keywords:
        word_freq[word] = word_freq.get(word, 0) + 1

    # Sort by frequency and take top N
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]


def build_kb_query(summary: str, description: str = None) -> str:
    """Build KB search query from request summary and description.

    Args:
        summary: Request summary
        description: Optional request description

    Returns:
        KB search query string
    """
    text = summary
    if description:
        text += ' ' + description

    keywords = extract_keywords(text, max_keywords=3)
    return ' '.join(keywords)
```

---

## Commit Strategy

### Commit Types

**test:** Adding or updating tests
- `test(jira-jsm): add failing tests for KB search`

**feat:** Implementing features
- `feat(jira-jsm): implement search_kb.py (7/7 tests passing)`

**docs:** Documentation updates
- `docs(jira-jsm): add KB and Assets examples to SKILL.md`

**fix:** Bug fixes
- `fix(jira-jsm): handle Assets API pagination correctly`

---

## API Sources

### Knowledge Base
- [JSM Knowledge Base API](https://developer.atlassian.com/cloud/jira/service-desk/rest/api-group-knowledgebase/)
- [Confluence REST API](https://developer.atlassian.com/cloud/confluence/rest/v1/intro/) (underlying KB storage)

### Assets/Insight
- [Assets (Insight) REST API v1](https://developer.atlassian.com/cloud/jira/service-management/rest/api-group-assets/)
- [Assets REST API Documentation](https://docs.atlassian.com/jira-servicedesk/REST/assets/latest/)
- [IQL (Insight Query Language) Reference](https://support.atlassian.com/jira-service-management-cloud/docs/use-insight-query-language-iql/)
- [Assets/Insight Configuration](https://support.atlassian.com/jira-service-management-cloud/docs/get-started-with-assets-in-jira-service-management/)

### License Requirements
- **Knowledge Base:** Included with JSM Standard/Premium
- **Assets/Insight:** Requires JSM Premium OR separate Assets license

---

**Plan Version:** 1.0
**Created:** 2025-12-25
**Status:** DRAFT - Ready for TDD implementation
**Implementation Priority:** Phase 4 (per JSM Gap Analysis)
**Estimated Effort:** ~28 hours (KB: 12h, Assets: 16h)
