# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude Code Skills project providing JIRA automation through seven modular skills:
- **jira-issue**: Core CRUD operations on issues
- **jira-lifecycle**: Workflow/transition management
- **jira-search**: JQL queries, saved filters, JQL builder/validator, and bulk operations
- **jira-collaborate**: Comments, attachments, watchers
- **jira-agile**: Agile/Scrum workflows (epics, sprints, backlog, story points)
- **jira-relationships**: Issue linking, dependencies, blocker chains, cloning
- **jira-time**: Time tracking, worklogs, estimates, and time reports

Each skill is designed for autonomous discovery and use by Claude Code.

## Architecture

### Shared Library Pattern

All skills depend on a shared library at `.claude/skills/shared/scripts/lib/` containing:

- **jira_client.py**: HTTP client with automatic retry (3 attempts, exponential backoff on 429/5xx)
- **config_manager.py**: Multi-source configuration merging (env vars > settings.local.json > settings.json > defaults)
- **error_handler.py**: Exception hierarchy that maps HTTP status codes to domain exceptions (400→ValidationError, 401→AuthenticationError, etc.)
- **validators.py**: Input validation (issue keys must match `^[A-Z][A-Z0-9]*-[0-9]+$`, URLs must be HTTPS)
- **formatters.py**: Output formatting (tables via tabulate, JSON, CSV export)
- **adf_helper.py**: Markdown to Atlassian Document Format conversion
- **time_utils.py**: Time parsing (parse_time_string), formatting (format_seconds), and relative date handling

**Import pattern**: All scripts use `sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))` to access shared modules.

### Configuration System

Configuration is merged from 4 sources (priority order):
1. Environment variables: `JIRA_API_TOKEN`, `JIRA_EMAIL`, `JIRA_SITE_URL`, `JIRA_PROFILE`
2. `.claude/settings.local.json` (gitignored, personal credentials)
3. `.claude/settings.json` (committed, team defaults with profiles)
4. Hardcoded defaults in config_manager.py

**Profile-based**: Supports multiple JIRA instances (dev/staging/prod). Profile contains: url, project_keys, default_project, use_service_management flag.

### Error Handling Strategy

4-layer approach:
1. **Pre-validation**: validators.py catches bad input before API calls
2. **API errors**: error_handler.handle_jira_error() maps status codes to exceptions with troubleshooting hints
3. **Retry logic**: JiraClient retries on [429, 500, 502, 503, 504] with exponential backoff
4. **User messages**: Exceptions include contextual help (e.g., AuthenticationError suggests checking token at specific URL)

### ADF Conversion

JIRA Cloud requires Atlassian Document Format for rich text. The adf_helper.py supports:
- **text_to_adf()**: Plain text → ADF paragraphs
- **markdown_to_adf()**: Markdown → ADF (headings, bold, italic, code, lists, links)
- **adf_to_text()**: ADF → plain text extraction

Scripts accept `--format` flag: text (default), markdown, or adf (raw JSON).

## Testing Scripts

All scripts are executable and support `--help`. Test with existing JIRA credentials:

```bash
# Setup
pip install -r .claude/skills/shared/scripts/lib/requirements.txt
export JIRA_API_TOKEN="token-from-id.atlassian.com"
export JIRA_EMAIL="your@email.com"
export JIRA_SITE_URL="https://your-company.atlassian.net"

# Test basic connectivity
python .claude/skills/jira-issue/scripts/get_issue.py EXISTING-ISSUE-KEY

# Test search
python .claude/skills/jira-search/scripts/jql_search.py "project = PROJ"

# Test with specific profile
python .claude/skills/jira-issue/scripts/get_issue.py PROJ-123 --profile development
```

## Adding New Scripts

When adding scripts to existing skills:

1. **Location**: Place in appropriate skill's `scripts/` directory
2. **Imports**: Use the standard path injection pattern to import from shared lib
3. **CLI**: Use argparse with descriptive help, examples in epilog
4. **Error handling**: Catch JiraError, call print_error(), sys.exit(1)
5. **Profile support**: Add `--profile` argument, pass to get_jira_client()
6. **Make executable**: `chmod +x script.py` and add shebang `#!/usr/bin/env python3`
7. **Update SKILL.md**: Document the new script in the skill's SKILL.md file

## Adding New Skills

Skills must follow this structure:

```
.claude/skills/new-skill/
├── SKILL.md              # Description for autonomous discovery
├── scripts/              # Executable Python scripts
├── references/           # API docs, guides (optional)
└── assets/templates/     # JSON templates (optional)
```

**SKILL.md format**:
- "When to use this skill" section for Claude's autonomous discovery
- "What this skill does" with feature list
- "Available scripts" with descriptions
- "Examples" with concrete bash commands

## Configuration Changes

When modifying configuration schema:

1. Update `.claude/skills/shared/config/config.schema.json` (JSON Schema validation)
2. Update `.claude/settings.json` with new structure/defaults
3. Update `config.example.json` with documented example
4. Test config merging in config_manager.py
5. Update setup guide if user-facing

## Credentials Security

**Never commit**:
- `.claude/settings.local.json` (already in .gitignore)
- API tokens in any file
- Hardcoded URLs that expose internal infrastructure

**Always**:
- Use environment variables for tokens
- Validate URLs are HTTPS-only (validators.validate_url)
- Document required JIRA permissions in skill docs

## Common Patterns

**Script template**:
```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError
from validators import validate_issue_key

def main():
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()

    try:
        # Validate inputs
        # Get client
        # Perform operation
        # Print success
    except JiraError as e:
        print_error(e)
        sys.exit(1)
```

**Transition matching**: Use transition_issue.py's `find_transition_by_name()` pattern - exact match first, then partial match, raise ValidationError if ambiguous.

**Bulk operations**: Always include `--dry-run` flag and confirmation prompts before modifying multiple issues.

**Agile custom fields**: Story point and epic link fields vary by JIRA instance. Default field IDs:
- Epic Link: `customfield_10014`
- Story Points: `customfield_10016`
- Epic Name: `customfield_10011`
- Epic Color: `customfield_10012`

**Sprint operations**: Use the Agile API (`/rest/agile/1.0/`) for sprint and board operations. Sprints require board context for creation.

**Issue linking**: Use the Issue Link API (`/rest/api/3/issueLink`) for creating relationships:
- Link types: Blocks, Cloners, Duplicate, Relates (names may vary by instance)
- Direction: inward (is blocked by) vs outward (blocks)
- Blocker chains: Traverse recursively with visited set to detect cycles
- Integration: `create_issue.py --blocks`, `get_issue.py --show-links`, `jql_search.py --show-links`

**Issue cloning**: Use `jira_client.clone_issue()` for copying issues:
- Copies: summary, description, priority, labels, components, fixVersions
- Creates "Cloners" link between clone and original
- Optional flags: `clone_subtasks=True`, `clone_links=True`
- Returns the new issue key after creation

**Time tracking**: Use the Worklog API (`/rest/api/3/issue/{key}/worklog`) for time management:
- Time format: JIRA accepts human-readable formats like '2h', '1d 4h', '30m', '1w'
- Estimate adjustment: Use `adjustEstimate` parameter (auto, leave, new, manual)
- Known bug JRACLOUD-67539: Always set both originalEstimate and remainingEstimate together
- Integration: `create_issue.py --estimate`, `get_issue.py --show-time`, `jql_search.py --show-time`

**JQL and Advanced Search**: Use the JQL APIs for query building and validation:
- JQL Autocomplete: `/rest/api/3/jql/autocompletedata` for fields, operators, functions
- JQL Parse: `/rest/api/3/jql/parse` for validation with error suggestions
- JQL Suggestions: `/rest/api/3/jql/autocompletedata/suggestions` for field value completion
- Filter CRUD: `/rest/api/3/filter` for create, read, update, delete filters
- Filter Sharing: `/rest/api/3/filter/{id}/permission` for sharing with projects, groups, users
- Integration: `jql_search.py --filter 10042` to run saved filter, `jql_search.py "query" --save-as "Name"`

**JQL Query Patterns**:
```jql
# User-based
assignee = currentUser()
assignee in membersOf("developers")
reporter != currentUser() AND watcher = currentUser()

# Time-based
created >= startOfDay(-7d)
updated >= startOfWeek() AND updated <= endOfWeek()
resolved >= -30d

# Status-based
status = "In Progress"
status in (Open, "To Do", Backlog)
status changed FROM "In Progress" TO Done DURING (startOfDay(-1d), now())

# Combined with ordering
project = PROJ AND type = Bug AND priority in (High, Highest) ORDER BY created DESC
```

## Git Commit Guidelines

This project follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for all commit messages.

### Commit Message Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types

- **feat**: New feature or functionality
- **fix**: Bug fix
- **docs**: Documentation changes only
- **style**: Code style changes (formatting, missing semicolons, etc.) with no logic changes
- **refactor**: Code changes that neither fix bugs nor add features
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **build**: Changes to build system or dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files

### Scopes

Use scopes to identify which part of the codebase changed. Suggested scopes for this project:

- **jira-issue**: Changes to the jira-issue skill
- **jira-lifecycle**: Changes to the jira-lifecycle skill
- **jira-search**: Changes to the jira-search skill
- **jira-collaborate**: Changes to the jira-collaborate skill
- **jira-agile**: Changes to the jira-agile skill
- **jira-relationships**: Changes to the jira-relationships skill
- **jira-time**: Changes to the jira-time skill
- **shared**: Changes to shared library code
- **config**: Configuration changes
- **docs**: Documentation updates (CLAUDE.md, README.md, etc.)

Multiple scopes can be specified with commas: `feat(jira-issue,shared): add retry logic`

### Breaking Changes

Breaking changes MUST be indicated by:
1. Adding `!` after the type/scope: `feat(shared)!: change config format`
2. Including a `BREAKING CHANGE:` footer with description

### Examples

```bash
# New feature in jira-issue skill
feat(jira-issue): add support for creating subtasks

# Bug fix with scope
fix(shared): correct retry backoff calculation

# Documentation update
docs: add troubleshooting guide for authentication

# Breaking change
feat(config)!: migrate to YAML configuration format

BREAKING CHANGE: settings.json is now settings.yaml and uses YAML syntax
```

### Body and Footer Guidelines

- Use the body to explain what and why, not how
- Reference JIRA tickets in footers: `Refs: PROJ-123`
- Use `BREAKING CHANGE:` footer for detailed breaking change descriptions
- Separate body from description with blank line
- Wrap body at 72 characters

### TDD Commit Best Practices

When developing features using Test-Driven Development (TDD), follow this commit pattern:

1. **Commit after all tests pass**: Always create a commit immediately after a feature's tests are passing. This ensures:
   - Working code is captured in version control
   - Easy rollback if future changes break functionality
   - Clear history of feature completion milestones

2. **Two-commit pattern per feature**:
   ```bash
   # First: Add failing tests
   test(jira-search): add failing tests for jql_validate

   # Second: Implement feature to pass tests
   feat(jira-search): implement jql_validate.py (7/7 tests passing)
   ```

3. **Include test counts in commit messages**: When implementing a feature, include the test pass count:
   - `feat(jira-agile): implement create_sprint.py (6/6 tests passing)`
   - `feat(shared): add worklog API methods (12/12 tests passing)`

4. **Run tests before committing**: Always verify all tests pass before creating a commit:
   ```bash
   # Run specific skill tests
   pytest .claude/skills/jira-search/tests/ -v

   # Run all tests
   pytest .claude/skills/*/tests/ -v
   ```

5. **Never commit failing tests**: If tests are failing, either fix the implementation or fix the tests before committing. The main branch should always have passing tests.

## Live Integration Testing

The project includes comprehensive live integration tests against real JIRA instances:

```bash
# Run all live integration tests
pytest .claude/skills/shared/tests/live_integration/ --profile development -v

# Run specific test modules
pytest .claude/skills/shared/tests/live_integration/test_issue_lifecycle.py -v
pytest .claude/skills/shared/tests/live_integration/test_agile_workflows.py -v
```

**Test structure**: Tests use session-scoped fixtures that create a test project at the start and clean up all test data at the end.

**Profile requirement**: Live tests require `--profile development` to specify which JIRA instance to test against.

**Current coverage**: 153 live integration tests covering all 7 skills across 3 phases:
- Phase 1: Core operations (issue CRUD, lifecycle, collaboration)
- Phase 2: Agile, relationships, time tracking
- Phase 3: Search, filters, bulk operations

## Key Constraints

- **Python 3.8+**: Minimum version for type hints and pathlib
- **No external CLI tools**: All operations via Python/requests
- **Profile-aware**: All scripts must support `--profile` override
- **Validation first**: Call validators before API operations to fail fast
- **HTTP client reuse**: Use get_jira_client() which handles session management and retry
