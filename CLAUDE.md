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

## Adding Skills

Skills are pure documentation - all implementation is in the CLI (`src/jira_assistant_skills/cli/commands/`).

```
plugins/jira-assistant-skills/skills/new-skill/
├── SKILL.md              # Description for autonomous discovery
├── docs/                 # Guides and documentation
├── references/           # API docs, quick references (optional)
└── assets/templates/     # JSON templates (optional)
```

**SKILL.md format**:
- "When to use this skill" section for autonomous discovery
- "What this skill does" with feature list
- "Available Commands" with CLI command examples
- Examples showing `jira-as` CLI commands

**Adding CLI commands**:
1. Add command functions to `src/jira_assistant_skills/cli/commands/<skill>_cmds.py`
2. Add tests to `src/jira_assistant_skills/tests/commands/test_<skill>_cmds.py`
3. Update the skill's SKILL.md to document the new commands

## Development Scripts

Scripts in the root `scripts/` directory for development and testing:

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

### Repository Settings

This repo enforces linear history (no merge commits):

| Scope | Setting | Value |
|-------|---------|-------|
| Local | `pull.rebase` | `true` (auto-rebase on pull) |
| Local | `rebase.autostash` | `true` (stash/unstash around rebase) |
| GitHub | `required_linear_history` | `true` (rejects merge commits) |
| GitHub | `required_pull_request_reviews` | `1` (PRs require 1 approval) |

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

- **Mock mode for testing**: Set `JIRA_MOCK_MODE=true` to use mock client instead of real JIRA API. Useful for testing without credentials.
- **Test fixtures**: Common fixtures in `src/jira_assistant_skills/tests/conftest.py`.
- **Skill routing**: The `jira-assistant` hub skill routes to specific skills based on descriptions. If routing fails (goes to setup instead of skill), check SKILL.md "When to use" sections.
- **SKILL.md discovery**: Claude reads SKILL.md files to understand capabilities. Keep "When to use this skill" section accurate and specific.
- **jira-as CLI from wheel, not editable**: The `jira-as` CLI is defined in root `pyproject.toml`. Editable installs (`pip install -e .`) fail due to broken venv symlinks in skill directories. Use `pip install dist/*.whl` or build fresh wheel with `hatch build`.
- **Rebuild wheel after changes**: Changes to the package (CLI, commands) require rebuilding the wheel (`hatch build`) before they take effect. The wheel is NOT auto-rebuilt.
- **Skills are documentation only**: All implementation logic is in `src/jira_assistant_skills/cli/commands/`. Skills provide SKILL.md documentation that Claude uses to understand capabilities and execute CLI commands.

## Best Practices

- **Bump version before merging PRs**: Always bump the version per [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and run `./scripts/sync-version.sh` before merging any PR
- Always use `#!/usr/bin/env bash` shebang for bash scripts
- Always use `./scripts/sync-version.sh` when bumping versions
- Run `./scripts/run_tests.sh` before committing
- Use `--force-with-lease` for force pushes
- Rebase is automatic via `pull.rebase=true` config
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
