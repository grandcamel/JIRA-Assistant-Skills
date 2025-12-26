# Unit Test Investigation: jira-relationships Skill

## Summary

8 unit test failures were identified in the jira-relationships skill. All failures stem from **CLI interface mismatches** between the test expectations and the actual script implementations. The tests were written for an older CLI interface that has since been updated to use semantic link flags.

## Test Run Results

Command: `pytest . -v --ignore=live_integration -p no:cacheprovider`
- Total tests: 111
- Passed: 103
- Failed: 8

---

## Failure Analysis

### Category 1: link_issue.py CLI Mismatch (4 failures)

| Test | File | Location |
|------|------|----------|
| `test_required_args` | test_cli_args.py:24 | TestLinkIssueCLI |
| `test_valid_positional_args` | test_cli_args.py:40 | TestLinkIssueCLI |
| `test_type_option` | test_cli_args.py:54 | TestLinkIssueCLI |
| `test_profile_option` | test_cli_args.py:69 | TestLinkIssueCLI |

#### Root Cause

Tests expect **two positional arguments** (`inward_key`, `outward_key`) plus a `--type` option:
```bash
# Test expectation
link_issue.py PROJ-123 PROJ-456 --type Blocks
```

Actual implementation uses **one positional argument** plus **semantic link flags**:
```bash
# Actual implementation
link_issue.py PROJ-123 --blocks PROJ-456
link_issue.py PROJ-123 --type Blocks --to PROJ-456
```

#### Implementation Details

**Test code (test_cli_args.py:44-52)**:
```python
with patch('sys.argv', ['link_issue.py', 'PROJ-123', 'PROJ-456']):
    # Expects two positional args
```

**Actual script (link_issue.py:184-221)**:
```python
parser.add_argument('issue_key',
                   help='Source issue key (e.g., PROJ-123)')
# No second positional argument!
link_group.add_argument('--blocks', metavar='ISSUE', ...)
link_group.add_argument('--type', '-t', dest='link_type', ...)
link_group.add_argument('--to', dest='target_issue', ...)
```

#### Error Messages

- `test_required_args`: Expected exit code 2 but got 1 (script errors due to missing link type, not argparse)
- `test_valid_positional_args`: argparse rejects second positional arg as "unrecognized arguments: PROJ-456"
- `test_type_option`: Same issue - PROJ-456 is unrecognized
- `test_profile_option`: Same issue - PROJ-456 is unrecognized

---

### Category 2: bulk_link.py CLI Mismatch (3 failures)

| Test | File | Location |
|------|------|----------|
| `test_valid_input` | test_cli_args.py:122 | TestBulkLinkCLI |
| `test_skip_existing_option` | test_cli_args.py:141 | TestBulkLinkCLI |
| `test_jql_input` | test_cli_args.py:161 | TestBulkLinkCLI |

#### Root Cause

Tests use `--target` argument which does **not exist** in the implementation. The implementation uses semantic flags like `--blocks TARGET` or `--type X --to TARGET`.

#### Test Expectations vs Implementation

**Test code (test_cli_args.py:126-131)**:
```python
with patch('sys.argv', [
    'bulk_link.py',
    '--issues', 'PROJ-1,PROJ-2',
    '--target', 'PROJ-100',    # <-- Does not exist!
    '--type', 'Blocks',
    '--dry-run'
]):
```

**Actual implementation (bulk_link.py:186-208)**:
```python
# No --target argument defined!
link_group.add_argument('--blocks', metavar='TARGET', ...)
link_group.add_argument('--relates-to', metavar='TARGET', ...)
link_group.add_argument('--type', dest='link_type', ...)
link_group.add_argument('--to', metavar='TARGET', ...)
```

#### Correct Usage

```bash
# Using semantic flags
bulk_link.py --issues PROJ-1,PROJ-2 --blocks PROJ-100 --dry-run

# Using explicit type
bulk_link.py --issues PROJ-1,PROJ-2 --type Blocks --to PROJ-100 --dry-run
```

---

### Category 3: bulk_link Function Signature Mismatch (1 failure)

| Test | File | Location |
|------|------|----------|
| `test_concurrent_bulk_link_operations` | test_concurrent_operations.py:71 | TestConcurrentLinkCreation |

#### Root Cause

Test passes an **invalid issue key format** as the target parameter.

**Test code (test_concurrent_operations.py:91-93)**:
```python
for i in range(3):
    issues = [f'PROJ-{i*10 + j}' for j in range(5)]
    future = executor.submit(run_bulk_link, issues, f'PROJ-TARGET-{i}')
```

The target value `PROJ-TARGET-0` fails validation because it contains two hyphens and doesn't match the issue key pattern `^[A-Z][A-Z0-9]*-[0-9]+$`.

#### Error Message

```
ValidationError: Invalid issue key format: 'PROJ-TARGET-2'.
Expected format: PROJECT-123 (e.g., PROJ-42, DEV-1234)
```

---

## Recommendations

### Tests to Update (7 tests)

All 7 failures in `test_cli_args.py` require test updates to match the current implementation:

1. **TestLinkIssueCLI.test_required_args**: Change to test missing semantic flag error
2. **TestLinkIssueCLI.test_valid_positional_args**: Use `['link_issue.py', 'PROJ-123', '--blocks', 'PROJ-456']`
3. **TestLinkIssueCLI.test_type_option**: Use `['link_issue.py', 'PROJ-123', '--type', link_type, '--to', 'PROJ-456']`
4. **TestLinkIssueCLI.test_profile_option**: Add semantic flag: `['link_issue.py', 'PROJ-123', '--blocks', 'PROJ-456', '--profile', 'development']`
5. **TestBulkLinkCLI.test_valid_input**: Replace `--target PROJ-100 --type Blocks` with `--blocks PROJ-100`
6. **TestBulkLinkCLI.test_skip_existing_option**: Same fix as above
7. **TestBulkLinkCLI.test_jql_input**: Replace `--target PROJ-100 --type Relates` with `--relates-to PROJ-100`

### Tests to Fix (1 test)

1. **TestConcurrentLinkCreation.test_concurrent_bulk_link_operations**: Change target from `f'PROJ-TARGET-{i}'` to valid issue key format like `f'PROJ-{100+i}'`

### Implementation Status

No changes needed to script implementations. Both `link_issue.py` and `bulk_link.py` are correctly implemented with the new semantic link flag interface:
- `--blocks ISSUE`
- `--relates-to ISSUE`
- `--duplicates ISSUE`
- `--clones ISSUE`
- `--is-blocked-by ISSUE`
- `--type NAME --to ISSUE`

---

## Corrected Test Code

### link_issue.py Tests

```python
class TestLinkIssueCLI:
    def test_required_args(self):
        """Test that issue_key and a link type are required."""
        import link_issue

        # Missing all required args
        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.argv', ['link_issue.py']):
                link_issue.main()
        assert exc_info.value.code == 2

        # Missing link type
        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.argv', ['link_issue.py', 'PROJ-123']):
                link_issue.main()
        assert exc_info.value.code == 1  # ValidationError, not argparse error

    def test_valid_positional_args(self):
        """Test valid positional argument with semantic flag."""
        import link_issue

        with patch('sys.argv', ['link_issue.py', 'PROJ-123', '--blocks', 'PROJ-456']):
            with patch.object(link_issue, 'get_jira_client') as mock_client:
                mock_client.return_value.get_link_types.return_value = [{'name': 'Blocks', 'outward': 'blocks'}]
                mock_client.return_value.create_link = Mock()
                mock_client.return_value.close = Mock()
                try:
                    link_issue.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("Valid args should be accepted")

    def test_type_option(self):
        """Test --type option with --to."""
        import link_issue

        for link_type in ['Blocks', 'Relates', 'Cloners', 'Duplicate']:
            with patch('sys.argv', ['link_issue.py', 'PROJ-123', '--type', link_type, '--to', 'PROJ-456']):
                with patch.object(link_issue, 'get_jira_client') as mock_client:
                    mock_client.return_value.get_link_types.return_value = [{'name': link_type}]
                    mock_client.return_value.create_link = Mock()
                    mock_client.return_value.close = Mock()
                    try:
                        link_issue.main()
                    except SystemExit as e:
                        if e.code == 2:
                            pytest.fail(f"--type {link_type} --to should be valid")

    def test_profile_option(self):
        """Test --profile option."""
        import link_issue

        with patch('sys.argv', [
            'link_issue.py', 'PROJ-123', '--blocks', 'PROJ-456',
            '--profile', 'development'
        ]):
            with patch.object(link_issue, 'get_jira_client') as mock_client:
                mock_client.return_value.get_link_types.return_value = [{'name': 'Blocks', 'outward': 'blocks'}]
                mock_client.return_value.create_link = Mock()
                mock_client.return_value.close = Mock()
                try:
                    link_issue.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("--profile should be valid")
```

### bulk_link.py Tests

```python
class TestBulkLinkCLI:
    def test_valid_input(self):
        """Test valid input combination."""
        import bulk_link

        with patch('sys.argv', [
            'bulk_link.py',
            '--issues', 'PROJ-1,PROJ-2',
            '--blocks', 'PROJ-100',
            '--dry-run'
        ]):
            with patch.object(bulk_link, 'get_jira_client') as mock_client:
                mock_client.return_value.close = Mock()
                try:
                    bulk_link.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("Valid input should be accepted")

    def test_skip_existing_option(self):
        """Test --skip-existing option."""
        import bulk_link

        with patch('sys.argv', [
            'bulk_link.py',
            '--issues', 'PROJ-1',
            '--blocks', 'PROJ-100',
            '--skip-existing',
            '--dry-run'
        ]):
            with patch.object(bulk_link, 'get_jira_client') as mock_client:
                mock_client.return_value.close = Mock()
                try:
                    bulk_link.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("--skip-existing should be valid")

    def test_jql_input(self):
        """Test --jql input."""
        import bulk_link

        with patch('sys.argv', [
            'bulk_link.py',
            '--jql', 'project = PROJ AND fixVersion = 1.0',
            '--relates-to', 'PROJ-100',
            '--dry-run'
        ]):
            with patch.object(bulk_link, 'get_jira_client') as mock_client:
                mock_client.return_value.search_issues.return_value = {'issues': [], 'total': 0}
                mock_client.return_value.close = Mock()
                try:
                    bulk_link.main()
                except SystemExit as e:
                    if e.code == 2:
                        pytest.fail("--jql should be valid")
```

### Concurrent Operations Test

```python
def test_concurrent_bulk_link_operations(self, mock_jira_client):
    """Test bulk_link with concurrent operations."""
    import bulk_link

    mock_jira_client.create_link.return_value = None

    with patch.object(bulk_link, 'get_jira_client', return_value=mock_jira_client):
        results = []

        def run_bulk_link(issues, target):
            result = bulk_link.bulk_link(
                issues=issues,
                target=target,
                link_type='Blocks'
            )
            return result

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for i in range(3):
                issues = [f'PROJ-{i*10 + j}' for j in range(5)]
                # Use valid issue key format: PROJ-100, PROJ-101, PROJ-102
                future = executor.submit(run_bulk_link, issues, f'PROJ-{100+i}')
                futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        assert len(results) == 3
        for result in results:
            assert result['failed'] == 0
```

---

## Investigation Date

2025-12-26

## Conclusion

All 8 test failures are due to **test code that does not match the current CLI interface**. The implementations are correct; only the tests need updating. No implementation changes are required.
