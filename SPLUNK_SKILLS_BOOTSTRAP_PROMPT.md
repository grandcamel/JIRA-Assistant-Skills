# Splunk-Assistant-Skills Bootstrap Prompt

Use this prompt in a blank project folder to bootstrap a Claude Code Skills project for Splunk Search REST API automation, following the same architecture as the JIRA Assistant Skills project.

---

## Prompt

```
Create a Claude Code Skills project called "Splunk-Assistant-Skills" for Splunk Search REST API automation.

## Project Goals

Build a modular, production-ready skills framework for Splunk that:
1. Enables natural language interaction with Splunk via Claude Code
2. Provides autonomous skill discovery and routing with 3-level progressive disclosure
3. Uses the Splunk REST API v2 endpoints (with v1 fallback for legacy operations)
4. Follows the exact architecture patterns from the JIRA Assistant Skills project
5. Includes comprehensive testing (unit + live integration)

## Architecture Requirements

### Directory Structure

```
Splunk-Assistant-Skills/
├── .claude/
│   ├── settings.json              # Team defaults (committed)
│   ├── settings.local.json        # Personal credentials (gitignored)
│   └── skills/
│       ├── splunk-assistant/      # Hub/router with progressive disclosure
│       │   ├── SKILL.md
│       │   └── docs/
│       ├── splunk-job/            # Search job lifecycle orchestration
│       │   ├── SKILL.md
│       │   ├── scripts/
│       │   ├── tests/
│       │   └── references/
│       ├── splunk-search/         # SPL query execution
│       ├── splunk-export/         # High-volume streaming extraction
│       ├── splunk-metadata/       # Index, source, sourcetype configs
│       ├── splunk-lookup/         # CSV and lookup file management
│       ├── splunk-tag/            # Knowledge object tags
│       ├── splunk-savedsearch/    # Reports and scheduled searches
│       ├── splunk-rest-admin/     # Internal system configurations
│       ├── splunk-security/       # Token management, RBAC, ACLs
│       ├── splunk-metrics/        # Real-time metrics (mstats, mcatalog)
│       ├── splunk-alert/          # Alert triggering and monitoring
│       ├── splunk-app/            # Splunk application management
│       ├── splunk-kvstore/        # App Key Value Store
│       └── shared/
│           ├── scripts/lib/
│           │   ├── __init__.py
│           │   ├── splunk_client.py      # HTTP client with retry
│           │   ├── config_manager.py     # Multi-source config
│           │   ├── error_handler.py      # Exception hierarchy
│           │   ├── validators.py         # Input validation
│           │   ├── formatters.py         # Output formatting
│           │   ├── spl_helper.py         # SPL query building/parsing
│           │   ├── job_poller.py         # Async job state polling
│           │   ├── time_utils.py         # Splunk time modifier handling
│           │   └── requirements.txt
│           ├── config/
│           │   ├── config.schema.json
│           │   └── config.example.json
│           └── tests/
│               ├── conftest.py
│               └── live_integration/
├── .github/
│   └── workflows/
│       └── release.yml            # Release Please + tests
├── .gitignore
├── CLAUDE.md                      # Project instructions
├── README.md
├── CHANGELOG.md
├── VERSION
├── release-please-config.json
└── .release-please-manifest.json
```

### Shared Library Components

#### splunk_client.py
HTTP client for Splunk REST API:
- **Dual authentication support**:
  - JWT Bearer token: `Authorization: Bearer <token>` (preferred for automation)
  - Basic Auth: username + password (legacy, on-prem compatibility)
- Auto-detect auth method from config (token present = Bearer, else Basic)
- Automatic retry with exponential backoff on 429/5xx
- Configurable timeout (default 30s, extended for long searches)
- Methods: get(), post(), put(), delete(), upload_file(), stream_results()
- Base URL: `https://{host}:{port}/services` (default port 8089)
- Content negotiation: `output_mode=json` for JSON responses
- API paths:
  - v2: `/services/search/v2/jobs`, `/services/search/v2/jobs/{sid}/results`
  - v1: `/services/search/jobs`, `/services/saved/searches` (legacy fallback)

```python
class SplunkClient:
    def __init__(self, base_url: str, token: str = None, username: str = None,
                 password: str = None, port: int = 8089, timeout: int = 30):
        self.base_url = f"{base_url}:{port}/services"
        self.session = requests.Session()
        self.session.headers['Content-Type'] = 'application/x-www-form-urlencoded'

        # Dual auth: prefer JWT token, fall back to Basic Auth
        if token:
            self.session.headers['Authorization'] = f'Bearer {token}'
            self.auth_method = 'bearer'
        elif username and password:
            self.session.auth = (username, password)
            self.auth_method = 'basic'
        else:
            raise ValueError("Must provide either token or username+password")

        self.timeout = timeout
        self.max_retries = 3
        self.retry_backoff = 2.0
```

#### config_manager.py
Adapt from JIRA's pattern:
- Environment variables:
  - `SPLUNK_TOKEN` - JWT Bearer token (preferred)
  - `SPLUNK_USERNAME`, `SPLUNK_PASSWORD` - Basic Auth (alternative)
  - `SPLUNK_SITE_URL`, `SPLUNK_MANAGEMENT_PORT`, `SPLUNK_PROFILE`
- Auth priority: token > username+password (auto-detect which is configured)
- Config priority: env vars > settings.local.json > settings.json > defaults
- Profile support for multiple Splunk instances (dev/staging/prod, cloud/on-prem)
- Convenience function: `get_splunk_client(profile=None)`
- Auto-detect deployment type (Cloud vs on-premises) from URL pattern

#### error_handler.py
Exception hierarchy for Splunk:
- `SplunkError` (base)
- `AuthenticationError` (401 - invalid/expired token)
- `AuthorizationError` (403 - insufficient permissions/capability)
- `ValidationError` (400 - invalid SPL, bad parameters)
- `NotFoundError` (404 - SID not found, endpoint missing)
- `RateLimitError` (429 - too many concurrent searches)
- `SearchQuotaError` (503 - search slot exhausted)
- `JobFailedError` (search job failed state)
- `ServerError` (5xx)
- `handle_splunk_error(response, operation)` function
- `sanitize_error_message()` for sensitive data
- `print_error()` and `@handle_errors` decorator

#### validators.py
Splunk-specific validators:
- `validate_sid(sid)` - Search ID format
- `validate_spl(spl)` - Basic SPL syntax validation
- `validate_time_modifier(time_str)` - Splunk time format (-1h, @d, etc.)
- `validate_index_name(index)` - Index naming rules
- `validate_app_name(app)` - App naming conventions
- `validate_port(port)` - Valid port range
- `validate_url(url)` - HTTPS required for production
- `validate_output_mode(mode)` - json, csv, xml, raw

#### formatters.py
Splunk-specific formatting:
- `format_search_results(results, fields=None)` - Tabular display
- `format_job_status(job)` - Job state and progress
- `format_metadata(meta)` - Index/source/sourcetype info
- `format_saved_search(search)` - Saved search details
- `format_table(data, columns, headers)` - Tabular output
- `format_json(data, pretty=True)`
- `export_csv(data, file_path, columns)`
- `print_success()`, `print_warning()`, `print_info()`

#### spl_helper.py
SPL query building and parsing:
- `build_search(base_query, **kwargs)` - Add time, fields, head
- `add_time_bounds(spl, earliest, latest)` - Insert time modifiers
- `add_field_extraction(spl, fields)` - Add fields command
- `validate_spl_syntax(spl)` - Basic syntax check
- `parse_spl_commands(spl)` - Extract command pipeline
- `estimate_search_complexity(spl)` - Simple/medium/complex
- `optimize_spl(spl)` - Add best-practice transformations

#### job_poller.py
Asynchronous job state management:
- `poll_job_status(client, sid, timeout=300)` - Wait for DONE state
- `get_dispatch_state(client, sid)` - Current job state
- `JobState` enum: QUEUED, PARSING, RUNNING, FINALIZING, DONE, FAILED, PAUSED
- `cancel_job(client, sid)` - Issue /control/cancel
- `finalize_job(client, sid)` - Issue /control/finalize

#### time_utils.py
Splunk time modifier handling:
- `parse_splunk_time(time_str)` - Parse -1h@h, @d, now(), etc.
- `format_splunk_time(datetime)` - Convert to Splunk format
- `validate_time_range(earliest, latest)` - Ensure earliest < latest
- `get_relative_time(offset, snap_to=None)` - Build relative time
- Time modifiers: `-1h`, `-7d@d`, `@w0`, `earliest=0`, `now()`

### Skills Specification

#### 1. splunk-assistant (Hub/Router with Progressive Disclosure)
Routes to specialized skills based on natural language intent.
Implements 3-level progressive disclosure for best practices.

**Level 1: Essential Connection & Identification**
- Verify Search Head connection on management port 8089 via HTTPS
- Validate JWT Bearer token existence and format
- Detect deployment type (Cloud: `https://<deployment>.splunkcloud.com:8089` vs on-prem)
- Route to appropriate skill based on intent

**Level 2: Execution Mode Strategy**
- Auto-select **Oneshot mode** for ad-hoc queries (minimize disk I/O)
- Use **Export mode** for ETL/large transfers (streaming stability)
- Implement async polling for normal jobs (wait for DONE state)
- Recommend blocking mode for simple, fast queries

**Level 3: Advanced Optimization & Resource Governance**
- **Strict Time Modifiers**: Enforce `earliest_time` and `latest_time` on every search
- **Field Reduction**: Insert `fields` command to limit data transfer
- **Resource Cleanup**: Issue `/control/cancel` after results consumed
- **Error Handling**: Use `strict=true` for clear errors vs incomplete data

**Triggers**: Any Splunk-related request, routes to specialized skills

#### 2. splunk-job
**Purpose**: Search job lifecycle orchestration
**Scripts**:
- `create_job.py` - Create search job, return SID
- `get_job_status.py` - Get dispatchState, progress, stats
- `poll_job.py` - Wait for job completion with timeout
- `cancel_job.py` - Issue /control/cancel action
- `pause_job.py` - Issue /control/pause action
- `unpause_job.py` - Issue /control/unpause action
- `finalize_job.py` - Issue /control/finalize action
- `set_job_ttl.py` - Extend job time-to-live
- `list_jobs.py` - List all search jobs for user
- `delete_job.py` - Remove job from dispatch directory

**dispatchState Values**:
- QUEUED → PARSING → RUNNING → FINALIZING → DONE
- FAILED (on error), PAUSED (on pause)

**Triggers**: "job", "search job", "SID", "status", "cancel", "pause"

#### 3. splunk-search
**Purpose**: SPL query execution in multiple modes
**Scripts**:
- `search_oneshot.py` - Execute oneshot search (results inline, no SID)
- `search_normal.py` - Execute normal search (returns SID, poll for results)
- `search_blocking.py` - Execute blocking search (wait for completion)
- `get_results.py` - Retrieve results from completed job
- `get_preview.py` - Get partial results during search
- `search_interactive.py` - Interactive SPL builder with suggestions
- `validate_spl.py` - Validate SPL syntax before execution

**Search Modes**:
```
# Oneshot - ad-hoc, results inline, no job created
POST /services/search/jobs/oneshot
search=<SPL>&output_mode=json&earliest_time=-1h

# Normal - async, returns SID immediately
POST /services/search/v2/jobs
search=<SPL>&exec_mode=normal

# Blocking - sync, waits for completion
POST /services/search/v2/jobs
search=<SPL>&exec_mode=blocking
```

**Triggers**: "search", "SPL", "query", "find", "oneshot", "blocking"

#### 4. splunk-export
**Purpose**: High-volume streaming data extraction (>50,000 rows)
**Scripts**:
- `export_results.py` - Stream results to file (CSV/JSON/XML)
- `export_raw.py` - Export raw events
- `export_with_checkpoint.py` - Resume-capable export with checkpoints
- `estimate_export_size.py` - Preview result count before export
- `schedule_export.py` - Schedule recurring export job

**Export Endpoint**:
```
GET /services/search/v2/jobs/{sid}/results
output_mode=csv&count=0  # count=0 for all results
```

**Triggers**: "export", "download", "extract", "stream", "large results"

#### 5. splunk-metadata
**Purpose**: Query index, source, sourcetype configurations
**Scripts**:
- `list_indexes.py` - List available indexes
- `get_index_info.py` - Index size, event count, time range
- `list_sources.py` - Unique sources per index
- `list_sourcetypes.py` - Sourcetypes in use
- `metadata_search.py` - Execute `| metadata` search
- `metasearch.py` - Execute `| metasearch` for discovery
- `get_field_summary.py` - Field summary for index/sourcetype

**Metadata SPL**:
```spl
| metadata type=sourcetypes index=main
| metasearch index=* sourcetype=access_combined
| fieldsummary maxvals=100
```

**Triggers**: "metadata", "index", "source", "sourcetype", "fields"

#### 6. splunk-lookup
**Purpose**: CSV and lookup file management
**Scripts**:
- `upload_lookup.py` - Upload CSV lookup file
- `download_lookup.py` - Download lookup file
- `list_lookups.py` - List lookup files in app
- `delete_lookup.py` - Remove lookup file
- `update_lookup_row.py` - Add/update lookup row via KV store
- `create_lookup_definition.py` - Create lookup-table stanza
- `get_lookup_definition.py` - Get lookup configuration
- `test_lookup.py` - Test lookup with sample input

**Endpoints**:
```
# Upload lookup
POST /services/data/lookup-table-files
# List lookups
GET /services/data/lookup-table-files
# Lookup definition
GET /services/data/transforms/lookups/{name}
```

**Triggers**: "lookup", "CSV", "upload", "lookup table"

#### 7. splunk-tag
**Purpose**: Knowledge object tags and field/value associations
**Scripts**:
- `add_tag.py` - Add tag to field value
- `remove_tag.py` - Remove tag from field value
- `list_tags.py` - List all tags
- `get_tagged_values.py` - Get values for tag
- `search_by_tag.py` - Search using tag= syntax
- `bulk_tag.py` - Tag multiple values at once

**Tag SPL**:
```spl
tag=web_traffic
tag::src_ip=internal
```

**Triggers**: "tag", "label", "classify"

#### 8. splunk-savedsearch
**Purpose**: CRUD for reports and scheduled searches
**Scripts**:
- `create_savedsearch.py` - Create saved search/report
- `get_savedsearch.py` - Get saved search details
- `update_savedsearch.py` - Modify saved search
- `delete_savedsearch.py` - Delete saved search
- `list_savedsearches.py` - List saved searches in app
- `run_savedsearch.py` - Execute saved search on-demand
- `enable_schedule.py` - Enable scheduled execution
- `disable_schedule.py` - Disable scheduling
- `get_savedsearch_history.py` - Get execution history

**Endpoints**:
```
# CRUD
GET/POST/PUT/DELETE /services/saved/searches/{name}
# Run on-demand
POST /services/saved/searches/{name}/dispatch
# History
GET /services/saved/searches/{name}/history
```

**Triggers**: "saved search", "report", "schedule", "alert"

#### 9. splunk-rest-admin
**Purpose**: Programmatic access to internal configurations via `rest` command
**Scripts**:
- `rest_get.py` - GET any REST endpoint
- `rest_post.py` - POST to REST endpoint
- `rest_list.py` - List REST endpoints
- `get_server_info.py` - Server version, build, features
- `get_server_settings.py` - Server configuration
- `get_deployment_info.py` - Deployment type, cluster status
- `list_users.py` - List Splunk users
- `list_roles.py` - List Splunk roles

**REST Command SPL**:
```spl
| rest /services/server/info
| rest /services/authentication/users
| rest /services/admin/conf-times
```

**Triggers**: "rest", "admin", "config", "server", "settings"

#### 10. splunk-security
**Purpose**: Token management, RBAC, and ACL verification
**Scripts**:
- `create_token.py` - Create new JWT token
- `list_tokens.py` - List tokens for user
- `delete_token.py` - Revoke token
- `get_capabilities.py` - Get user capabilities
- `check_permission.py` - Verify access to resource
- `get_acl.py` - Get ACL for knowledge object
- `set_acl.py` - Modify ACL permissions
- `move_object.py` - Move object between apps (via /move)
- `list_roles.py` - List role definitions
- `get_role.py` - Get role capabilities

**Endpoints**:
```
# Tokens
GET/POST/DELETE /services/authorization/tokens
# ACL
GET/POST /services/data/transforms/lookups/{name}/acl
# Move
POST /services/data/transforms/lookups/{name}/move
```

**Triggers**: "token", "permission", "ACL", "security", "RBAC", "role"

#### 11. splunk-metrics
**Purpose**: Real-time metrics and data point analysis
**Scripts**:
- `mstats.py` - Execute mstats command for metrics
- `mcatalog.py` - Query metrics catalog
- `list_metric_indexes.py` - List metric indexes
- `list_metrics.py` - List metric names in index
- `get_metric_dimensions.py` - Get dimensions for metric
- `metric_search.py` - Build metrics search
- `aggregate_metrics.py` - Common aggregation patterns

**Metrics SPL**:
```spl
| mstats avg(cpu.percent) WHERE index=metrics BY host span=1h
| mcatalog values(metric_name) WHERE index=metrics
| mpreview index=metrics
```

**Triggers**: "metrics", "mstats", "mcatalog", "time series"

#### 12. splunk-alert
**Purpose**: Alert triggering, monitoring, and notification management
**Scripts**:
- `create_alert.py` - Create alert from saved search
- `get_alert.py` - Get alert configuration
- `update_alert.py` - Modify alert settings
- `delete_alert.py` - Delete alert
- `list_alerts.py` - List configured alerts
- `get_triggered_alerts.py` - List triggered alert instances
- `acknowledge_alert.py` - Acknowledge triggered alert
- `suppress_alert.py` - Suppress alert temporarily
- `test_alert_action.py` - Test alert action without trigger

**Alert Actions**:
- email, webhook, script, custom

**Triggers**: "alert", "trigger", "notification", "monitor"

#### 13. splunk-app
**Purpose**: Splunk application management
**Scripts**:
- `list_apps.py` - List installed apps
- `get_app.py` - Get app details
- `install_app.py` - Install app from file
- `uninstall_app.py` - Remove app
- `enable_app.py` - Enable disabled app
- `disable_app.py` - Disable app
- `update_app.py` - Update app configuration
- `create_app.py` - Create new empty app
- `export_app.py` - Export app as package
- `get_app_conf.py` - Get app-specific configuration

**Endpoints**:
```
GET/POST /services/apps/local
GET/POST/DELETE /services/apps/local/{name}
POST /services/apps/local/{name}/package
```

**Triggers**: "app", "install", "application", "package"

#### 14. splunk-kvstore
**Purpose**: Interaction with App Key Value Store for persistent metadata
**Scripts**:
- `create_collection.py` - Create KV store collection
- `delete_collection.py` - Delete collection
- `list_collections.py` - List collections in app
- `insert_record.py` - Insert record into collection
- `get_record.py` - Get record by _key
- `update_record.py` - Update existing record
- `delete_record.py` - Delete record
- `query_collection.py` - Query with filters
- `batch_insert.py` - Bulk insert records
- `batch_delete.py` - Bulk delete records

**Endpoints**:
```
# Collection
GET/POST/DELETE /services/storage/collections/config
# Data
GET/POST /services/storage/collections/data/{collection}
GET/PUT/DELETE /services/storage/collections/data/{collection}/{key}
```

**KV Store SPL**:
```spl
| inputlookup collection_name
| outputlookup collection_name append=true
```

**Triggers**: "kvstore", "collection", "key-value", "persist"

### Configuration Files

#### .claude/settings.json
```json
{
  "splunk": {
    "default_profile": "production",
    "profiles": {
      "production": {
        "url": "https://splunk.your-company.com",
        "port": 8089,
        "auth_method": "bearer",
        "default_app": "search",
        "default_index": "main",
        "deployment_type": "on-prem"
      },
      "cloud": {
        "url": "https://your-deployment.splunkcloud.com",
        "port": 8089,
        "auth_method": "bearer",
        "default_app": "search",
        "default_index": "main",
        "deployment_type": "cloud"
      },
      "development": {
        "url": "https://splunk-dev.your-company.com",
        "port": 8089,
        "auth_method": "basic",
        "default_app": "search",
        "default_index": "dev_main",
        "deployment_type": "on-prem"
      }
    },
    "api": {
      "timeout": 30,
      "search_timeout": 300,
      "max_retries": 3,
      "retry_backoff": 2.0,
      "default_output_mode": "json",
      "prefer_v2_api": true
    },
    "search_defaults": {
      "earliest_time": "-24h",
      "latest_time": "now",
      "max_count": 50000,
      "status_buckets": 300,
      "auto_cancel": 300
    }
  }
}
```

#### .gitignore
```
# Credentials
.claude/settings.local.json

# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.coverage
htmlcov/

# IDE
.idea/
.vscode/
*.swp

# Build
dist/
*.egg-info/

# OS
.DS_Store
Thumbs.db

# Splunk
*.spl
local/
metadata/local.meta
```

### Testing Requirements

#### Unit Tests
- One test file per script in `{skill}/tests/test_{script}.py`
- Use pytest with fixtures in `conftest.py`
- Mock HTTP responses, never hit real API in unit tests
- Target: Comprehensive coverage matching JIRA skills pattern

#### Live Integration Tests
- Location: `{skill}/tests/live_integration/`
- Require `--profile` argument
- Use session-scoped fixtures for test data setup/teardown
- Create test index at start, clean up at end (if permissions allow)
- Skip destructive tests in CI (use `@pytest.mark.destructive`)
- Respect Splunk license limits in tests

#### CI Workflow (.github/workflows/release.yml)
```yaml
name: Release

on:
  push:
    branches:
      - main

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    outputs:
      release_created: ${{ steps.release.outputs.release_created }}
      tag_name: ${{ steps.release.outputs.tag_name }}
      version: ${{ steps.release.outputs.version }}
    steps:
      - name: Run Release Please
        uses: googleapis/release-please-action@v4
        id: release
        with:
          release-type: simple
          token: ${{ secrets.GITHUB_TOKEN }}

  publish-release:
    needs: release-please
    if: ${{ needs.release-please.outputs.release_created }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r .claude/skills/shared/scripts/lib/requirements.txt

      - name: Run tests
        run: |
          pip install pytest pytest-asyncio
          for skill_dir in .claude/skills/*/tests/; do
            if [ -d "$skill_dir" ]; then
              skill_name=$(basename $(dirname $skill_dir))
              echo "Testing $skill_name..."
              python -m pytest "$skill_dir" -v \
                --ignore="${skill_dir}live_integration" \
                || exit 1
            fi
          done

      - name: Create release archive
        run: |
          VERSION=${{ needs.release-please.outputs.version }}
          mkdir -p dist
          tar -czvf dist/splunk-assistant-skills-${VERSION}.tar.gz \
            --exclude='*/tests/*' \
            --exclude='*/docs/*' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            .claude/skills/ \
            CLAUDE.md \
            README.md \
            VERSION

      - name: Upload release assets
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          VERSION=${{ needs.release-please.outputs.version }}
          gh release upload v${VERSION} dist/splunk-assistant-skills-${VERSION}.tar.gz --clobber
```

### CLAUDE.md Template

Create a comprehensive CLAUDE.md following this structure:
1. Project Overview - list all 14 skills
2. Architecture - shared library pattern, import pattern
3. Configuration System - multi-source, profiles
4. Error Handling Strategy - 4-layer approach
5. Authentication - JWT Bearer token setup
6. SPL Query Patterns - examples by use case
7. Search Modes - Oneshot vs Normal vs Blocking vs Export
8. Job Lifecycle - dispatchState flow, polling, cleanup
9. Progressive Disclosure - 3 levels explained
10. Testing Scripts - how to run tests
11. Adding New Scripts - step-by-step guide
12. Adding New Skills - structure requirements
13. Configuration Changes - schema, validation
14. Credentials Security - never commit tokens
15. Common Patterns - script template, time handling
16. Git Commit Guidelines - Conventional Commits
17. Live Integration Testing - how to run

### Implementation Order

**Phase 1: Foundation**
1. Create directory structure
2. Implement shared library (client, config, errors, validators, formatters)
3. Implement spl_helper.py and job_poller.py
4. Implement time_utils.py for Splunk time modifiers
5. Create settings.json schema and examples
6. Create CLAUDE.md

**Phase 2: Core Search**
7. splunk-job (job lifecycle is foundational)
8. splunk-search (SPL execution modes)
9. splunk-export (high-volume extraction)
10. splunk-assistant (hub routing with progressive disclosure)

**Phase 3: Discovery & Metadata**
11. splunk-metadata (indexes, sources, sourcetypes)
12. splunk-lookup (CSV management)
13. splunk-tag (knowledge object tagging)

**Phase 4: Saved Objects**
14. splunk-savedsearch (reports, schedules)
15. splunk-alert (alert management)

**Phase 5: Administration**
16. splunk-rest-admin (REST configuration access)
17. splunk-security (tokens, RBAC, ACLs)
18. splunk-app (application management)
19. splunk-kvstore (key-value store)

**Phase 6: Advanced**
20. splunk-metrics (mstats, mcatalog)

**Phase 7: Quality**
21. Unit tests for all scripts
22. Live integration tests
23. CI/CD workflow
24. README.md with badges

### API Reference

**Splunk REST API v2** (primary):
- Jobs: `POST/GET /services/search/v2/jobs`
- Job Control: `POST /services/search/v2/jobs/{sid}/control`
- Results: `GET /services/search/v2/jobs/{sid}/results`
- Events: `GET /services/search/v2/jobs/{sid}/events`
- Summary: `GET /services/search/v2/jobs/{sid}/summary`

**Splunk REST API v1** (legacy/fallback):
- Search: `POST /services/search/jobs` (oneshot endpoint)
- Saved Searches: `GET/POST/PUT/DELETE /services/saved/searches`
- Indexes: `GET /services/data/indexes`
- Lookups: `GET/POST /services/data/lookup-table-files`
- Apps: `GET/POST /services/apps/local`
- Users: `GET /services/authentication/users`
- Tokens: `GET/POST/DELETE /services/authorization/tokens`

**Authentication** (supports both methods):
- **JWT Bearer Token** (preferred): `Authorization: Bearer <token>`
  - Token creation: Settings > Tokens in Splunk Web
  - Best for: automation, CI/CD, Splunk Cloud
- **Basic Auth** (legacy): username + password
  - Best for: on-prem environments, quick testing, legacy integrations
- Required capabilities vary by endpoint

**Common Parameters**:
- `output_mode`: json, csv, xml, raw
- `count`: Number of results (0 for all)
- `offset`: Results pagination
- `search`: SPL query string
- `earliest_time`, `latest_time`: Time bounds

### Script Template

Every script should follow this pattern:

```python
#!/usr/bin/env python3
"""
Brief description of what this script does.

Examples:
    python script_name.py "index=main | stats count" --earliest "-1h"
"""

import sys
import argparse
from pathlib import Path

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_splunk_client
from error_handler import handle_errors, print_error, SplunkError
from validators import validate_spl, validate_time_modifier
from formatters import print_success, format_search_results
from spl_helper import build_search, add_time_bounds


@handle_errors
def main():
    parser = argparse.ArgumentParser(
        description='Script description',
        epilog='Examples:\n  python script.py "index=main | head 10" --earliest -1h',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('spl', help='SPL query to execute')
    parser.add_argument('--profile', '-p', help='Splunk profile to use')
    parser.add_argument('--earliest', '-e', default='-24h', help='Earliest time (default: -24h)')
    parser.add_argument('--latest', '-l', default='now', help='Latest time (default: now)')
    parser.add_argument('--output', '-o', choices=['text', 'json', 'csv'], default='text')
    args = parser.parse_args()

    # Validate inputs
    spl = validate_spl(args.spl)
    earliest = validate_time_modifier(args.earliest)
    latest = validate_time_modifier(args.latest)

    # Build optimized search
    search_spl = build_search(spl, earliest_time=earliest, latest_time=latest)

    # Get client
    client = get_splunk_client(profile=args.profile)

    # Perform operation
    result = client.post(
        '/services/search/jobs/oneshot',
        data={'search': search_spl, 'output_mode': 'json'},
        operation='execute search'
    )

    # Output
    if args.output == 'json':
        print(format_json(result))
    elif args.output == 'csv':
        export_csv(result['results'], 'results.csv')
    else:
        print(format_search_results(result))

    print_success(f"Search completed: {len(result.get('results', []))} results")


if __name__ == '__main__':
    main()
```

### SPL Query Patterns

```spl
# Basic search with time bounds (ALWAYS include time!)
index=main earliest=-1h latest=now | head 100

# Field extraction optimization
index=main sourcetype=access_combined | fields host, status, uri | head 1000

# Statistics and aggregation
index=main | stats count by status | sort -count

# Time-based analysis
index=main | timechart span=1h count by sourcetype

# Subsearch
index=main [search index=alerts | fields src_ip | head 1000] | stats count by src_ip

# Transaction
index=main | transaction host maxspan=5m | stats avg(duration)

# Metrics (mstats)
| mstats avg(cpu.percent) WHERE index=metrics BY host span=1h

# Metadata discovery
| metadata type=sourcetypes index=main | table sourcetype, totalCount, lastTime

# REST API access
| rest /services/server/info | table splunk_server, version, build

# Lookup enrichment
index=main | lookup users.csv username OUTPUT department | stats count by department
```

Now create the complete project structure and implement all components in order. Start with Phase 1 (Foundation) and proceed through each phase, creating fully functional skills with tests.
```

---

## Usage Instructions

1. Create a new empty directory:
   ```bash
   mkdir Splunk-Assistant-Skills
   cd Splunk-Assistant-Skills
   git init
   ```

2. Start Claude Code in the directory

3. Paste the prompt above

4. Claude will create the complete project structure following the JIRA Assistant Skills patterns

## Quick Reference: Splunk vs JIRA/Confluence

| Aspect | Splunk | JIRA/Confluence |
|--------|--------|-----------------|
| Auth | JWT Bearer token OR Basic Auth | Basic Auth (email + API token) |
| Base URL | `/services` on port 8089 | `/rest/api/3` or `/api/v2` |
| Query Language | SPL | JQL / CQL |
| Async Pattern | SID polling (dispatchState) | Webhook or polling |
| Pagination | count/offset | startAt/maxResults |
| Content Format | JSON, CSV, XML | ADF, HTML, Plain text |
| Time Format | `-1h`, `@d`, `now()` | ISO 8601, relative dates |

## Splunk-Specific Considerations

1. **Always include time bounds**: Splunk searches without `earliest_time` and `latest_time` scan all data, causing performance issues and potential timeout.

2. **Search modes matter**:
   - **Oneshot**: Best for ad-hoc queries, results inline, no SID
   - **Normal**: Returns SID immediately, poll for completion
   - **Blocking**: Waits synchronously, good for fast queries
   - **Export**: Streaming for large result sets

3. **Resource cleanup**: Always cancel jobs after results are consumed to free search slots.

4. **Field reduction**: Use `| fields field1, field2` early in the pipeline to reduce data transfer.

5. **Cloud vs On-Prem**: URL patterns differ - Cloud uses `*.splunkcloud.com`.
