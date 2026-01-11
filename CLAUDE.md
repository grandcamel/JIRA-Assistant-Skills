# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code Plugin providing JIRA automation through fourteen modular skills. This is a **documentation-only** plugin - the CLI implementation is in the `jira-assistant-skills` PyPI package (source: `jira-assistant-skills-lib/` directory).

```
plugins/jira-assistant-skills/
├── plugin.json           # Plugin manifest
├── commands/             # Slash commands
├── config/               # Configuration examples
└── skills/               # 14 JIRA automation skills (SKILL.md docs)
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
# Install the CLI (includes library)
pip install jira-assistant-skills

# Set credentials
export JIRA_API_TOKEN="token-from-id.atlassian.com"
export JIRA_EMAIL="your@email.com"
export JIRA_SITE_URL="https://your-company.atlassian.net"

# Test
jira-as issue get PROJ-123
jira-as search query "project = PROJ"
```

## Architecture

**This project is a Claude Code plugin (documentation only).**

| Component | Location | Purpose |
|-----------|----------|---------|
| CLI (`jira-as`) | `jira-assistant-skills` package | Command implementation |
| Skills (SKILL.md) | This repo | Documentation for Claude |
| Tests | `jira-assistant-skills` package | 952 unit tests |

## Credentials Security

**Never commit**: API tokens, hardcoded URLs exposing internal infrastructure

**Always**:
- Use environment variables (`JIRA_API_TOKEN`, `JIRA_EMAIL`, `JIRA_SITE_URL`)
- Validate URLs are HTTPS-only

## How Claude Code Skills Work

**Fundamental concept**: Claude Code skills are context-loading mechanisms, NOT direct executors.

**The pattern:**
1. **Skill tool** → Loads SKILL.md content into Claude's context
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

## Adding/Modifying Skills

Skills are pure documentation - all implementation is in the CLI library.

```
plugins/jira-assistant-skills/skills/skill-name/
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

**Adding CLI commands** (in `jira-assistant-skills-lib/` directory):
1. Add command functions to `jira-assistant-skills-lib/src/jira_assistant_skills_lib/cli/commands/<skill>_cmds.py`
2. Add tests to `jira-assistant-skills-lib/tests/commands/test_<skill>_cmds.py`
3. Update the skill's SKILL.md in this repo to document the new commands

## Git (Quick Reference)

**CRITICAL: Never push directly to `origin/main`.** Local `main` is read-only.

This repo enforces linear history (no merge commits):

| Scope | Setting | Value |
|-------|---------|-------|
| Local | `pull.rebase` | `true` (auto-rebase on pull) |
| Local | `rebase.autostash` | `true` (stash/unstash around rebase) |
| GitHub | `required_linear_history` | `true` (rejects merge commits) |

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

- **CLI is in the package**: The `jira-as` CLI is in `jira-assistant-skills` package (source: `jira-assistant-skills-lib/` dir)
- **Mock mode for testing**: Set `JIRA_MOCK_MODE=true` to use mock client
- **Skill routing**: The `jira-assistant` hub skill routes to specific skills based on descriptions
- **SKILL.md discovery**: Claude reads SKILL.md files to understand capabilities. Keep "When to use this skill" section accurate

## Related Resources

| Document | Content |
|----------|---------|
| `docs/ARCHITECTURE.md` | Shared library, error handling, ADF, configuration |
| `docs/quick-start.md` | Getting started guide |
| `docs/configuration.md` | Configuration details |
| `docs/troubleshooting.md` | Common issues and solutions |
