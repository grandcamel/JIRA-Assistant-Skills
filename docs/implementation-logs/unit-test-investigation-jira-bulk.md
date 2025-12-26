# Unit Test Investigation: jira-bulk Skill

**Date:** 2025-12-26
**Investigator:** Claude Agent (Testing and QA Specialist)

## Summary

Two unit test failures were identified in the jira-bulk skill:
1. `test_bulk_clone.py::TestBulkCloneApiErrors::test_not_found_error`
2. `test_cli_args.py::TestBulkCloneCLI::test_clone_options`

**Conclusion:** Both failures are due to **test expectations being wrong** - the tests do not match the actual implementation.

---

## Failure 1: test_not_found_error

### Test Location
`/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-bulk/tests/test_bulk_clone.py:358`

### Test Expectation
The test expects that when a 404 error occurs during issue fetch, a `JiraError` exception should be raised:

```python
def test_not_found_error(self, mock_jira_client):
    """Test handling of 404 not found error during issue fetch."""
    # 404 during initial issue fetch propagates as exception
    mock_jira_client.get_issue.side_effect = JiraError(
        "Issue not found", status_code=404
    )

    # The script raises the error when issue cannot be fetched
    with pytest.raises(JiraError) as exc_info:
        bulk_clone(
            client=mock_jira_client,
            issue_keys=['PROJ-999'],
            dry_run=False
        )
```

### Actual Implementation Behavior
The implementation (`bulk_clone.py:277-285`) catches the JiraError and continues gracefully:

```python
for key in issue_keys:
    try:
        issue = client.get_issue(key)
        issues.append(issue)
    except JiraError as e:
        sanitized_msg = sanitize_error_message(str(e))
        retrieval_errors[key] = sanitized_msg
        print_warning(f"Could not retrieve {key}: {sanitized_msg}")
```

This is by design - bulk operations are intended to be resilient and continue processing even if some issues fail. The function returns a result dict with `retrieval_failed` count and `errors` dictionary rather than raising an exception.

### Verdict: **Test Expectation is Wrong**

The test docstring says "404 during initial issue fetch propagates as exception" but the implementation intentionally handles errors gracefully for bulk operations. The test should be updated to match the actual (correct) behavior:

```python
def test_not_found_error(self, mock_jira_client):
    """Test handling of 404 not found error during issue fetch."""
    mock_jira_client.get_issue.side_effect = JiraError(
        "Issue not found", status_code=404
    )

    result = bulk_clone(
        client=mock_jira_client,
        issue_keys=['PROJ-999'],
        dry_run=False
    )

    # Should handle gracefully, not raise
    assert result['success'] == 0
    assert result['retrieval_failed'] == 1
    assert 'PROJ-999' in result.get('errors', {})
```

---

## Failure 2: test_clone_options

### Test Location
`/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-bulk/tests/test_cli_args.py:335`

### Test Expectation
The test expects CLI arguments `--clone-subtasks` and `--clone-links`:

```python
def test_clone_options(self):
    """Test --clone-subtasks and --clone-links options."""
    with patch('sys.argv', [
        'bulk_clone.py',
        '--issues', 'PROJ-1',
        '--clone-subtasks',
        '--clone-links',
        '--dry-run'
    ]):
```

### Actual Implementation
The implementation (`bulk_clone.py:436-441`) defines the arguments as `--include-subtasks` and `--include-links`:

```python
parser.add_argument('--include-subtasks', '-s',
                    action='store_true',
                    help='Clone subtasks')
parser.add_argument('--include-links', '-l',
                    action='store_true',
                    help='Recreate issue links')
```

### Error Message
```
bulk_clone.py: error: unrecognized arguments: --clone-subtasks --clone-links
```

### Verdict: **Test Expectation is Wrong**

The test uses incorrect CLI argument names. The test should be updated to use the actual argument names:

```python
def test_clone_options(self):
    """Test --include-subtasks and --include-links options."""
    with patch('sys.argv', [
        'bulk_clone.py',
        '--issues', 'PROJ-1',
        '--include-subtasks',
        '--include-links',
        '--dry-run'
    ]):
```

---

## Recommendations

1. **Fix test_not_found_error**: Update to expect graceful handling (result dict with errors) instead of exception propagation.

2. **Fix test_clone_options**: Change `--clone-subtasks` to `--include-subtasks` and `--clone-links` to `--include-links`.

3. **Note on design decision**: The graceful error handling in bulk operations is the correct design pattern. Bulk operations should continue processing remaining items when individual items fail, collecting errors for reporting rather than failing the entire batch.

---

## Files Involved

| File | Role |
|------|------|
| `.claude/skills/jira-bulk/scripts/bulk_clone.py` | Implementation (correct) |
| `.claude/skills/jira-bulk/tests/test_bulk_clone.py` | Test with wrong expectation |
| `.claude/skills/jira-bulk/tests/test_cli_args.py` | Test with wrong CLI arg names |
