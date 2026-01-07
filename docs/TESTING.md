# Testing

**IMPORTANT: All unit tests must pass before merging to main.** Enforced by CI.

## Running All Unit Tests

```bash
# Run all unit tests (required before merge)
./scripts/run_tests.sh

# Run with verbose output
./scripts/run_tests.sh --verbose

# Run tests for a specific skill only
./scripts/run_tests.sh --skill jira-bulk

# Stop on first skill failure
./scripts/run_tests.sh --fail-fast
```

## Running Single Tests

Use the single test runner for rapid iteration:

```bash
# Run all tests in a file
./scripts/run_single_test.sh jira-bulk test_bulk_assign.py

# Run a specific test class
./scripts/run_single_test.sh jira-bulk test_bulk_assign.py::TestBulkAssignToUser

# Run a specific test method
./scripts/run_single_test.sh jira-bulk test_bulk_assign.py::TestBulkAssignToUser::test_bulk_assign_to_user_by_account_id

# Run tests matching a keyword
./scripts/run_single_test.sh jira-search -k "validate"

# Run with verbose output and full traceback
./scripts/run_single_test.sh jira-admin test_list_projects.py -v --tb=long

# Re-run only failed tests from last run
./scripts/run_single_test.sh jira-admin --lf

# Drop into debugger on failure
./scripts/run_single_test.sh jira-bulk test_bulk_assign.py --pdb
```

## Test Organization

```
plugins/jira-assistant-skills/skills/<skill>/tests/
├── conftest.py           # Skill-specific fixtures
├── fixtures/             # Test data and mock responses
├── test_*.py             # Unit tests
├── unit/                 # Additional unit test modules (optional)
└── live_integration/     # Live API tests (excluded from unit tests)
```

## Test Coverage

**Requirement: 95% test coverage is required for all PRs.**

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

Tests against real JIRA instances:

```bash
# Core skills
pytest plugins/jira-assistant-skills/skills/shared/tests/live_integration/ --profile development -v

# JSM skills
pytest plugins/jira-assistant-skills/skills/jira-jsm/tests/live_integration/ --profile development --skip-premium -v

# Specific modules
pytest plugins/jira-assistant-skills/skills/shared/tests/live_integration/test_issue_lifecycle.py -v
```

**Profile requirement**: Live tests require `--profile development`.

**JSM test options**:
- `--skip-premium`: Skip tests requiring JSM Premium license
- `--service-desk-id N`: Use existing service desk
- `--keep-project`: Keep test service desk after tests

## Routing Tests

Validate Claude routes prompts to correct skills:

```bash
cd plugins/jira-assistant-skills/skills/jira-assistant/tests

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
   test(jira-search): add failing tests for jql_validate
   feat(jira-search): implement jql_validate.py (7/7 tests passing)
   ```
3. **Include test counts**: `feat(jira-agile): implement create_sprint.py (6/6 tests passing)`
4. **Never commit failing tests** - main branch should always have passing tests
