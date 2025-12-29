# Splunk-Assistant-Skills Bootstrap Prompt (Minimal)

```
Create "Splunk-Assistant-Skills" for Splunk Search REST API automation.

## Pattern Source
Clone architecture from: https://github.com/grandcamel/jira-assistant-skills
- Same directory structure, shared library, config system, testing, CI/CD

## Key Differences from JIRA
- Env vars: SPLUNK_TOKEN (JWT) OR SPLUNK_USERNAME + SPLUNK_PASSWORD (Basic Auth)
- SPLUNK_SITE_URL, SPLUNK_MANAGEMENT_PORT (8089)
- Auth: JWT Bearer token (preferred) OR Basic Auth (on-prem/legacy)
- Base URL: /services on port 8089
- APIs: v2 (/services/search/v2/jobs) + v1 fallback (/services/saved/searches)
- Add spl_helper.py for SPL query building + job_poller.py for async SID polling
- SPL instead of JQL/CQL

## Skills (14)
1. splunk-assistant - Hub/router with 3-level progressive disclosure
2. splunk-job - Search job lifecycle (SID, dispatchState, /control)
3. splunk-search - SPL execution (Oneshot, Normal, Blocking modes)
4. splunk-export - High-volume streaming extraction (>50k rows)
5. splunk-metadata - Index, source, sourcetype discovery
6. splunk-lookup - CSV and lookup file management
7. splunk-tag - Knowledge object tags
8. splunk-savedsearch - Reports and scheduled searches
9. splunk-rest-admin - REST config access (| rest command)
10. splunk-security - Tokens, RBAC, ACLs (/acl, /move)
11. splunk-metrics - mstats/mcatalog for metrics
12. splunk-alert - Alert triggering and monitoring
13. splunk-app - Splunk application management
14. splunk-kvstore - App Key Value Store

## Progressive Disclosure (splunk-assistant)
L1: HTTPS to Search Head:8089, valid JWT, Cloud vs on-prem detection
L2: Oneshot for ad-hoc, Export for ETL, Normal+polling for async
L3: Enforce time bounds, field reduction, job cleanup, strict=true

Build in order: shared lib → job/search/export → metadata/lookup → savedsearch/alert → admin/security → metrics → tests/CI
```
