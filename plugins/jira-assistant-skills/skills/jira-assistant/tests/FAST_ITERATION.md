# Fast Iteration Workflow for Routing Tests

This document describes how to minimize the fix-test-pass/fail cycle when improving routing accuracy.

## The Problem

Full test suite takes **~22 minutes** (79 tests × ~17 seconds each). This makes iteration painfully slow when tuning skill descriptions.

## The Solution

Three optimizations reduce cycle time from 22 minutes to **1-4 minutes**:

| Optimization | Speed-Up | Trade-off |
|--------------|----------|-----------|
| Targeted tests | 10-20x | Only tests relevant skill |
| Parallel execution | 2-4x | May hit rate limits |
| Haiku model | ~2x | May behave slightly differently |

## Quick Start

```bash
cd plugins/jira-assistant-skills/skills/jira-assistant/tests

# Fast iteration on a single skill (recommended workflow)
./fast_test.sh --skill agile --fast --parallel 2

# Quick smoke test (5 representative tests)
./fast_test.sh --smoke --fast

# Test specific failing cases
./fast_test.sh --id TC012,TC015,TC020 --fast

# Re-run only previously failed tests
./fast_test.sh --failed --fast

# Full validation (before committing)
./fast_test.sh --production
```

## Recommended Workflow

### 1. Identify Failing Tests

Run the full suite once to establish baseline:

```bash
pytest test_routing.py -v 2>&1 | tee baseline.log
```

### 2. Group Failures by Skill

From the test output, identify which skills need work. Common failure patterns:

| Failure Pattern | Skill to Fix | Command |
|-----------------|--------------|---------|
| "Expected jira-agile, got jira-issue" | jira-agile | `--skill agile` |
| "Expected jira-bulk, got jira-search" | jira-bulk | `--skill bulk` |
| "Expected jira-dev, got jira-issue" | jira-dev | `--skill dev` |

### 3. Fast Iteration Loop

```bash
# 1. Edit the skill description
vim ../../jira-agile/SKILL.md

# 2. Test quickly with haiku (~2 min)
./fast_test.sh --skill agile --fast

# 3. If passing, validate with production model (~4 min)
./fast_test.sh --skill agile --production

# 4. Repeat until skill passes
```

### 4. Validate Full Suite

Before committing, run the full suite:

```bash
# Parallel for speed, production model for accuracy
./fast_test.sh --all --parallel 4

# Or sequential for maximum reliability
./fast_test.sh --production
```

## Test Subsets by Skill

| Skill | Test IDs | Estimated Time (--fast) |
|-------|----------|------------------------|
| jira-issue | TC001-TC004, TC039, TC047 | ~2 min |
| jira-search | TC005-TC008 | ~1 min |
| jira-lifecycle | TC009-TC011, TC040 | ~1 min |
| jira-agile | TC012-TC015, TC031 | ~1.5 min |
| jira-bulk | TC024-TC025, TC041, TC036 | ~1 min |
| jira-dev | TC026-TC027, TC079 | ~1 min |
| jira-relationships | TC019-TC021, TC063 | ~1 min |
| jira-time | TC022-TC023, TC075 | ~1 min |
| jira-fields | TC028, TC077 | ~30 sec |
| jira-ops | TC029, TC078 | ~30 sec |

## CLI Options

### Using pytest directly

```bash
# Target specific tests
pytest test_routing.py -v -k "TC012 or TC015"

# Use haiku model
pytest test_routing.py -v --model haiku

# Parallel execution (4 workers)
pytest test_routing.py -v -n 4

# Combine all
pytest test_routing.py -v -k "TC012" --model haiku -n 2

# Re-run failed tests only
pytest test_routing.py -v --lf
```

### Using fast_test.sh

```bash
./fast_test.sh --skill agile           # Test agile skill
./fast_test.sh --skill agile,bulk      # Test multiple skills
./fast_test.sh --id TC012,TC015        # Test specific IDs
./fast_test.sh --smoke                 # Quick 5-test smoke
./fast_test.sh --fast                  # Use haiku model
./fast_test.sh --parallel 4            # 4 parallel workers
./fast_test.sh --failed                # Re-run failures only
./fast_test.sh --production            # Full production validation
```

## Timing Estimates

| Scenario | Command | Time |
|----------|---------|------|
| Single test | `--id TC012 --fast` | ~15 sec |
| Smoke test (5) | `--smoke --fast` | ~1.5 min |
| Single skill | `--skill agile --fast` | ~2 min |
| Single skill + parallel | `--skill agile --fast --parallel 2` | ~1 min |
| All tests + haiku + parallel | `--fast --parallel 4` | ~8-10 min |
| Full production run | `--production` | ~22 min |

## Model Differences

The `--fast` flag uses Claude Haiku which is faster but may route slightly differently than the production model (Sonnet).

**Recommendation:**
- Use `--fast` during iteration for quick feedback
- Validate with `--production` before committing changes
- If a test passes with haiku but fails with production, investigate the specific case

## Parallel Execution Notes

- `--parallel 2` is safe and provides ~2x speedup
- `--parallel 4` may hit rate limits on slower connections
- If you see timeout errors, reduce parallelism or add delays
- Parallel tests may have non-deterministic output ordering

## Troubleshooting

### "ModuleNotFoundError: conftest"

Run from the tests directory:
```bash
cd plugins/jira-assistant-skills/skills/jira-assistant/tests
./fast_test.sh --smoke
```

### Rate Limit Errors (429)

Reduce parallelism:
```bash
./fast_test.sh --skill agile --fast --parallel 1
```

### Tests Pass with Haiku but Fail with Production

The models may interpret skill descriptions differently. Test with production model and adjust descriptions accordingly:
```bash
./fast_test.sh --id TC012 --production
```

## Integration with CI/CD

For pull request validation:

```yaml
# Fast check (gate merge)
- run: ./fast_test.sh --smoke --fast

# Full validation (nightly)
- run: ./fast_test.sh --production
```

## Container-Based Testing

For isolated, reproducible test environments, use the Docker-based test runner.

### Benefits

| Feature | Benefit |
|---------|---------|
| Isolation | Tests run in clean environment |
| Reproducibility | Same container = same results |
| CI/CD Ready | Easy integration with pipelines |
| Cost Options | OAuth (subscription) or API key |

### Quick Start

```bash
# Build container (first time only)
./run_container_tests.sh --build

# RECOMMENDED: Token server mode for long jobs (auto-refreshing OAuth)
./run_container_tests.sh --token-server --parallel 4

# Quick test with static OAuth token (5-min TTL)
export ANTHROPIC_AUTH_TOKEN=$(security find-generic-password -a $USER -s 'Claude Code-credentials' -w | jq -r .claudeAiOauth.accessToken)
./run_container_tests.sh

# Run with API key (uses API credits - paid)
export ANTHROPIC_API_KEY="sk-ant-..."
./run_container_tests.sh --api-key

# Run with options
./run_container_tests.sh --token-server --parallel 4 --model haiku
./run_container_tests.sh -- -k "TC001" -v  # Pass pytest args
```

### Authentication Options

| Method | Flag | Cost | TTL | Use Case |
|--------|------|------|-----|----------|
| **Token Server** | `--token-server` | Free (subscription) | Auto-refresh | Long jobs (>5 min) |
| Static OAuth | (default) | Free (subscription) | 5 minutes | Quick tests |
| API Key | `--api-key` | Pay per token | Unlimited | CI without subscription |

### Token Server Mode (Recommended for Long Jobs)

The `--token-server` flag enables automatic OAuth token refresh:

1. Starts a local HTTP server on host (port 9876)
2. Server reads fresh tokens from macOS Keychain on each request
3. Container uses `apiKeyHelper` to fetch tokens every 4 minutes
4. Automatically cleans up on exit

```bash
# Long running job with auto-refresh
./run_container_tests.sh --token-server --parallel 4

# Full test suite (20+ minutes) with auto-refresh
./run_container_tests.sh --token-server
```

**Architecture:**
```
┌──────────────────────────────────────────────────────────┐
│  macOS Host                                               │
│  ┌────────────────────────────────────────────────────┐  │
│  │  token-server.sh (Python HTTP server)               │  │
│  │  • Listens on localhost:9876                        │  │
│  │  • Reads from macOS Keychain on each request        │  │
│  │  • Returns fresh OAuth token                        │  │
│  └───────────────────────┬────────────────────────────┘  │
│                          │ http://host.docker.internal    │
│  ┌───────────────────────┴────────────────────────────┐  │
│  │  Docker Container                                   │  │
│  │  apiKeyHelper: "curl http://host.docker.internal"   │  │
│  │  TTL: 240000ms (4 min, before 5 min expiry)         │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Static OAuth Token (Quick Tests Only)

For quick tests under 5 minutes, use static token:

```bash
export ANTHROPIC_AUTH_TOKEN=$(security find-generic-password -a $USER -s 'Claude Code-credentials' -w | jq -r .claudeAiOauth.accessToken)
./run_container_tests.sh -- -k "TC001"  # Single test
```

**Warning:** Token expires after 5 minutes. Use `--token-server` for longer jobs.

### Container Options

```bash
./run_container_tests.sh [options] [-- pytest-args...]

Authentication:
  --token-server  Auto-refresh OAuth via host server (recommended for long jobs)
  --api-key       Use ANTHROPIC_API_KEY (paid)
  (default)       Use static ANTHROPIC_AUTH_TOKEN (5-min TTL)

Options:
  --build         Rebuild Docker image before running
  --parallel N    Run N tests in parallel
  --model NAME    Use specific model (sonnet, haiku, opus)
  --keep          Don't remove container after run
  --help          Show help message
```

### Environment Variables

The container automatically sets these for optimal operation:

| Variable | Value | Purpose |
|----------|-------|---------|
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | `1` | No telemetry/updates |
| `CLAUDE_CODE_ACTION` | `bypassPermissions` | Automated testing |
| `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` | `240000` | Token refresh every 4 min |
| `CHOKIDAR_USEPOLLING` | `true` | Docker file watching |

## Iterative Refinement Loop

The container setup supports a fast edit-test cycle for improving SKILL.md descriptions:

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. Host: Claude edits SKILL.md                              │
│     vim plugins/.../skills/jira-agile/SKILL.md               │
└──────────────────────────┬──────────────────────────────────┘
                           │ Volume mount
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Container: Plugin installed from mount                   │
│     claude plugins add /workspace/plugin --local             │
│     (runs automatically at container start)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Container: Tests run with updated SKILL.md               │
│     pytest test_routing.py -v -k "agile"                     │
│     (Claude reads SKILL.md fresh each invocation)            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Review results, repeat from step 1                       │
└─────────────────────────────────────────────────────────────┘
```

### Workflow Example

```bash
# Terminal 1: Edit SKILL.md
vim plugins/jira-assistant-skills/skills/jira-agile/SKILL.md

# Terminal 2: Run tests (sees changes immediately via volume mount)
./run_container_tests.sh --token-server -- -k "agile" -v

# Repeat until tests pass
```

### Why This Works

1. **Volume mount** - Plugin directory is mounted into container (`-v $PLUGIN_ROOT:/workspace/plugin`)
2. **Fresh install** - Container installs plugin from mount on each run
3. **No caching** - Claude Code reads SKILL.md content fresh each invocation
4. **Hot reload** - Changes on host are immediately visible in container

## Next Steps

See [ROUTING_ACCURACY_PROPOSAL.md](ROUTING_ACCURACY_PROPOSAL.md) for specific skill description changes to improve routing accuracy.
