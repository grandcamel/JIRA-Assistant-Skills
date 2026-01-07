# CLI Reference

The unified `jira` CLI entry point for all JIRA operations.

## Installation

```bash
pip install -e .  # Editable mode for development
```

## Command Groups

| Group | Purpose |
|-------|---------|
| `jira issue` | CRUD operations for issues |
| `jira search` | JQL queries and filters |
| `jira lifecycle` | Workflow transitions, versions, components |
| `jira agile` | Epics, sprints, backlog management |
| `jira collaborate` | Comments, attachments, watchers |
| `jira relationships` | Issue links and dependencies |
| `jira time` | Time tracking and worklogs |
| `jira bulk` | Bulk operations |
| `jira dev` | Git/PR integration |
| `jira fields` | Custom field management |
| `jira ops` | Cache and operational utilities |
| `jira jsm` | Jira Service Management |
| `jira admin` | Project and permission administration |

```bash
# Get help
jira --help
jira issue --help
jira issue get --help
```

## Global Options

All commands support:
- `--profile, -p`: JIRA profile to use (from config)
- `--output, -o`: Output format (text, json, table)
- `--verbose, -v`: Enable verbose output
- `--quiet, -q`: Suppress non-essential output
- `--help`: Show help

## Shell Completion

**Bash** (add to ~/.bashrc):
```bash
eval "$(_JIRA_COMPLETE=bash_source jira)"
```

**Zsh** (add to ~/.zshrc):
```bash
eval "$(_JIRA_COMPLETE=zsh_source jira)"
```

**Fish** (add to ~/.config/fish/completions/jira.fish):
```bash
_JIRA_COMPLETE=fish_source jira | source
```

## Version Management

```bash
# Check if all versions are in sync
./scripts/sync-version.sh --check

# Sync all files to match VERSION
./scripts/sync-version.sh

# Set a new version
./scripts/sync-version.sh --set 2.3.0
```

**Files synchronized** (source of truth: `VERSION`):

| File | Field |
|------|-------|
| `VERSION` | Source of truth |
| `pyproject.toml` | `version` |
| `plugins/jira-assistant-skills/plugin.json` | `"version"` |
| `.claude-plugin/marketplace.json` | `"metadata.version"`, `"plugins[0].version"` |
| `.release-please-manifest.json` | `"."` |

## Distribution Channels

| Channel | Package | Install Command | Use Case |
|---------|---------|-----------------|----------|
| **PyPI** | `jira-assistant-skills` | `pip install jira-assistant-skills` | CLI tool |
| **GitHub** | Plugin manifest | `claude plugin marketplace add https://github.com/grandcamel/jira-assistant-skills.git#main` | Claude Code plugin |

**Both must be updated when releasing:**
1. PyPI: `twine upload`
2. GitHub: `git push` (main branch or tag)

## Environment Setup

```bash
./scripts/setup-env.sh
```

This script:
- Prompts for JIRA credentials
- Optionally configures Anthropic API key for E2E tests
- Validates input and tests connections
- Saves to `~/.env` with secure permissions

## E2E Tests

```bash
./scripts/run-e2e-tests.sh           # Docker
./scripts/run-e2e-tests.sh --local   # Local
./scripts/run-e2e-tests.sh --verbose # Verbose
```
