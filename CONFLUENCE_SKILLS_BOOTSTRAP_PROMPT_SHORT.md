# Confluence-Assistant-Skills Bootstrap Prompt (Short Version)

Use in a blank project folder to create a Claude Code Skills project for Confluence Cloud.

---

## Prompt

```
Create "Confluence-Assistant-Skills" - a Claude Code Skills project for Confluence Cloud API automation.

## Reference Architecture

Copy patterns exactly from: https://github.com/grandcamel/jira-assistant-skills

Use the same:
- Directory structure (.claude/skills/{skill-name}/SKILL.md, scripts/, tests/)
- Shared library pattern (.claude/skills/shared/scripts/lib/)
- Configuration system (settings.json, settings.local.json, profiles)
- Error handling (exception hierarchy, handle_confluence_error())
- Testing approach (pytest, unit + live_integration)
- CI/CD (release-please, GitHub Actions)
- CLAUDE.md format

## Confluence-Specific Adaptations

### Environment Variables
- CONFLUENCE_API_TOKEN, CONFLUENCE_EMAIL, CONFLUENCE_SITE_URL, CONFLUENCE_PROFILE

### API Endpoints
- v2 (primary): /api/v2/pages, /api/v2/spaces, /api/v2/blogposts
- v1 (legacy): /rest/api/content, /rest/api/space, /rest/api/search

### Shared Library Files
| File | Adaptation |
|------|------------|
| confluence_client.py | Base URL: /wiki, v2 API paths |
| validators.py | validate_page_id(), validate_space_key(), validate_cql() |
| adf_helper.py | Same as JIRA (ADF format) |
| xhtml_helper.py | NEW: xhtml_to_markdown(), markdown_to_xhtml() for legacy content |

## Skills to Create (13 total)

| Skill | Purpose | Key Scripts |
|-------|---------|-------------|
| confluence-assistant | Hub/router | SKILL.md with routing table |
| confluence-page | Page/blog CRUD | create_page, get_page, update_page, delete_page, copy_page, move_page |
| confluence-space | Space management | create_space, get_space, list_spaces, delete_space |
| confluence-search | CQL queries | cql_search, cql_validate, export_results, streaming_export |
| confluence-comment | Comments | add_comment, add_inline_comment, get_comments, resolve_comment |
| confluence-attachment | Attachments | upload_attachment, download_attachment, list_attachments |
| confluence-label | Labels | add_label, remove_label, get_labels, search_by_label |
| confluence-template | Templates | list_templates, create_from_template |
| confluence-property | Content metadata | get_properties, set_property, delete_property |
| confluence-permission | Access control | get_space_permissions, add_page_restriction |
| confluence-analytics | Views/stats | get_page_views, get_popular_content |
| confluence-watch | Notifications | watch_page, unwatch_page, get_watchers |
| confluence-hierarchy | Page tree | get_ancestors, get_descendants, get_children, get_page_tree |
| confluence-jira | JIRA integration | embed_jira_issues, get_linked_issues, create_jira_from_page |

## CQL Examples (like JQL)
```cql
space = "DEV" AND type = page
label = "documentation" AND creator = currentUser()
text ~ "API" AND lastModified >= "2024-01-01" ORDER BY title ASC
```

## Implementation Order
1. Shared library (client, config, errors, validators, formatters, adf_helper, xhtml_helper)
2. confluence-page, confluence-space, confluence-search
3. confluence-comment, confluence-attachment, confluence-label, confluence-watch
4. confluence-template, confluence-property, confluence-permission, confluence-hierarchy
5. confluence-analytics, confluence-jira
6. Tests, CI/CD, README

Start with Phase 1. Create complete, tested, production-ready code.
```

---

## Usage

```bash
mkdir Confluence-Assistant-Skills && cd Confluence-Assistant-Skills && git init
# Start Claude Code, paste prompt above
```