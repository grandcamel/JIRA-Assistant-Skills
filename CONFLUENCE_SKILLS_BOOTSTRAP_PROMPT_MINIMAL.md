# Confluence-Assistant-Skills Bootstrap Prompt (Minimal)

```
Create "Confluence-Assistant-Skills" for Confluence Cloud API automation.

## Pattern Source
Clone architecture from: https://github.com/grandcamel/jira-assistant-skills
- Same directory structure, shared library, config system, testing, CI/CD

## Key Differences from JIRA
- Env vars: CONFLUENCE_API_TOKEN, CONFLUENCE_EMAIL, CONFLUENCE_SITE_URL
- Base URL: /wiki
- APIs: v2 (/api/v2/pages, /api/v2/spaces) + v1 fallback (/rest/api/content)
- Add xhtml_helper.py for legacy XHTML ↔ Markdown conversion
- CQL instead of JQL

## Skills (13)
1. confluence-assistant - Hub/router
2. confluence-page - Page/blog CRUD
3. confluence-space - Space management
4. confluence-search - CQL queries, export
5. confluence-comment - Page/inline comments
6. confluence-attachment - File uploads
7. confluence-label - Content labels
8. confluence-template - Page templates
9. confluence-property - Content metadata
10. confluence-permission - Access control
11. confluence-analytics - Page views/stats
12. confluence-watch - Notifications
13. confluence-hierarchy - Page tree navigation
14. confluence-jira - Cross-product JIRA integration

Build in order: shared lib → page/space/search → collaboration skills → advanced → tests/CI
```