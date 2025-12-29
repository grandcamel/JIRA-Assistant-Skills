# Splunk-Assistant-Skills Bootstrap Prompt (Short Version)

Use in a blank project folder to create a Claude Code Skills project for Splunk Search REST API.

---

## Prompt

```
Create "Splunk-Assistant-Skills" - a Claude Code Skills project for Splunk Search REST API automation.

## Reference Architecture

Copy patterns exactly from: https://github.com/grandcamel/jira-assistant-skills

Use the same:
- Directory structure (.claude/skills/{skill-name}/SKILL.md, scripts/, tests/)
- Shared library pattern (.claude/skills/shared/scripts/lib/)
- Configuration system (settings.json, settings.local.json, profiles)
- Error handling (exception hierarchy, handle_splunk_error())
- Testing approach (pytest, unit + live_integration)
- CI/CD (release-please, GitHub Actions)
- CLAUDE.md format

## Splunk-Specific Adaptations

### Environment Variables
- SPLUNK_TOKEN (JWT) OR SPLUNK_USERNAME + SPLUNK_PASSWORD (Basic Auth)
- SPLUNK_SITE_URL, SPLUNK_MANAGEMENT_PORT (default 8089), SPLUNK_PROFILE

### Authentication (supports both methods)
- **JWT Bearer Token** (preferred): `Authorization: Bearer <token>` - best for automation, Cloud
- **Basic Auth** (legacy): username + password - best for on-prem, quick testing
- Base URL: `https://{host}:{port}/services`

### API Endpoints
- v2 (primary): `/services/search/v2/jobs`, `/services/search/v2/jobs/{sid}/results`
- v1 (legacy): `/services/search/jobs`, `/services/saved/searches`

### Shared Library Files
| File | Adaptation |
|------|------------|
| splunk_client.py | Dual auth (JWT Bearer OR Basic), port 8089, /services base |
| validators.py | validate_sid(), validate_spl(), validate_time_modifier() |
| spl_helper.py | NEW: SPL query building, time bounds, field reduction |
| job_poller.py | NEW: Async dispatchState polling, job control |
| time_utils.py | Splunk time modifiers (-1h, @d, now()) |

## Skills to Create (14 total)

| Skill | Purpose | Key Scripts |
|-------|---------|-------------|
| splunk-assistant | Hub/router with 3-level progressive disclosure | SKILL.md with routing table |
| splunk-job | Search job lifecycle | create_job, poll_job, cancel_job, get_job_status |
| splunk-search | SPL execution modes | search_oneshot, search_normal, search_blocking, get_results |
| splunk-export | High-volume streaming | export_results, export_raw, export_with_checkpoint |
| splunk-metadata | Index/source discovery | list_indexes, list_sourcetypes, metadata_search, fieldsummary |
| splunk-lookup | CSV/lookup management | upload_lookup, download_lookup, create_lookup_definition |
| splunk-tag | Knowledge object tags | add_tag, remove_tag, search_by_tag |
| splunk-savedsearch | Reports/schedules | create_savedsearch, run_savedsearch, enable_schedule |
| splunk-rest-admin | REST config access | rest_get, get_server_info, list_users |
| splunk-security | Tokens/RBAC/ACLs | create_token, get_acl, set_acl, check_permission |
| splunk-metrics | mstats/mcatalog | mstats, mcatalog, list_metrics, aggregate_metrics |
| splunk-alert | Alert management | create_alert, get_triggered_alerts, acknowledge_alert |
| splunk-app | App management | list_apps, install_app, create_app, export_app |
| splunk-kvstore | Key-Value Store | create_collection, insert_record, query_collection |

## Progressive Disclosure (splunk-assistant)

**Level 1 - Connection**: HTTPS to Search Head:8089, valid JWT, detect Cloud vs on-prem
**Level 2 - Mode Selection**: Oneshot for ad-hoc, Export for ETL, Normal+polling for async
**Level 3 - Optimization**: Enforce time bounds, field reduction, job cleanup, strict=true

## Search Modes
```spl
# Oneshot - ad-hoc, results inline
POST /services/search/jobs/oneshot
search=index=main | head 10&output_mode=json

# Normal - async, returns SID
POST /services/search/v2/jobs
search=index=main | stats count&exec_mode=normal

# Export - streaming for large results
GET /services/search/v2/jobs/{sid}/results
output_mode=csv&count=0
```

## SPL Patterns (like JQL)
```spl
# Always include time!
index=main earliest=-1h latest=now | head 100

# Field reduction
index=main | fields host, status, uri | stats count by status

# Metrics
| mstats avg(cpu.percent) WHERE index=metrics BY host span=1h

# Metadata discovery
| metadata type=sourcetypes index=main
```

## Implementation Order
1. Shared library (client, config, errors, validators, spl_helper, job_poller)
2. splunk-job, splunk-search, splunk-export
3. splunk-metadata, splunk-lookup, splunk-tag
4. splunk-savedsearch, splunk-alert
5. splunk-rest-admin, splunk-security, splunk-app, splunk-kvstore
6. splunk-metrics, splunk-assistant
7. Tests, CI/CD, README

Start with Phase 1. Create complete, tested, production-ready code.
```

---

## Usage

```bash
mkdir Splunk-Assistant-Skills && cd Splunk-Assistant-Skills && git init
# Start Claude Code, paste prompt above
```
