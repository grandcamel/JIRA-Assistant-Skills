# JIRA Assistant Skills

A modular, production-ready Claude Code skills framework for JIRA REST API automation.

## Project Overview

This project provides 14 specialized skills for interacting with JIRA via natural language:

| Skill | Purpose |
|-------|---------|
| `jira-assistant` | Hub/router with progressive disclosure |
| `jira-issue` | Core CRUD operations on issues |
| `jira-lifecycle` | Workflow/transition management |
| `jira-search` | JQL queries, saved filters, bulk operations |
| `jira-collaborate` | Comments, attachments, watchers |
| `jira-agile` | Epics, sprints, backlog, story points |
| `jira-relationships` | Issue linking, dependencies, cloning |
| `jira-time` | Time tracking, worklogs, estimates |
| `jira-jsm` | Jira Service Management |
| `jira-bulk` | Bulk operations with dry-run support |
| `jira-dev` | Git branch names, commit parsing, PR descriptions |
| `jira-fields` | Custom field management |
| `jira-ops` | Cache management, request batching |
| `jira-admin` | Project and permission administration |

## Architecture

### Directory Structure

```
.claude/
├── settings.example.json      # Example config (copy to settings.local.json)
└── settings.local.json        # Personal credentials (gitignored)

./ # Plugin package
├── plugin.json                # Plugin manifest
├── commands/                  # Slash commands
├── config/                    # Configuration examples
└── skills/
    ├── jira-assistant/        # Hub router
    ├── jira-issue/            # Issue CRUD
    ├── jira-lifecycle/        # Workflow transitions
    ├── jira-search/           # JQL queries
    ├── jira-collaborate/      # Comments, attachments
    ├── jira-agile/            # Sprints, boards
    ├── jira-relationships/    # Issue links
    ├── jira-time/             # Time tracking
    ├── jira-jsm/              # Service Management
    ├── jira-bulk/             # Bulk operations
    ├── jira-dev/              # Developer integration
    ├── jira-fields/           # Custom fields
    ├── jira-ops/              # Operations
    ├── jira-admin/            # Administration
    └── shared/                # Shared config and tests
        ├── config/
        ├── docs/
        └── tests/

jira-assistant-skills-lib/     # PyPI library (source)
├── src/jira_assistant_skills_lib/
│   ├── cli/                   # CLI implementation
│   │   ├── main.py            # Entry point
│   │   ├── cli_utils.py       # Shared utilities
│   │   └── commands/          # Command groups
│   ├── mock/                  # Mock client (10 mixins)
│   └── *.py                   # Core modules
└── tests/                     # 952 unit tests
```

### Shared Library Pattern

All scripts import from the [jira-assistant-skills-lib](https://pypi.org/project/jira-assistant-skills-lib/) PyPI package:

```python
from jira_assistant_skills_lib import (
    get_jira_client,
    JiraError,
    ValidationError,
    validate_issue_key,
    format_issue,
)
```

### Shared Library Components

The `jira-assistant-skills-lib` package provides:

| Module | Purpose |
|--------|---------|
| `jira_client` | HTTP client with retry logic and session management |
| `config_manager` | Multi-source configuration |
| `error_handler` | Exception hierarchy |
| `validators` | Input validation (issue keys, JQL, URLs) |
| `formatters` | Output formatting (tables, JSON, CSV) |
| `adf_helper` | Atlassian Document Format conversion |
| `time_utils` | JIRA time format parsing |
| `cache` | SQLite-based caching with TTL |
| `credential_manager` | Keychain integration |
| `transition_helpers` | Fuzzy workflow matching |
| `user_helpers` | User resolution to account IDs |
| `jsm_utils` | Service Management SLA utilities |

### CLI Entry Point

The project provides a unified CLI via the `jira-as` command:

```bash
# Install in development mode
pip install -e jira-assistant-skills-lib/

# Verify installation
jira-as --version
```

#### CLI Usage

```bash
# Get help
jira-as --help
jira-as issue --help

# Issue operations
jira-as issue get PROJ-123
jira-as issue create PROJ --type Bug --summary "Fix login"
jira-as issue update PROJ-123 --priority High
jira-as issue delete PROJ-123

# Search and JQL
jira-as search query "project = PROJ AND status = Open"
jira-as search query "assignee = currentUser()" --max-results 50

# Workflow transitions
jira-as lifecycle transitions PROJ-123
jira-as lifecycle transition PROJ-123 "In Progress"

# Agile operations
jira-as agile sprints --board 1
jira-as agile move-to-sprint PROJ-123 --sprint 42

# Time tracking
jira-as time log PROJ-123 --time "2h 30m" --comment "Code review"
jira-as time worklogs PROJ-123

# Bulk operations
jira-as bulk transition "project = PROJ AND status = Open" "In Progress" --dry-run

# Administration
jira-as admin projects
jira-as admin users --project PROJ
```

#### Available Command Groups

| Group | Description |
|-------|-------------|
| `issue` | Issue CRUD operations |
| `search` | JQL queries and saved filters |
| `lifecycle` | Workflow transitions and status changes |
| `agile` | Sprint, board, and backlog management |
| `collaborate` | Comments, attachments, watchers |
| `relationships` | Issue links and dependencies |
| `time` | Time tracking and worklogs |
| `fields` | Custom field operations |
| `bulk` | Bulk operations with dry-run |
| `dev` | Developer workflow integration |
| `ops` | Cache and request management |
| `jsm` | Jira Service Management |
| `admin` | Project administration |

## Configuration System

### Priority Order

1. Environment variables (highest)
2. System keychain (via `keyring` library)
3. `.claude/settings.local.json` (personal, gitignored)
4. `.claude/settings.json` (shared defaults)
5. Built-in defaults (lowest)

### Environment Variables

```bash
# Required
export JIRA_API_TOKEN="your-api-token"           # From id.atlassian.com
export JIRA_EMAIL="your@email.com"               # Account email
export JIRA_SITE_URL="https://company.atlassian.net"

# Optional
export JIRA_MOCK_MODE="true"                     # Use mock client
export JIRA_DEFAULT_PROJECT="PROJ"               # Default project key

# Agile field overrides (if custom field IDs differ)
export JIRA_EPIC_LINK_FIELD="customfield_10014"
export JIRA_STORY_POINTS_FIELD="customfield_10016"
export JIRA_SPRINT_FIELD="customfield_10020"
```

### Settings File Example

```json
{
  "jira": {
    "site_url": "https://company.atlassian.net",
    "email": "your@email.com",
    "default_project": "PROJ",
    "page_size": 50
  }
}
```

## Authentication

### API Token (Required for Cloud)

1. Generate token at https://id.atlassian.com/manage-profile/security/api-tokens
2. Set via environment or config:
   ```bash
   export JIRA_API_TOKEN="your-token"
   export JIRA_EMAIL="your@email.com"
   ```

### Personal Access Token (Data Center)

For JIRA Data Center/Server:
```bash
export JIRA_PAT="your-personal-access-token"
```

## Error Handling Strategy

### 4-Layer Approach

1. **Validation Layer**: Input validation before API calls (validators.py)
2. **HTTP Layer**: Retry on transient failures (429, 5xx)
3. **API Layer**: Parse JIRA error responses
4. **Application Layer**: User-friendly error messages with troubleshooting hints

### Exception Hierarchy

```
JiraError (base)
├── AuthenticationError (401)
├── PermissionError (403)
├── ValidationError (400)
├── NotFoundError (404)
├── RateLimitError (429)
├── ConflictError (409)
└── ServerError (5xx)
```

### Using the Error Decorator

```python
from jira_assistant_skills_lib.cli.cli_utils import handle_jira_errors

@handle_jira_errors
def main():
    with get_jira_client() as client:
        issue = client.get_issue("PROJ-123")
```

### Exit Codes

| Code | Error Type |
|------|------------|
| 0 | Success |
| 1 | General error |
| 2 | Validation error |
| 3 | Authentication error |
| 4 | Permission error |
| 5 | Not found error |
| 6 | Rate limit error |
| 7 | Server error |

## JQL Query Patterns

### Basic Queries

```jql
# Find issues by project
project = PROJ

# Find by status
project = PROJ AND status = "In Progress"

# Find by assignee
assignee = currentUser()
assignee = "john.doe@company.com"

# Find unassigned
assignee IS EMPTY
```

### Time-Based Queries

```jql
# Created recently
created >= -7d

# Updated in last hour
updated >= -1h

# Due soon
due <= 7d AND due >= 0d

# Overdue
due < now() AND resolution IS EMPTY
```

### Advanced Patterns

```jql
# Issues in active sprints
sprint IN openSprints()

# Epics with incomplete children
issuetype = Epic AND "Epic Status" != Done

# Issues with specific labels
labels IN ("urgent", "customer-facing")

# Text search in summary/description
text ~ "performance issue"

# Issues linked to specific issue
issue IN linkedIssues("PROJ-123")

# Subtasks of an issue
parent = PROJ-123

# Issues without subtasks
issueFunction NOT IN hasSubtasks()

# Recently resolved by team
resolved >= -7d AND assignee IN membersOf("dev-team")
```

### JQL Functions

| Function | Description |
|----------|-------------|
| `currentUser()` | Logged-in user |
| `membersOf("group")` | Users in group |
| `openSprints()` | Active sprints |
| `closedSprints()` | Completed sprints |
| `futureSprints()` | Planned sprints |
| `linkedIssues("KEY")` | Linked to issue |
| `hasSubtasks()` | Issues with subtasks |
| `now()` | Current timestamp |

## JiraClient Usage

### Context Manager Pattern (Required)

```python
from jira_assistant_skills_lib import get_jira_client

# Correct - context manager handles cleanup
with get_jira_client() as client:
    issue = client.get_issue("PROJ-123")
    return issue

# Wrong - deprecated pattern
client = get_jira_client()
try:
    issue = client.get_issue("PROJ-123")
finally:
    client.close()  # Don't do this
```

### Common Operations

```python
with get_jira_client() as client:
    # Get issue
    issue = client.get_issue("PROJ-123")

    # Create issue
    new_issue = client.create_issue(
        project="PROJ",
        issue_type="Bug",
        summary="Fix login bug",
        description="Users cannot login after password reset",
    )

    # Update issue
    client.update_issue("PROJ-123", {"priority": {"name": "High"}})

    # Transition issue
    client.transition_issue("PROJ-123", "In Progress")

    # Add comment
    client.add_comment("PROJ-123", "Working on this now")

    # Search with JQL
    issues = client.search_issues("project = PROJ AND status = Open")
```

## Mock Client

### Architecture

The mock client uses mixin composition for modularity:

```
jira-assistant-skills-lib/src/jira_assistant_skills_lib/mock/
├── __init__.py      # Exports MockJiraClient, is_mock_mode
├── base.py          # MockJiraClientBase with core operations
├── clients.py       # Composed client (Base + all mixins)
├── factories.py     # Test data factories
└── mixins/          # 10 specialized mixins
    ├── admin.py     # Project/user administration
    ├── agile.py     # Boards, sprints, backlog
    ├── collaborate.py # Comments, attachments
    ├── dev.py       # Developer integration
    ├── fields.py    # Custom fields
    ├── jsm.py       # Service desk, SLAs
    ├── relationships.py # Issue links
    ├── search.py    # JQL parsing
    └── time.py      # Worklogs
```

### Enabling Mock Mode

```bash
export JIRA_MOCK_MODE=true
```

The `get_jira_client()` function auto-detects:

```python
def get_jira_client():
    from .mock import is_mock_mode, MockJiraClient
    if is_mock_mode():
        return MockJiraClient()
    # ... normal client creation
```

### Seed Data

Mock client provides deterministic test data:

| Project | Issues |
|---------|--------|
| DEMO | DEMO-84 (Epic), DEMO-85 (Story), DEMO-86 (Bug), DEMO-87 (Task), DEMO-91 (Bug) |
| DEMOSD | DEMOSD-1 through DEMOSD-5 (Service desk requests) |

| User | Account ID |
|------|------------|
| Jason Krueger | abc123 |
| Jane Manager | def456 |

## Testing

### Test Configuration

Tests are configured via `pytest.ini` at the project root:
- Uses `--import-mode=importlib` to avoid module name conflicts
- Excludes `live_integration` directories by default
- Defines 57+ markers for test categorization

### Test Coverage Summary

| Category | Tests | Status |
|----------|-------|--------|
| Unit Tests (library) | 952 | Passing |
| Live Integration Tests | ~100 | Requires credentials |
| E2E Tests | ~20 | Requires Claude CLI |

### Unit Tests

```bash
# Install dependencies
pip install -e "jira-assistant-skills-lib/[dev]"

# Run all unit tests
pytest jira-assistant-skills-lib/tests/ -v

# Run tests for specific module
pytest jira-assistant-skills-lib/tests/test_jira_client.py -v

# Run with coverage
pytest jira-assistant-skills-lib/tests/ --cov=jira_assistant_skills_lib -v
```

### Live Integration Tests

Live integration tests require a JIRA instance and credentials.

#### Environment Variables

```bash
export JIRA_TEST_URL="https://your-site.atlassian.net"
export JIRA_TEST_EMAIL="your@email.com"
export JIRA_TEST_TOKEN="your-api-token"
export JIRA_TEST_PROJECT="SKILLSTEST"  # Test project key
```

#### Running Tests

```bash
# Run all live integration tests
pytest skills/shared/tests/live_integration/ -v

# Run with specific markers
pytest -m "live" -v
pytest -m "live and not destructive" -v

# Run single test class
pytest skills/shared/tests/live_integration/test_utils.py::TestIssueBuilder -v
```

### Test Markers

The project defines 57+ pytest markers for fine-grained test selection:

#### Core Markers

```python
@pytest.mark.unit          # Fast unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.live          # Requires live API
@pytest.mark.e2e           # End-to-end tests
@pytest.mark.slow          # Long-running tests
@pytest.mark.destructive   # Modifies/deletes data
```

#### Skill-Specific Markers

```python
@pytest.mark.issue         # Issue CRUD tests
@pytest.mark.search        # JQL/search tests
@pytest.mark.agile         # Sprint/board tests
@pytest.mark.jsm           # Service Management tests
@pytest.mark.bulk          # Bulk operation tests
@pytest.mark.admin         # Administration tests
```

#### Environment Markers

```python
@pytest.mark.cloud_only    # JIRA Cloud only
@pytest.mark.dc_only       # Data Center only
@pytest.mark.docker_required  # Requires Docker
```

### Test Framework Architecture

#### Singleton Pattern with Double-Checked Locking

Docker containers and external connections use thread-safe singleton:

```python
# In jira_container.py
_shared_connection = None
_connection_lock = threading.Lock()

def get_jira_connection():
    global _shared_connection
    if _shared_connection is None:
        with _connection_lock:
            if _shared_connection is None:  # Double-check
                _shared_connection = JiraContainer()
    return _shared_connection
```

#### Reference Counting for Container Lifecycle

```python
class JiraContainer:
    def start(self):
        with self._lock:
            self._ref_count += 1
            if self._is_started:
                return self  # Reuse existing
            # ... start container

    def stop(self):
        with self._lock:
            self._ref_count -= 1
            if self._ref_count > 0:
                return  # Keep running
            # ... stop container
```

#### Environment-Based Adaptation

```python
@pytest.fixture(scope="session")
def jira_connection():
    if os.getenv("JIRA_TEST_URL"):
        return ExternalJiraConnection()
    elif docker_available():
        return JiraContainer()
    else:
        pytest.skip("No test environment available")
```

### Test Fixture Reference

#### Unit Test Fixtures (conftest.py)

| Fixture | Scope | Description |
|---------|-------|-------------|
| `mock_client` | function | Mock JiraClient with context manager |
| `mock_config` | function | Mock configuration dictionary |
| `sample_issue` | function | Sample issue response |
| `sample_search_results` | function | Sample JQL results |

#### Live Integration Fixtures (fixtures.py)

| Fixture | Scope | Description |
|---------|-------|-------------|
| `jira_connection` | session | Container or external connection |
| `jira_client` | session | Configured JiraClient |
| `test_project` | session | Test project key |
| `test_issue` | function | Fresh test issue (auto-cleanup) |
| `issue_helper` | function | IssueBuilder instance |
| `search_helper` | function | Search convenience methods |

### Test Data Generation

#### IssueBuilder Fluent API

```python
from test_utils import IssueBuilder

issue = (IssueBuilder(client, "PROJ")
    .with_summary("Test issue")
    .with_type("Bug")
    .with_priority("High")
    .with_labels(["test", "automated"])
    .with_description("Test description")
    .with_assignee("abc123")
    .build())
```

#### Assertion Helpers

```python
from test_utils import assert_search_returns_results, assert_issue_has_field

# Assert JQL returns results
issues = assert_search_returns_results(
    client,
    "project = PROJ AND labels = test",
    min_count=1,
    timeout=10,
)

# Assert field value
assert_issue_has_field(issue, "priority", expected_value="High")
```

#### Wait Utilities

```python
from test_utils import wait_for_transition, wait_for_assignment

# Wait for status change
success = wait_for_transition(client, "PROJ-123", "Done", timeout=30)

# Wait for assignment
success = wait_for_assignment(client, "PROJ-123", "abc123", timeout=10)
```

## Adding New Skills

### Required Files

```
skills/new-skill/
├── SKILL.md              # Skill documentation
├── docs/                 # Guides and documentation
├── references/           # API docs (optional)
├── assets/templates/     # JSON templates (optional)
└── tests/
    ├── conftest.py       # Skill-specific fixtures
    └── test_*.py
```

### SKILL.md Template

```markdown
# jira-new-skill

Brief description.

## When to Use This Skill

Keywords and scenarios that trigger this skill.

## What This Skill Does

- Feature 1
- Feature 2

## Available Commands

\`\`\`bash
jira-as newskill command --option value
\`\`\`

## Examples

Example usage scenarios.

## Risk Level

| Operation | Risk |
|-----------|------|
| Read operations | - |
| Create operations | Warning |
| Delete operations | Danger |
```

### Adding CLI Commands

1. Add command module in `jira-assistant-skills-lib/src/jira_assistant_skills_lib/cli/commands/`
2. Register in `cli/main.py`
3. Add tests in `tests/commands/`
4. Update SKILL.md documentation

## How Claude Code Skills Work

**Fundamental concept**: Skills are context-loading mechanisms, NOT direct executors.

**The pattern:**
1. **Skill tool** → Loads SKILL.md content into Claude's context
2. **Bash tool** → Claude executes `jira-as` CLI commands described in the skill

**Key behaviors:**
- Once loaded, skill context persists for the entire conversation
- Subsequent operations use Bash directly WITHOUT re-invoking the Skill tool
- SKILL.md should document CLI commands that Claude will execute

**Expected tool sequences:**

| Scenario | Expected Tools |
|----------|---------------|
| First JIRA operation | `['Skill', 'Bash']` |
| Subsequent operations | `['Bash']` |
| Knowledge question only | `['Skill']` |

## Git Workflow

### Branch Strategy

**CRITICAL: Never push directly to `origin/main`.** Local `main` is read-only.

This repo enforces linear history (no merge commits):

| Scope | Setting | Value |
|-------|---------|-------|
| Local | `pull.rebase` | `true` |
| Local | `rebase.autostash` | `true` |
| GitHub | `required_linear_history` | `true` |

### Creating PRs

```bash
# Start work
git checkout dev

# Create PR branch
git checkout -b feat/my-feature
git push -u origin feat/my-feature
gh pr create --base main --head feat/my-feature
```

### Commit Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

Examples:
```
feat(agile): add sprint velocity tracking
fix(client): handle 429 rate limit with retry
docs(search): add JQL examples
test(bulk): add dry-run integration tests
```

## Credentials Security

### DO

- Use environment variables for sensitive data
- Store tokens in `.claude/settings.local.json` (gitignored)
- Use system keychain when available
- Rotate tokens regularly

### DON'T

- Commit tokens or passwords to git
- Log sensitive values
- Share settings.local.json
- Hardcode credentials in scripts

## Common Issues

### Authentication Errors

```
AuthenticationError: 401 Unauthorized
```

Solutions:
- Verify API token is valid and not expired
- Check email matches the JIRA account
- Ensure token has required permissions
- For Cloud: regenerate at id.atlassian.com

### Permission Errors

```
PermissionError: 403 Forbidden
```

Solutions:
- Verify user has project access
- Check issue-level security scheme
- Ensure required capabilities (browse, edit, transition)

### Rate Limiting

```
RateLimitError: 429 Too Many Requests
```

Solutions:
- Use bulk operations instead of individual calls
- Add delays between requests
- Check Atlassian rate limit headers
- Use caching for repeated reads

### Issue Not Found

```
NotFoundError: Issue PROJ-123 does not exist
```

Solutions:
- Verify issue key format (PROJECT-NUMBER)
- Check project exists and is accessible
- Issue may have been deleted or moved

### JQL Syntax Errors

```
ValidationError: JQL parse error at position 15
```

Solutions:
- Check field names are valid
- Quote string values: `status = "In Progress"`
- Escape special characters
- Use JQL autocomplete in JIRA Web

### Custom Field Errors

```
ValidationError: Field 'customfield_10014' cannot be set
```

Solutions:
- Verify field ID is correct for your instance
- Check field is on the issue's screen
- Field may require specific format (e.g., option ID vs name)
- Use `jira-as fields list` to discover field IDs

## Gotchas

- **Context manager required**: Always use `with get_jira_client() as client:` pattern
- **Mock mode**: Set `JIRA_MOCK_MODE=true` for testing without API calls
- **Skill routing**: The `jira-assistant` hub routes based on skill descriptions
- **ADF format**: JIRA Cloud uses Atlassian Document Format for rich text
- **Field IDs vary**: Custom field IDs differ between instances
- **Version sync**: Keep `pyproject.toml` and `__version__` in sync
- **Test mocks**: Mock fixtures must include `__enter__` and `__exit__`
- **Linear history**: Repository requires rebase merges, no merge commits

## Related Resources

| Document | Content |
|----------|---------|
| `jira-assistant-skills-lib/CLAUDE.md` | Library implementation details |
| `skills/shared/docs/DECISION_TREE.md` | Skill routing logic |
| `skills/shared/docs/SAFEGUARDS.md` | Safety procedures |
| `skills/shared/docs/QUICK_REFERENCE.md` | JQL cheat sheet |
| `docs/ARCHITECTURE.md` | System architecture |
| `docs/quick-start.md` | Getting started guide |
| `docs/troubleshooting.md` | Detailed troubleshooting |
