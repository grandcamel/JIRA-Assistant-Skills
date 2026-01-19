# Container Testing

Docker-based testing infrastructure for isolated, reproducible test execution.

## Claude DevContainer Submodule

```bash
# Initialize submodule (first time)
git submodule update --init --recursive

# Update to latest
git submodule update --remote claude-devcontainer
```

Location: `skills/jira-assistant/tests/claude-devcontainer/`

Docker Hub images:
- `grandcamel/claude-devcontainer:latest` - Base image
- `grandcamel/claude-devcontainer:enhanced` - Pre-built with enhanced CLI tools

## Container Test Runners

All scripts in `skills/jira-assistant/tests/`:

| Script | Purpose |
|--------|---------|
| `run_container_tests.sh` | Standard routing test execution |
| `run_sandboxed.sh` | Restricted tool access with profiles |
| `run_workspace.sh` | Hybrid file + JIRA workflows |
| `run_devcontainer.sh` | Batteries-included dev environment |
| `run_jira_devcontainer.sh` | JIRA-specific wrapper |

Common options:
- **OAuth** (default): Uses macOS Keychain credentials
- `--api-key`: Uses `ANTHROPIC_API_KEY` environment variable
- `--api-key-from-config`: Reads from `~/.claude.json`
- `--build`: Rebuild Docker image before running
- `--model`: Select model (haiku, sonnet, opus)

## Standard Container Tests

```bash
cd skills/jira-assistant/tests

# Run all routing tests
./run_container_tests.sh

# Run with parallel workers
./run_container_tests.sh --parallel 4

# Run specific test
./run_container_tests.sh -- -k "TC001"
```

## Sandboxed Testing

Run tests with restricted tool access:

```bash
# List profiles
./run_sandboxed.sh --list-profiles

# Run in read-only mode
./run_sandboxed.sh --profile read-only

# Validate restrictions work
./run_sandboxed.sh --profile read-only --validate
```

| Profile | Use Case | Allowed Operations |
|---------|----------|-------------------|
| `read-only` | Safe demos | `jira issue get`, `jira search`, `jira fields list/get` |
| `search-only` | JQL workshops | `jira search` only |
| `issue-only` | CRUD training | All `jira issue` commands |
| `full` | Full testing | No restrictions |

## Workspace Runner

Hybrid file + JIRA workflows:

```bash
# Organize docs and close ticket
./run_workspace.sh --project ~/myproject \
  --prompt "Organize docs/ and close TES-123"

# Code review with JIRA comment
./run_workspace.sh --project ~/myproject --profile code-review \
  --prompt "Review src/auth.py and comment on TES-456"
```

| Profile | Use Case | Allowed Operations |
|---------|----------|-------------------|
| `docs-jira` | Default | File ops + `jira issue` + `jira lifecycle` |
| `code-review` | Reviews | Read files + `jira collaborate` |
| `docs-only` | File work | File operations only |
| `full-access` | Everything | No restrictions |

## Developer Container

Batteries-included development environment:

```bash
# Interactive shell
./run_devcontainer.sh

# Mount specific project
./run_devcontainer.sh --project ~/myproject

# Full setup with Docker
./run_devcontainer.sh --project ~/app --docker --port 3000:3000

# Persist caches
./run_devcontainer.sh --persist-cache
```

**Included toolchains:**

| Category | Tools |
|----------|-------|
| Languages | Python 3.11, Node.js 20, Go 1.22, Rust 1.92 |
| Cloud CLI | AWS CLI, GitHub CLI, Docker |
| CLI Tools | jq, yq, ripgrep, fd, fzf, httpie, shellcheck |
| Python | black, ruff, mypy, pytest, poetry, uv, ipython |
| Node.js | TypeScript, ESLint, Prettier, yarn, pnpm |
| Databases | PostgreSQL, MySQL, Redis, SQLite clients |

## Corporate Proxy Support (Zscaler)

```bash
docker build --build-arg EXTRA_CA_CERT=zscaler.crt -f Dockerfile .
```
