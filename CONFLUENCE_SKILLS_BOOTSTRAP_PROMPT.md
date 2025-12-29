# Confluence-Assistant-Skills Bootstrap Prompt

Use this prompt in a blank project folder to bootstrap a Claude Code Skills project for Confluence Cloud automation, following the same architecture as the JIRA Assistant Skills project.

---

## Prompt

```
Create a Claude Code Skills project called "Confluence-Assistant-Skills" for Confluence Cloud API automation.

## Project Goals

Build a modular, production-ready skills framework for Confluence Cloud that:
1. Enables natural language interaction with Confluence via Claude Code
2. Provides autonomous skill discovery and routing
3. Uses the Confluence Cloud REST API v2 (with v1 fallback for legacy endpoints)
4. Follows the exact architecture patterns from the JIRA Assistant Skills project
5. Includes comprehensive testing (unit + live integration)

## Architecture Requirements

### Directory Structure

```
Confluence-Assistant-Skills/
├── .claude/
│   ├── settings.json              # Team defaults (committed)
│   ├── settings.local.json        # Personal credentials (gitignored)
│   └── skills/
│       ├── confluence-assistant/  # Hub/router skill
│       │   ├── SKILL.md
│       │   └── docs/
│       ├── confluence-page/       # Page/blog post CRUD
│       │   ├── SKILL.md
│       │   ├── scripts/
│       │   ├── tests/
│       │   └── references/
│       ├── confluence-space/      # Space management
│       ├── confluence-search/     # CQL queries, saved searches
│       ├── confluence-comment/    # Page/inline comments
│       ├── confluence-attachment/ # File attachments
│       ├── confluence-label/      # Content labeling
│       ├── confluence-template/   # Page templates, blueprints
│       ├── confluence-property/   # Content properties (metadata)
│       ├── confluence-permission/ # Space/page permissions
│       ├── confluence-analytics/  # Content analytics, views
│       ├── confluence-watch/      # Content watching, notifications
│       ├── confluence-hierarchy/  # Ancestors, descendants, tree navigation
│       ├── confluence-jira/       # Cross-product JIRA integration
│       └── shared/
│           ├── scripts/lib/
│           │   ├── __init__.py
│           │   ├── confluence_client.py    # HTTP client with retry
│           │   ├── config_manager.py       # Multi-source config
│           │   ├── error_handler.py        # Exception hierarchy
│           │   ├── validators.py           # Input validation
│           │   ├── formatters.py           # Output formatting
│           │   ├── adf_helper.py           # ADF <-> Markdown
│           │   ├── xhtml_helper.py         # XHTML <-> Markdown (legacy)
│           │   ├── cache.py                # Response caching
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

#### confluence_client.py
Copy the pattern from JIRA's jira_client.py:
- HTTP Basic Auth with email + API token
- Automatic retry with exponential backoff on 429/5xx
- Configurable timeout
- Methods: get(), post(), put(), delete(), upload_file()
- Base URL: `https://{site}.atlassian.net/wiki`
- API paths:
  - v2: `/api/v2/pages`, `/api/v2/spaces`, `/api/v2/blogposts`
  - v1: `/rest/api/content`, `/rest/api/space` (legacy fallback)

#### config_manager.py
Adapt from JIRA's pattern:
- Environment variables: `CONFLUENCE_API_TOKEN`, `CONFLUENCE_EMAIL`, `CONFLUENCE_SITE_URL`, `CONFLUENCE_PROFILE`
- Priority: env vars > settings.local.json > settings.json > defaults
- Profile support for multiple Confluence instances
- Convenience function: `get_confluence_client(profile=None)`

#### error_handler.py
Same exception hierarchy adapted for Confluence:
- `ConfluenceError` (base)
- `AuthenticationError` (401)
- `PermissionError` (403)
- `ValidationError` (400)
- `NotFoundError` (404)
- `RateLimitError` (429)
- `ConflictError` (409)
- `ServerError` (5xx)
- `handle_confluence_error(response, operation)` function
- `sanitize_error_message()` for sensitive data
- `print_error()` and `@handle_errors` decorator

#### validators.py
Confluence-specific validators:
- `validate_page_id(page_id)` - numeric string
- `validate_space_key(space_key)` - uppercase letters
- `validate_cql(cql)` - CQL query validation
- `validate_content_type(content_type)` - page, blogpost, comment
- `validate_file_path(file_path, must_exist=True)`
- `validate_url(url)` - HTTPS required
- `validate_email(email)`

#### formatters.py
Confluence-specific formatting:
- `format_page(page, detailed=False)` - Display page info
- `format_space(space)` - Display space info
- `format_table(data, columns, headers)` - Tabular output
- `format_json(data, pretty=True)`
- `export_csv(data, file_path, columns)`
- `format_search_results(pages, show_labels=False, show_ancestors=False)`
- `format_comments(comments, limit=None)`
- `print_success()`, `print_warning()`, `print_info()`

#### adf_helper.py
Copy and adapt from JIRA:
- `text_to_adf(text)` - Plain text to ADF
- `markdown_to_adf(markdown)` - Markdown to ADF
- `adf_to_text(adf)` - ADF to plain text
- `adf_to_markdown(adf)` - ADF to Markdown (new)

#### xhtml_helper.py (NEW - for legacy content)
- `xhtml_to_markdown(xhtml)` - Storage format to Markdown
- `markdown_to_xhtml(markdown)` - Markdown to storage format
- `xhtml_to_adf(xhtml)` - Convert legacy to v2 format
- Handle Confluence macros, tables, code blocks

### Skills Specification

#### 1. confluence-assistant (Hub/Router)
Routes to specialized skills based on natural language intent.
Triggers for each skill mapped in SKILL.md routing table.

#### 2. confluence-page
**Purpose**: Page and blog post CRUD operations
**Scripts**:
- `create_page.py` - Create page with parent, space, title, body
- `get_page.py` - Retrieve page content and metadata
- `update_page.py` - Update title, body, status
- `delete_page.py` - Move to trash or permanent delete
- `create_blogpost.py` - Create blog post
- `get_blogpost.py` - Retrieve blog post
- `copy_page.py` - Copy page to new location
- `move_page.py` - Move page to different parent/space
- `get_page_versions.py` - Version history
- `restore_version.py` - Restore previous version

**Triggers**: "create page", "get page", "update page", "delete page", "blog post", "copy", "move", "version"

#### 3. confluence-space
**Purpose**: Space management
**Scripts**:
- `create_space.py` - Create space with key, name, description
- `get_space.py` - Retrieve space details
- `update_space.py` - Update space properties
- `delete_space.py` - Delete space
- `list_spaces.py` - List all spaces (with filters)
- `get_space_content.py` - List pages in space
- `get_space_settings.py` - Space settings/theme

**Triggers**: "create space", "list spaces", "space settings", "space content"

#### 4. confluence-search
**Purpose**: CQL queries, saved searches, export
**Scripts**:
- `cql_search.py` - Execute CQL queries
- `cql_validate.py` - Validate CQL syntax
- `cql_suggest.py` - Field/value suggestions
- `cql_interactive.py` - Interactive query builder
- `export_results.py` - Export to CSV/JSON
- `streaming_export.py` - Large result streaming with checkpoints
- `cql_history.py` - Local query history
- `search_content.py` - Simple text search

**CQL Patterns**:
```cql
# By space
space = "DEV" AND type = page

# By label
label = "documentation" AND space = "DOCS"

# By date
created >= "2024-01-01" AND creator = currentUser()

# Text search
text ~ "API documentation" AND type = blogpost

# Combined
space in ("DEV", "DOCS") AND label = "approved" ORDER BY lastModified DESC
```

**Triggers**: "search", "find pages", "CQL", "query", "export"

#### 5. confluence-comment
**Purpose**: Page and inline comments
**Scripts**:
- `add_comment.py` - Add page footer comment
- `add_inline_comment.py` - Add inline comment with selection
- `get_comments.py` - List comments on page
- `update_comment.py` - Edit comment
- `delete_comment.py` - Delete comment
- `resolve_comment.py` - Mark inline comment resolved

**Triggers**: "comment", "add comment", "inline comment", "resolve"

#### 6. confluence-attachment
**Purpose**: File attachments
**Scripts**:
- `upload_attachment.py` - Upload file to page
- `download_attachment.py` - Download attachment
- `list_attachments.py` - List page attachments
- `delete_attachment.py` - Remove attachment
- `update_attachment.py` - Replace attachment file

**Triggers**: "attach", "upload", "download", "attachment"

#### 7. confluence-label
**Purpose**: Content labeling
**Scripts**:
- `add_label.py` - Add label to content
- `remove_label.py` - Remove label from content
- `get_labels.py` - List labels on content
- `search_by_label.py` - Find content by label
- `list_popular_labels.py` - Most used labels in space

**Triggers**: "label", "tag", "add label", "remove label"

#### 8. confluence-template
**Purpose**: Page templates and blueprints
**Scripts**:
- `list_templates.py` - List available templates
- `get_template.py` - Get template content
- `create_from_template.py` - Create page from template
- `create_template.py` - Create new template
- `update_template.py` - Update template

**Triggers**: "template", "blueprint", "create from template"

#### 9. confluence-property
**Purpose**: Content properties (metadata)
**Scripts**:
- `get_properties.py` - Get content properties
- `set_property.py` - Set property value
- `delete_property.py` - Remove property
- `list_properties.py` - List all properties on content

**Triggers**: "property", "metadata", "custom field"

#### 10. confluence-permission
**Purpose**: Space and page permissions
**Scripts**:
- `get_space_permissions.py` - List space permissions
- `add_space_permission.py` - Grant space permission
- `remove_space_permission.py` - Revoke space permission
- `get_page_restrictions.py` - List page restrictions
- `add_page_restriction.py` - Restrict page access
- `remove_page_restriction.py` - Remove restriction

**Triggers**: "permission", "restrict", "access", "security"

#### 11. confluence-analytics
**Purpose**: Content analytics
**Scripts**:
- `get_page_views.py` - Page view statistics
- `get_space_analytics.py` - Space-level analytics
- `get_popular_content.py` - Most viewed content
- `get_content_watchers.py` - Who's watching content

**Triggers**: "analytics", "views", "statistics", "popular"

#### 12. confluence-watch
**Purpose**: Content watching and notifications
**Scripts**:
- `watch_page.py` - Start watching page
- `unwatch_page.py` - Stop watching page
- `watch_space.py` - Watch entire space
- `get_watchers.py` - List content watchers
- `am_i_watching.py` - Check watch status

**Triggers**: "watch", "unwatch", "notify", "follow"

#### 13. confluence-hierarchy
**Purpose**: Content tree navigation
**Scripts**:
- `get_ancestors.py` - Get parent pages
- `get_descendants.py` - Get child pages (recursive)
- `get_children.py` - Get direct children
- `get_page_tree.py` - Full tree visualization
- `reorder_children.py` - Change child page order

**Triggers**: "parent", "children", "tree", "hierarchy", "ancestors"

#### 14. confluence-jira (Cross-product)
**Purpose**: JIRA integration
**Scripts**:
- `embed_jira_issues.py` - Embed JIRA issues in page
- `link_to_jira.py` - Create application link
- `get_linked_issues.py` - List JIRA issues on page
- `create_jira_from_page.py` - Create JIRA issue from page content
- `sync_jira_macro.py` - Update JIRA macro content

**Triggers**: "jira", "embed issue", "link jira", "jira macro"

### Configuration Files

#### .claude/settings.json
```json
{
  "confluence": {
    "default_profile": "production",
    "profiles": {
      "production": {
        "url": "https://your-company.atlassian.net",
        "default_space": "DOCS",
        "space_keys": ["DOCS", "KB", "DEV"]
      },
      "development": {
        "url": "https://your-company-dev.atlassian.net",
        "default_space": "TEST",
        "space_keys": ["TEST", "SANDBOX"]
      }
    },
    "api": {
      "version": "2",
      "timeout": 30,
      "max_retries": 3,
      "retry_backoff": 2.0
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
```

### Testing Requirements

#### Unit Tests
- One test file per script in `{skill}/tests/test_{script}.py`
- Use pytest with fixtures in `conftest.py`
- Mock HTTP responses, never hit real API in unit tests
- Target: Same coverage as JIRA skills (~300+ tests)

#### Live Integration Tests
- Location: `{skill}/tests/live_integration/`
- Require `--profile` argument
- Use session-scoped fixtures for test data setup/teardown
- Create test space at start, clean up at end
- Skip destructive tests in CI (use `@pytest.mark.destructive`)

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
          tar -czvf dist/confluence-assistant-skills-${VERSION}.tar.gz \
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
          gh release upload v${VERSION} dist/confluence-assistant-skills-${VERSION}.tar.gz --clobber
```

### CLAUDE.md Template

Create a comprehensive CLAUDE.md following this structure:
1. Project Overview - list all skills
2. Architecture - shared library pattern, import pattern
3. Configuration System - multi-source, profiles
4. Error Handling Strategy - 4-layer approach
5. Content Formats - ADF + XHTML conversion
6. Testing Scripts - how to run tests
7. Adding New Scripts - step-by-step guide
8. Adding New Skills - structure requirements
9. Configuration Changes - schema, validation
10. Credentials Security - never commit tokens
11. Common Patterns - script template, bulk operations
12. CQL Query Patterns - examples
13. Git Commit Guidelines - Conventional Commits
14. Live Integration Testing - how to run

### Implementation Order

**Phase 1: Foundation**
1. Create directory structure
2. Implement shared library (client, config, errors, validators, formatters)
3. Implement adf_helper.py and xhtml_helper.py
4. Create settings.json schema and examples
5. Create CLAUDE.md

**Phase 2: Core Skills**
6. confluence-page (most critical - pages are the core entity)
7. confluence-space (required for page operations)
8. confluence-search (CQL is essential for discovery)
9. confluence-assistant (hub routing)

**Phase 3: Collaboration**
10. confluence-comment
11. confluence-attachment
12. confluence-label
13. confluence-watch

**Phase 4: Advanced**
14. confluence-template
15. confluence-property
16. confluence-permission
17. confluence-hierarchy

**Phase 5: Integration**
18. confluence-analytics
19. confluence-jira (cross-product)

**Phase 6: Quality**
20. Unit tests for all scripts
21. Live integration tests
22. CI/CD workflow
23. README.md with badges

### API Reference

**Confluence Cloud REST API v2** (primary):
- Pages: `GET/POST/PUT/DELETE /api/v2/pages/{id}`
- Spaces: `GET/POST/PUT/DELETE /api/v2/spaces/{id}`
- Blog Posts: `GET/POST/PUT/DELETE /api/v2/blogposts/{id}`
- Comments: `GET/POST/PUT/DELETE /api/v2/pages/{id}/footer-comments`
- Attachments: `GET/POST/DELETE /api/v2/attachments/{id}`
- Labels: `GET/POST/DELETE /api/v2/pages/{id}/labels`

**Confluence Cloud REST API v1** (legacy/fallback):
- Content: `GET/POST/PUT/DELETE /rest/api/content/{id}`
- Space: `GET/POST/PUT/DELETE /rest/api/space/{key}`
- Search: `GET /rest/api/search?cql={query}`
- Content Properties: `GET/POST/PUT/DELETE /rest/api/content/{id}/property/{key}`

**Authentication**:
- HTTP Basic Auth: email + API token
- Token URL: https://id.atlassian.com/manage-profile/security/api-tokens

### Script Template

Every script should follow this pattern:

```python
#!/usr/bin/env python3
"""
Brief description of what this script does.

Examples:
    python script_name.py SPACE-KEY --option value
"""

import sys
import argparse
from pathlib import Path

# Add shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_confluence_client
from error_handler import handle_errors, print_error, ConfluenceError
from validators import validate_space_key
from formatters import print_success, format_page


@handle_errors
def main():
    parser = argparse.ArgumentParser(
        description='Script description',
        epilog='Examples:\n  python script.py SPACE --option value',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('space_key', help='Space key')
    parser.add_argument('--profile', '-p', help='Confluence profile to use')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text')
    args = parser.parse_args()

    # Validate inputs
    space_key = validate_space_key(args.space_key)

    # Get client
    client = get_confluence_client(profile=args.profile)

    # Perform operation
    result = client.get(f'/api/v2/spaces/{space_key}', operation='get space')

    # Output
    if args.output == 'json':
        print(format_json(result))
    else:
        print(format_space(result))

    print_success(f"Successfully retrieved space {space_key}")


if __name__ == '__main__':
    main()
```

Now create the complete project structure and implement all components in order. Start with Phase 1 (Foundation) and proceed through each phase, creating fully functional skills with tests.
```

---

## Usage Instructions

1. Create a new empty directory:
   ```bash
   mkdir Confluence-Assistant-Skills
   cd Confluence-Assistant-Skills
   git init
   ```

2. Start Claude Code in the directory

3. Paste the prompt above

4. Claude will create the complete project structure following the JIRA Assistant Skills patterns