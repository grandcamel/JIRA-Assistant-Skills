# CLI Reference

The unified `jira-as` CLI entry point for all JIRA operations.

## Installation

```bash
pip install "jira-as>=1.1.3"  # From public PyPI
```

## Command Groups

| Group | Purpose |
|-------|---------|
| `jira-as issue` | CRUD operations for issues |
| `jira-as search` | JQL queries and filters |
| `jira-as lifecycle` | Workflow transitions, versions, components |
| `jira-as agile` | Epics, sprints, backlog management |
| `jira-as collaborate` | Comments, attachments, watchers |
| `jira-as relationships` | Issue links and dependencies |
| `jira-as time` | Time tracking and worklogs |
| `jira-as bulk` | Bulk operations |
| `jira-as dev` | Git/PR integration |
| `jira-as fields` | Custom field management |
| `jira-as ops` | Cache and operational utilities |
| `jira-as jsm` | Jira Service Management |
| `jira-as admin` | Project and permission administration |

```bash
# Get help
jira-as --help
jira-as issue --help
jira-as issue get --help
```

## Global Options

All commands support:
- `--version`: Show the version and exit
- `--output, -o`: Output format (text, json, table)
- `--verbose, -v`: Enable verbose output
- `--quiet, -q`: Suppress non-essential output
- `--help`: Show help

## Shell Completion

**Bash** (add to ~/.bashrc):
```bash
eval "$(_JIRA_AS_COMPLETE=bash_source jira-as)"
```

**Zsh** (add to ~/.zshrc):
```bash
eval "$(_JIRA_AS_COMPLETE=zsh_source jira-as)"
```

**Fish** (add to ~/.config/fish/completions/jira-as.fish):
```bash
_JIRA_AS_COMPLETE=fish_source jira-as | source
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
| `.claude-plugin/plugin.json` | `"version"` |
| `.claude-plugin/marketplace.json` | `"metadata.version"`, `"plugins[0].version"` |
| `.release-please-manifest.json` | `"."` |

## Distribution Channels

| Channel | Package | Install Command | Use Case |
|---------|---------|-----------------|----------|
| **PyPI** | `jira-as` | `pip install "jira-as>=1.1.3"` | CLI tool + shared library |
| **GitHub** | Plugin manifest | `claude plugin marketplace add https://github.com/grandcamel/jira-assistant-skills.git#main` | Claude Code plugin |

**Both must be updated when releasing:**
1. PyPI: release `jira-as` from https://github.com/grandcamel/jira-as
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
