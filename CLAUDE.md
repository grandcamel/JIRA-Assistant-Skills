# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude Code Plugin project providing JIRA automation through fourteen modular skills. The plugin is self-contained in `plugins/jira-assistant-skills/` and can be installed via the Claude Code plugin system.

### Plugin Structure

```
plugins/jira-assistant-skills/
├── plugin.json           # Plugin manifest
├── commands/             # Slash commands
├── config/               # Configuration examples
└── skills/               # 14 JIRA automation skills
```

### Available Skills
- **jira-issue**: Core CRUD operations on issues
- **jira-lifecycle**: Workflow/transition management
- **jira-search**: JQL queries, saved filters, JQL builder/validator, and bulk operations
- **jira-collaborate**: Comments, attachments, watchers
- **jira-agile**: Agile/Scrum workflows (epics, sprints, backlog, story points)
- **jira-relationships**: Issue linking, dependencies, blocker chains, cloning
- **jira-time**: Time tracking, worklogs, estimates, and time reports
- **jira-jsm**: Jira Service Management (service desks, requests, SLAs, queues, customers, approvals, knowledge base)
- **jira-bulk**: Bulk operations (transitions, assignments, priorities, cloning) at scale with dry-run support
- **jira-dev**: Developer workflow integration (Git branch names, commit parsing, PR descriptions)
- **jira-fields**: Custom field management, Agile field configuration, project field discovery
- **jira-ops**: Cache management, request batching, and operational utilities
- **jira-admin**: Project, permission, notification, screen, issue type, and workflow administration
- **jira-assistant**: Hub skill for routing and skill discovery

Each skill is designed for autonomous discovery and use by Claude Code.

## Architecture

### Shared Library Pattern

All skills depend on the `jira-assistant-skills-lib` PyPI package. Install with:

```bash
pip install jira-assistant-skills-lib>=0.1.5
```

The package provides:
- **JiraClient**: HTTP client with automatic retry (3 attempts, exponential backoff on 429/5xx)
- **ConfigManager**: Multi-source configuration merging (env vars > settings.local.json > settings.json > defaults)
- **Config helpers**: `get_agile_fields()`, `get_agile_field()`, `get_project_defaults()` for Agile field IDs and issue defaults
- **Error handling**: Exception hierarchy that maps HTTP status codes to domain exceptions (400→ValidationError, 401→AuthenticationError, etc.)
- **Validators**: Input validation (issue keys must match `^[A-Z][A-Z0-9]*-[0-9]+$`, URLs must be HTTPS)
- **Formatters**: Output formatting (tables via tabulate, JSON, CSV export)
- **ADF helpers**: Markdown to Atlassian Document Format conversion
- **Time utilities**: Time parsing (parse_time_string), formatting (format_seconds), and relative date handling
- **Cache**: SQLite-based caching with TTL support (`JiraCache`, `get_cache`)
- **Request batching**: Concurrent API requests (`RequestBatcher`, `batch_fetch_issues`)
- **Batch processing**: Large-scale operations with checkpoints (`BatchProcessor`, `BatchConfig`)
- **Project context**: Project metadata and defaults (`ProjectContext`, `get_project_context`)
- **Transition helpers**: Fuzzy transition matching (`find_transition_by_name`, `find_transition_by_keywords`)
- **User helpers**: User resolution (`resolve_user_to_account_id`, `get_user_display_info`)
- **JSM utilities**: SLA formatting and status helpers
- **Credential management**: Secure credential storage with keychain support
- **Permission helpers**: Permission scheme management utilities
- **Autocomplete cache**: JQL field/value autocomplete caching

**Import pattern**: All scripts use `from jira_assistant_skills_lib import ...` to access shared modules.

### Configuration System

Configuration is loaded from environment variables (recommended):
- `JIRA_API_TOKEN`: API token from id.atlassian.com/manage-profile/security/api-tokens
- `JIRA_EMAIL`: Atlassian account email
- `JIRA_SITE_URL`: JIRA instance URL (e.g., https://company.atlassian.net)
- `JIRA_PROFILE`: Optional profile name for multi-instance support

See `plugins/jira-assistant-skills/config/settings.example.json` for profile-based configuration examples supporting multiple JIRA instances (dev/staging/prod).

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

All scripts are executable via the unified `jira` CLI. Test with existing JIRA credentials:

```bash
# Setup
pip install -e .  # Install CLI in editable mode
pip install jira-assistant-skills-lib
export JIRA_API_TOKEN="token-from-id.atlassian.com"
export JIRA_EMAIL="your@email.com"
export JIRA_SITE_URL="https://your-company.atlassian.net"

# Test basic connectivity (via CLI)
jira issue get EXISTING-ISSUE-KEY

# Test search
jira search query "project = PROJ"

# Test with specific profile
jira issue get PROJ-123 --profile development

# Direct script execution is also supported for development:
python plugins/jira-assistant-skills/skills/jira-issue/scripts/get_issue.py EXISTING-ISSUE-KEY
```

## Adding New Scripts

When adding scripts to existing skills:

1. **Location**: Place in appropriate skill's `scripts/` directory
2. **Imports**: Use `from jira_assistant_skills_lib import ...` to import shared modules
3. **CLI**: Use argparse with descriptive help, examples in epilog
4. **Error handling**: Catch JiraError, call print_error(), sys.exit(1)
5. **Profile support**: Add `--profile` argument, pass to get_jira_client()
6. **Make executable**: `chmod +x script.py` and add shebang `#!/usr/bin/env python3`
7. **Update SKILL.md**: Document the new script in the skill's SKILL.md file

## Adding New Skills

Skills must follow this structure:

```
plugins/jira-assistant-skills/skills/new-skill/
├── SKILL.md              # Description for autonomous discovery
├── scripts/              # Executable Python scripts
├── tests/                # Unit and integration tests
├── references/           # API docs, guides (optional)
└── assets/templates/     # JSON templates (optional)
```

**SKILL.md format**:
- "When to use this skill" section for Claude's autonomous discovery
- "What this skill does" with feature list
- "Available scripts" with descriptions
- "Examples" with concrete bash commands

## Credentials Security

**Never commit**:
- API tokens in any file
- Hardcoded URLs that expose internal infrastructure

**Always**:
- Use environment variables for tokens (`JIRA_API_TOKEN`, `JIRA_EMAIL`, `JIRA_SITE_URL`)
- Validate URLs are HTTPS-only (validators.validate_url)
- Document required JIRA permissions in skill docs

## Common Patterns

**Script template**:
```python
#!/usr/bin/env python3
import argparse
import sys

from jira_assistant_skills_lib import get_jira_client, print_error, JiraError
from jira_assistant_skills_lib.validators import validate_issue_key

def main(argv: list[str] | None = None):
    """Main function with argv parameter for CLI integration."""
    parser = argparse.ArgumentParser(...)
    parser.add_argument('--profile', help='JIRA profile to use')
    args = parser.parse_args(argv)

    try:
        # Validate inputs
        # Get client
        client = get_jira_client(profile=args.profile)
        # Perform operation
        # Print success
    except JiraError as e:
        print_error(e)
        sys.exit(1)

if __name__ == '__main__':
    main()
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
- **Default search fields**: `key, summary, status, priority, issuetype, assignee, reporter` - Reporter is included by default to identify who created each issue

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
- **jira-jsm**: Changes to the jira-jsm skill
- **jira-bulk**: Changes to the jira-bulk skill
- **jira-dev**: Changes to the jira-dev skill
- **jira-fields**: Changes to the jira-fields skill
- **jira-ops**: Changes to the jira-ops skill
- **jira-admin**: Changes to the jira-admin skill
- **jira-assistant**: Changes to the jira-assistant hub skill
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
   # Install test dependencies (pytest-asyncio required for async tests)
   pip install pytest pytest-asyncio

   # Run specific skill tests
   pytest plugins/jira-assistant-skills/skills/jira-search/tests/ -v

   # Run all unit tests (uses root pytest.ini configuration)
   pytest plugins/jira-assistant-skills/skills/*/tests/*.py -v

   # Run tests for multiple skills together
   pytest plugins/jira-assistant-skills/skills/jira-search/tests/ \
          plugins/jira-assistant-skills/skills/jira-bulk/tests/ -v
   ```

5. **Never commit failing tests**: If tests are failing, either fix the implementation or fix the tests before committing. The main branch should always have passing tests.

6. **Pytest configuration**: The project uses a centralized `pytest.ini` at the root with:
   - `import-mode=importlib` to avoid module name conflicts across skills
   - Shared markers (unit, integration, live, slow, etc.)
   - Test paths configured for skill directories

## Live Integration Testing

The project includes comprehensive live integration tests against real JIRA instances:

```bash
# Run all shared/core live integration tests
pytest plugins/jira-assistant-skills/skills/shared/tests/live_integration/ --profile development -v

# Run JSM live integration tests
pytest plugins/jira-assistant-skills/skills/jira-jsm/tests/live_integration/ --profile development --skip-premium -v

# Run new skill live integration tests
pytest plugins/jira-assistant-skills/skills/jira-bulk/tests/live_integration/ --profile development -v
pytest plugins/jira-assistant-skills/skills/jira-dev/tests/live_integration/ --profile development -v
pytest plugins/jira-assistant-skills/skills/jira-fields/tests/live_integration/ --profile development -v
pytest plugins/jira-assistant-skills/skills/jira-ops/tests/live_integration/ --profile development -v

# Run specific test modules
pytest plugins/jira-assistant-skills/skills/shared/tests/live_integration/test_issue_lifecycle.py -v
pytest plugins/jira-assistant-skills/skills/jira-jsm/tests/live_integration/test_request_lifecycle.py -v
```

**Test structure**: Tests use session-scoped fixtures that create a test project/service desk at the start and clean up all test data at the end.

**Profile requirement**: Live tests require `--profile development` to specify which JIRA instance to test against.

**Current coverage**:
- **Core skills**: 157 live integration tests covering 8 skills across 3 phases
  - Phase 1: Core operations (issue CRUD, lifecycle, collaboration)
  - Phase 2: Agile, relationships, time tracking
  - Phase 3: Search, filters, bulk operations
- **JSM skill**: 94 live integration tests covering service management features
  - Service desks, request types, portals
  - Request lifecycle (CRUD, transitions, comments)
  - Customers, organizations, participants
  - SLAs, queues, approvals
  - Knowledge base integration
  - Assets/CMDB (requires JSM Premium)
- **New skills**: 87 live integration tests + 84 unit tests
  - jira-bulk: 22 live + 42 unit tests (bulk transitions, assignments, priorities, cloning)
  - jira-dev: 25 live + 42 unit tests (Git integration, PR management)
  - jira-fields: 18 live tests (field discovery, Agile fields)
  - jira-ops: 22 live tests (cache warming, cache operations)

**JSM test options**:
- `--skip-premium`: Skip tests requiring JSM Premium license (Assets/CMDB)
- `--service-desk-id N`: Use existing service desk instead of creating one
- `--keep-project`: Keep test service desk after tests (for debugging)

## Routing Tests

The jira-assistant skill includes routing accuracy tests that validate Claude routes user prompts to the correct skill based on SKILL.md descriptions.

### Running Routing Tests

```bash
cd plugins/jira-assistant-skills/skills/jira-assistant/tests

# Run all routing tests (sequential, ~22 min)
pytest test_routing.py -v

# Fast iteration with haiku model (~10 min with parallel)
./fast_test.sh --fast --parallel 4

# Test specific skill routing
./fast_test.sh --skill agile --fast

# Smoke test (5 key tests, ~1.5 min)
./fast_test.sh --smoke --fast

# Re-run only failed tests
./fast_test.sh --failed --fast
```

### Fast Iteration Options

The `fast_test.sh` script optimizes the fix-test-pass/fail cycle:

| Option | Description |
|--------|-------------|
| `--fast` | Use haiku model (faster, lower cost) |
| `--skill NAME` | Test specific skill(s): issue, search, lifecycle, agile, etc. |
| `--id TC###` | Test specific test ID(s) |
| `--smoke` | Run 5 representative tests |
| `--parallel N` | Run N tests concurrently |
| `--failed` | Re-run only previously failed tests |

### OpenTelemetry Observability

Enable metrics export for test analysis:

```bash
# Start local collector (requires Docker)
docker run -p 4318:4318 otel/opentelemetry-collector

# Run tests with OTel export
pytest test_routing.py --otel --otlp-endpoint http://localhost:4318 -v
```

### Documenting Testing Insights

After debugging a non-obvious test failure, document the root cause in:
`plugins/jira-assistant-skills/skills/jira-assistant/tests/FAST_ITERATION.md`

**Why:** Context is lost between sessions. Future sessions need these insights to avoid re-discovering the same issues.

**What to document:**
- Environment factors that cause unexpected test behavior
- Semantic ambiguities (e.g., directory names conflicting with test inputs)
- Workarounds for Claude CLI quirks
- Container/networking gotchas

**Format example:**
```
**Discovered:** 2026-01-02
**Test case:** TC001 ("create a bug in TES")
**Root cause:** Working directory `/workspace/tests` caused Claude to interpret "TES" as a file reference
**Fix:** Changed container working directory to `/tmp`
```

See `plugins/jira-assistant-skills/skills/jira-assistant/tests/FAST_ITERATION.md` for detailed documentation.

### Sandboxed Container Testing

Run tests in Docker containers with restricted tool access for safe demos and focused testing:

```bash
cd plugins/jira-assistant-skills/skills/jira-assistant/tests

# List available sandbox profiles
./run_sandboxed.sh --list-profiles

# Run in read-only mode (safe for demos)
./run_sandboxed.sh --profile read-only

# Run with validation tests to verify restrictions work
./run_sandboxed.sh --profile read-only --validate

# Run specific tests in search-only mode
./run_sandboxed.sh --profile search-only -- -k "TC005"
```

**Available profiles:**

| Profile | Use Case | Allowed Operations |
|---------|----------|-------------------|
| `read-only` | Safe demos | `jira issue get`, `jira search`, `jira fields list/get` |
| `search-only` | JQL workshops | `jira search` only |
| `issue-only` | CRUD training | All `jira issue` commands |
| `full` | Full testing | No restrictions |

The sandbox uses Claude's `--allowedTools` flag with patterns like `Bash(jira issue get:*)` to restrict tool access.

## CLI Usage

The project provides a unified `jira` CLI entry point for all operations:

```bash
# Install the CLI (editable mode for development)
pip install -e .

# View all available command groups
jira --help

# Available command groups:
# - jira issue      - CRUD operations for issues
# - jira search     - JQL queries and filters
# - jira lifecycle  - Workflow transitions, versions, components
# - jira agile      - Epics, sprints, backlog management
# - jira collaborate - Comments, attachments, watchers
# - jira relationships - Issue links and dependencies
# - jira time       - Time tracking and worklogs
# - jira bulk       - Bulk operations
# - jira dev        - Git/PR integration
# - jira fields     - Custom field management
# - jira ops        - Cache and operational utilities
# - jira jsm        - Jira Service Management

# Get help for any command
jira issue --help
jira issue get --help
```

### Shell Completion

Enable tab-completion for the `jira` CLI:

```bash
# Bash (add to ~/.bashrc)
eval "$(_JIRA_COMPLETE=bash_source jira)"

# Zsh (add to ~/.zshrc)
eval "$(_JIRA_COMPLETE=zsh_source jira)"

# Fish (add to ~/.config/fish/completions/jira.fish)
_JIRA_COMPLETE=fish_source jira | source
```

### Global Options

All commands support these global options:
- `--profile, -p`: JIRA profile to use (from config)
- `--output, -o`: Output format (text, json, table)
- `--verbose, -v`: Enable verbose output
- `--quiet, -q`: Suppress non-essential output
- `--help`: Show help for any command

## Key Constraints

- **Python 3.10+**: Minimum version for union syntax (`X | Y`) and modern type hints
- **No external CLI tools**: All operations via Python/requests
- **Profile-aware**: All scripts must support `--profile` override
- **Validation first**: Call validators before API operations to fail fast
- **HTTP client reuse**: Use get_jira_client() which handles session management and retry

## Version Management

When releasing a new version, update version numbers in ALL of these files to stay in sync:

| File | Field | Purpose |
|------|-------|---------|
| `VERSION` | entire file | Release-please source of truth |
| `plugins/jira-assistant-skills/plugin.json` | `"version"` | Plugin manifest for marketplace |
| `.claude-plugin/marketplace.json` | `"metadata.version"` and `"plugins[0].version"` | Marketplace listing |

**Release workflow**:
1. Release-please automatically updates `VERSION` and creates a release PR
2. After merging the release PR, manually update `plugin.json` and `marketplace.json` to match
3. Commit with: `chore: sync plugin version to X.Y.Z`

**Why this matters**: Users installing via marketplace (`/plugin marketplace update`) rely on `plugin.json` version to detect updates. If versions are out of sync, users won't receive updates.

**Automation opportunity**: Consider adding a GitHub Action or pre-commit hook to sync versions automatically.

### Environment Setup

Use the interactive setup script to configure environment variables:

```bash
./scripts/setup-env.sh
```

This script:
- Prompts for JIRA credentials (site URL, email, API token)
- Optionally configures Anthropic API key for E2E tests
- Validates input and tests connections
- Saves to `~/.env` with secure permissions (chmod 600)
- Adds environment loader to shell config (~/.zshrc or ~/.bashrc)

### Run E2E Tests

```bash
# Requires ANTHROPIC_API_KEY (configure via ./scripts/setup-env.sh)
./scripts/run-e2e-tests.sh           # Docker
./scripts/run-e2e-tests.sh --local   # Local
./scripts/run-e2e-tests.sh --verbose # Verbose
```
