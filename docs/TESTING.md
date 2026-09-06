# Testing

**IMPORTANT: All CI checks must pass before merging to main.**

This repository is documentation-first: the CLI's unit tests (950+) live in
the [jira-as](https://github.com/grandcamel/jira-as) library repository. The
test suites in this repo are:

| Suite | Location | Needs |
|-------|----------|-------|
| SBX profile unit tests | `skills/shared/tests/test_live_profile.py` | Offline fakes |
| Routing tests | `skills/jira-assistant/tests/` | Claude CLI (live, billed) |
| Live integration | `skills/shared/tests/live_integration/` | Host-approved dev wrapper and existing SBX project |
| Plugin E2E | `tests/e2e/` | Claude CLI credentials |

## Running Tests

```bash
# Run the per-skill unit-test loop (most skills have no unit tests here;
# suites that require live services are excluded by default)
./scripts/run_tests.sh

# Run with verbose output
./scripts/run_tests.sh --verbose

# Run tests for a specific skill only
./scripts/run_tests.sh --skill jira-assistant

# Stop on first skill failure
./scripts/run_tests.sh --fail-fast
```

## Running Single Tests

Use the single test runner for rapid iteration:

```bash
# Run all tests in a file
./scripts/run_single_test.sh jira-assistant test_sandbox_validation.py

# Run tests matching a keyword
./scripts/run_single_test.sh jira-assistant -k "sandbox"

# Re-run only failed tests from last run
./scripts/run_single_test.sh jira-assistant --lf

# Drop into debugger on failure
./scripts/run_single_test.sh jira-assistant test_sandbox_validation.py --pdb
```

## Test Organization

CLI unit tests live in the [jira-as](https://github.com/grandcamel/jira-as)
library repository, which ships the `jira-as` CLI this plugin documents.

Live integration tests remain in this repository:

```
skills/shared/tests/
└── live_integration/              # Live API tests (excluded from unit tests)
```

## Test Coverage

Coverage requirements apply to the [jira-as](https://github.com/grandcamel/jira-as)
library, where the CLI's unit tests live. For suites in this repo:

```bash
# Run tests with coverage collection
./scripts/run_tests.sh --coverage

# Generate HTML coverage report
./scripts/run_tests.sh --coverage --coverage-report html
# Open htmlcov/index.html in browser

# Generate XML coverage report (for CI)
./scripts/run_tests.sh --coverage --coverage-report xml

# Enforce minimum coverage threshold
./scripts/run_tests.sh --coverage --min-coverage 95

# Combined: coverage + HTML report + enforce 95%
./scripts/run_tests.sh --coverage --coverage-report html --min-coverage 95
```

| Format | Output | Use Case |
|--------|--------|----------|
| `term` (default) | Terminal | Quick local check |
| `html` | `htmlcov/` directory | Detailed local analysis |
| `xml` | `coverage.xml` | CI services (Codecov, Coveralls) |
| `json` | `coverage.json` | Custom tooling |

## Live Integration Testing

In this organization, **all live Jira tests run only through the host-approved
`jira-dev-host --suite` wrapper**, targeting the existing Sandbox Project
`SBX`. The shared suite defaults to the SBX profile; no extra pytest flag is
needed. An operator with host approval runs:

```bash
lane=/absolute/path/to/JIRA-Assistant-Skills
/Users/jasonkrueger/projects/grand-camel-platform/scripts/jira-dev-host "$lane" --suite \
  "$lane/.venv/bin/python" -m pytest \
  "$lane/skills/shared/tests/live_integration" -q -p no:cacheprovider
```

Use absolute paths: the wrapper supplies a private working directory and HOME.
The lane must already have its `.venv/bin/jira-as` and pytest dependencies.
The wrapper injects `JIRA_SITE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` and
`JIRA_DEFAULT_PROJECT=SBX`. The profile reads only those environment names,
never credentials or a project from settings files or the keychain. It refuses
missing credentials and any project other than exact `SBX` before constructing
a client. It never falls back to Docker and never creates a project.

The smoke tests create issues through the session fixture, helper and direct
client API. The fixture client tracks created keys and attaches a unique run
label. Session teardown attempts deletion of every tracked issue and verifies
with a final run-label search. The terminal output must include
`SBX cleanup verified:` with `remaining=0`; survivors or an unverifiable search
fail the session. Cleanup runs even after a test failure. A killed process or
machine outage cannot guarantee teardown; use the run label in the test output
to reconcile interrupted runs before acceptance.

The standalone `jira_container` API retains its legacy `JIRA_TEST_*` and Docker
behavior for compatibility. Those paths are not an approved way to run live
tests in this organization. The older `scripts/run_live_tests.sh` and examples
in other files do not replace the wrapper requirement above.

Offline profile and cleanup tests use fakes and need no Jira access:

```bash
.venv/bin/python -m pytest skills/shared/tests/test_live_profile.py -q -p no:cacheprovider
```

## Routing Tests

Validate Claude routes prompts to correct skills:

```bash
cd skills/jira-assistant/tests

# Run all routing tests
pytest test_routing.py -v

# Fast iteration with haiku model
./fast_test.sh --fast --parallel 4

# Test specific skill routing
./fast_test.sh --skill agile --fast

# Smoke test (5 key tests)
./fast_test.sh --smoke --fast
```

| Option | Description |
|--------|-------------|
| `--fast` | Use haiku model (faster, lower cost) |
| `--skill NAME` | Test specific skill(s) |
| `--id TC###` | Test specific test ID(s) |
| `--smoke` | Run 5 representative tests |
| `--parallel N` | Run N tests concurrently |
| `--failed` | Re-run only previously failed tests |

## OpenTelemetry Observability

```bash
# Simple collector
docker run -p 4318:4318 otel/opentelemetry-collector

# Full LGTM stack
cd ~/docker-otel-lgtm && docker compose up -d

# Run tests with OTel export
pytest test_routing.py --otel --otlp-endpoint http://localhost:4318 -v
```

## TDD Commit Best Practices

1. **Commit after all tests pass** - capture working code immediately
2. **Two-commit pattern per feature**:
   ```bash
   test(jira-search): add failing tests for validate command
   feat(jira-search): implement validate command (7/7 tests passing)
   ```
3. **Include test counts**: `feat(jira-agile): implement sprint create command (6/6 tests passing)`
4. **Never commit failing tests** - main branch should always have passing tests
