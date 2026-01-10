# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code Plugin providing JIRA automation through fourteen modular skills. Plugin is self-contained in `plugins/jira-assistant-skills/`.

```
plugins/jira-assistant-skills/
├── plugin.json           # Plugin manifest
├── commands/             # Slash commands
├── config/               # Configuration examples
└── skills/               # 14 JIRA automation skills
```

### Available Skills

| Skill | Purpose |
|-------|---------|
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
| `jira-assistant` | Hub skill for routing and discovery |

## Quick Start

```bash
# Setup
pip install -e .
pip install jira-assistant-skills-lib
export JIRA_API_TOKEN="token-from-id.atlassian.com"
export JIRA_EMAIL="your@email.com"
export JIRA_SITE_URL="https://your-company.atlassian.net"

# Test
jira-as issue get PROJ-123
jira-as search query "project = PROJ"
```

## Key Constraints

- **Python 3.10+**: Minimum version for union syntax (`X | Y`) and modern type hints
- **No external CLI tools**: All operations via Python/requests
- **Validation first**: Call validators before API operations to fail fast
- **HTTP client reuse**: Use `get_jira_client()` for session management and retry

## Credentials Security

**Never commit**: API tokens, hardcoded URLs exposing internal infrastructure

**Always**:
- Use environment variables (`JIRA_API_TOKEN`, `JIRA_EMAIL`, `JIRA_SITE_URL`)
- Validate URLs are HTTPS-only (`validators.validate_url`)

## How Claude Code Skills Work

**Fundamental concept**: Claude Code skills are context-loading mechanisms, NOT direct executors.

**The pattern:**
1. **Skill tool** → Loads SKILL.md content into Claude's context (triggered by YAML frontmatter matching)
2. **Bash tool** → Claude executes the `jira-as` CLI commands described in the skill

**Key behaviors:**
- Once loaded, skill context persists for the entire conversation
- Subsequent operations use Bash directly WITHOUT re-invoking the Skill tool
- SKILL.md should document CLI commands that Claude will execute via Bash

**Expected tool sequences:**
| Scenario | Expected Tools |
|----------|---------------|
| First JIRA operation | `['Skill', 'Bash']` |
| Subsequent operations | `['Bash']` |
| Knowledge question only | `['Skill']` |

**SKILL.md implications:**
- "Examples" section should show `jira-as` CLI commands Claude will run
- Clear command examples help Claude execute correctly on first try
- Skill does NOT execute commands itself - it provides instructions for Claude to follow

## Adding Scripts

1. Place in skill's `scripts/` directory
2. Import: `from jira_assistant_skills_lib import ...`
3. Use shared utilities from `shared/scripts/script_utils.py`
4. Add shebang `#!/usr/bin/env python3`, make executable
5. Update skill's SKILL.md

**Script utilities** (`shared/scripts/script_utils.py`):
- `add_common_args(parser)` - Adds `--profile` and `--output` args
- `add_bulk_args(parser)` - Adds `--dry-run`, `--max-issues`, `--yes` for bulk ops
- `parse_comma_list(value)` - Parse "a,b,c" → ["a", "b", "c"]
- `parse_json_arg(value)` - Parse JSON string args
- `format_output(result, format)` - Handle text vs JSON output
- `run_script(main_func)` - Wrapper with standard error handling
- `@script_main` - Decorator version of `run_script`
- `ScriptResult` - Helper for building structured results

**Script template**:
```python
#!/usr/bin/env python3
import argparse
import sys
sys.path.insert(0, str(__file__).replace("/scripts/my_script.py", "/../shared/scripts"))

from jira_assistant_skills_lib import get_jira_client, JiraError
from jira_assistant_skills_lib.validators import validate_issue_key
from script_utils import add_common_args, format_output, run_script

def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(...)
    add_common_args(parser)  # Adds --profile, --output
    args = parser.parse_args(argv)

    client = get_jira_client(args.profile)
    result = client.get_issue(args.issue_key)
    format_output(result, args.output, success_message=f"Found: {result['key']}")

if __name__ == '__main__':
    run_script(main)  # Handles JiraError, KeyboardInterrupt, etc.
```

## Adding Skills

```
plugins/jira-assistant-skills/skills/new-skill/
├── SKILL.md              # Description for autonomous discovery
├── scripts/              # Executable Python scripts
├── tests/                # Unit and integration tests
├── references/           # API docs, guides (optional)
└── assets/templates/     # JSON templates (optional)
```

**SKILL.md format**:
- "When to use this skill" section for autonomous discovery
- "What this skill does" with feature list
- "Available scripts" with descriptions
- "Examples" with concrete bash commands

## Available Scripts

Scripts in `scripts/` for development and testing:

| Script | Purpose |
|--------|---------|
| `run_tests.sh` | Main unit test runner (runs each skill separately) |
| `run_single_test.sh` | Run individual test file, class, or method |
| `run_live_tests.sh` | Live integration tests with real JIRA credentials |
| `run-e2e-tests.sh` | End-to-end tests with Claude Code (Docker or local) |
| `setup-env.sh` | Interactive environment configuration wizard |
| `sync-version.sh` | Synchronize version across all project files |
| `install.sh` | Unix installer (clones repo, installs deps, runs setup) |

### Testing Commands

```bash
# Run all unit tests (required before merge)
./scripts/run_tests.sh

# Run specific skill
./scripts/run_tests.sh --skill jira-bulk

# Run single test
./scripts/run_single_test.sh jira-bulk test_bulk_assign.py

# Run with coverage (95% required)
./scripts/run_tests.sh --coverage --min-coverage 95

# Run live integration tests (requires JIRA credentials)
./scripts/run_live_tests.sh

# Run E2E tests
./scripts/run-e2e-tests.sh --local
```

### Version Management

```bash
# Check if versions are in sync
./scripts/sync-version.sh --check

# Sync all files to VERSION
./scripts/sync-version.sh

# Set new version and sync
./scripts/sync-version.sh --set 2.3.0
```

### Environment Setup

```bash
# Interactive setup (prompts for JIRA credentials, tests connection)
./scripts/setup-env.sh
```

## Git (Quick Reference)

**CRITICAL: Never push directly to `origin/main`.** Local `main` is read-only.

```bash
# Start work
git checkout dev

# Create PR (when requested)
git checkout -b <pr-branch-name>
git push -u origin <pr-branch-name>
gh pr create --base main --head <pr-branch-name>
```

**Commit format**: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

## Gotchas

- **Mock mode for testing**: Set `JIRA_MOCK_MODE=true` to use mock client instead of real JIRA API. Useful for skill testing without credentials.
- **Shared test fixtures**: Common fixtures in `skills/shared/tests/conftest.py`. Import with `from shared.tests.conftest import *` in skill conftest.py files.
- **Skill routing**: The `jira-assistant` hub skill routes to specific skills based on descriptions. If routing fails (goes to setup instead of skill), check SKILL.md "When to use" sections.
- **Script imports**: Scripts must use `from jira_assistant_skills_lib import ...` not relative imports. The library is installed separately.
- **SKILL.md discovery**: Claude reads SKILL.md files to understand capabilities. Keep "When to use this skill" section accurate and specific.
- **jira-as CLI from wheel, not editable**: The `jira-as` CLI is defined in root `pyproject.toml`. Editable installs (`pip install -e .`) fail due to broken venv symlinks in skill directories. Use `pip install dist/*.whl` or build fresh wheel with `hatch build`.
- **Rebuild wheel after changes**: Changes to the package (CLI, skills) require rebuilding the wheel (`hatch build`) before they take effect. The wheel is NOT auto-rebuilt.

## Best Practices

- **Bump version before merging PRs**: Always bump the version per [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and run `./scripts/sync-version.sh` before merging any PR
- Always use `#!/usr/bin/env bash` shebang for bash scripts
- Always use `./scripts/sync-version.sh` when bumping versions
- Run `./scripts/run_tests.sh` before committing
- Use `--force-with-lease` for force pushes
- Always use `--rebase` with git pull
- Ask for PR branch names before creating pull requests

## Related Resources

Detailed documentation in `docs/`:

| Document | Content |
|----------|---------|
| `docs/ARCHITECTURE.md` | Shared library, error handling, ADF, configuration, API patterns |
| `docs/TESTING.md` | Unit testing, coverage, live integration, routing tests, TDD |
| `docs/GIT_WORKFLOW.md` | Branch strategy, PR process, conventional commits |
| `docs/CONTAINER_TESTING.md` | Docker testing, devcontainer, sandbox profiles |
| `docs/PARALLEL_SUBAGENTS.md` | Subagent patterns, worktrees, multi-agent coordination |
| `docs/CLI_REFERENCE.md` | CLI usage, shell completion, version management, distribution |
| `docs/quick-start.md` | Getting started guide |
| `docs/configuration.md` | Configuration details |
| `docs/troubleshooting.md` | Common issues and solutions |
