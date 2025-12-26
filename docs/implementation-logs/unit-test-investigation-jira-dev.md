# Unit Test Investigation: jira-dev Skill

**Date:** 2025-12-26
**Status:** Investigation Complete
**Total Failures:** 24 (not 31 as originally reported - test session shows 24 failed, 147 passed)

## Summary

The test failures fall into two distinct categories:

1. **Return Type Mismatch (17 failures):** The `create_branch_name()` and `create_pr_description()` functions now return dictionaries instead of strings, but tests expect string return values.

2. **CLI Argument Mismatches (7 failures):** Tests expect different CLI argument names than what the implementations actually use.

---

## Category 1: Return Type Mismatch (17 failures)

### Root Cause

The `create_branch_name()` function (lines 111-193) and `create_pr_description()` function (lines 98-230) were refactored to return dictionaries containing multiple fields instead of plain strings.

**create_branch_name.py** returns:
```python
return {
    'branch_name': branch_name,
    'issue_key': issue_key,
    'issue_type': issue_type,
    'summary': summary,
    'git_command': f"git checkout -b {branch_name}"
}
```

**create_pr_description.py** returns:
```python
return {
    'markdown': markdown,
    'issue_key': issue_key,
    'issue_type': issue_type,
    'summary': summary,
    'priority': priority,
    'labels': labels,
    'components': components
}
```

### Affected Tests

#### test_git_integration.py (8 failures)
- `test_create_branch_name_basic`: Expects `result.startswith('feature/')` but result is a dict
- `test_create_branch_name_with_custom_prefix`: Expects `result.startswith('bugfix/')` but result is a dict
- `test_create_branch_name_lowercase`: Expects `result == result.lower()` but result is a dict
- `test_create_branch_name_auto_prefix_bug`: Expects `result.startswith('bugfix/')` but result is a dict
- `test_create_branch_name_auto_prefix_story`: Expects `result.startswith('feature/')` but result is a dict
- `test_create_branch_name_auto_prefix_task`: Expects `result.startswith('task/')` but result is a dict
- `test_create_branch_name_output_git_command`: Expects `branch_name in output` where branch_name is a dict

#### test_pr_management.py (6 failures)
- `test_create_pr_description_basic`: Expects `'PROJ-123' in result` but result is a dict
- `test_create_pr_description_includes_jira_link`: Expects `'PROJ-123' in result` but result is a dict
- `test_create_pr_description_includes_checklist`: Expects `'- [ ]' in result` but result is a dict
- `test_create_pr_description_markdown_format`: Expects `'## ' in result` but result is a dict
- `test_create_pr_description_with_labels`: Expects `result.lower()` but result is a dict
- `test_create_pr_description_json_output`: Calls `format_output(description, 'PROJ-123', sample_issue, output_format='json')` with wrong signature

#### test_parametrized.py (4 failures)
- `test_pr_description_sections[True-True-expected_sections0]`: Expects `result.lower()` but result is a dict
- `test_pr_description_sections[True-False-expected_sections1]`: Same issue
- `test_pr_description_sections[False-True-expected_sections2]`: Same issue
- `test_pr_description_sections[False-False-expected_sections3]`: Same issue

### Resolution

**Tests need updating** to access dictionary keys:
- For `create_branch_name()`: Use `result['branch_name']` instead of `result`
- For `create_pr_description()`: Use `result['markdown']` instead of `result`

---

## Category 2: CLI Argument Mismatches (7 failures)

### 2.1 parse_commit_issues.py - Missing main() function issue

**Test:** `test_cli_args.py::TestParseCommitIssuesCLI::test_required_message`

**Error:** Tests assume script has a `main()` function that parses CLI args, but the test doesn't actually show the function is missing - rather, the script might not require the message argument the same way.

**Resolution:** Verify the parse_commit_issues.py main() function CLI behavior.

---

### 2.2 link_commit.py - CLI Argument Naming

**Tests:**
- `test_all_required_args_present`
- `test_optional_message_and_repo`

**Test Expectation:**
```python
# Test uses positional commit_sha
['link_commit.py', 'PROJ-123', 'abc123def']
```

**Implementation Reality (link_commit.py lines 275-296):**
```python
parser.add_argument('issue_key', nargs='?', help='JIRA issue key')
parser.add_argument('--commit', '-c', required=True, help='Commit SHA')
```

**Mismatch:** Tests pass `commit_sha` as positional argument, but implementation requires `--commit` flag.

**Resolution:** Tests need updating to use `--commit abc123def` instead of positional argument.

---

### 2.3 link_pr.py - CLI Argument Naming

**Tests:**
- `test_issue_key_and_pr_url_required`
- `test_status_choices`

**Test Expectation:**
```python
['link_pr.py', 'PROJ-123', '--pr-url', 'https://github.com/org/repo/pull/456']
```

**Implementation Reality (link_pr.py lines 224-226):**
```python
parser.add_argument('--pr', '-p', required=True, help='Pull request URL')
```

**Mismatch:** Tests use `--pr-url` but implementation uses `--pr`.

**Resolution:** Tests need updating to use `--pr` instead of `--pr-url`.

---

### 2.4 create_pr_description.py - CLI Argument Naming

**Tests:**
- `test_optional_flags`
- `test_output_format_choices`

**Test Expectation:**
```python
['create_pr_description.py', 'PROJ-123', '--checklist', '--labels']
# and for output format:
['create_pr_description.py', 'PROJ-123', '--output', 'markdown']
```

**Implementation Reality (create_pr_description.py lines 267-279):**
```python
parser.add_argument('--include-checklist', '-c', action='store_true')
parser.add_argument('--include-labels', '-l', action='store_true')
parser.add_argument('--output', '-o', choices=['text', 'json'], default='text')
```

**Mismatches:**
1. Tests use `--checklist` but implementation uses `--include-checklist`
2. Tests use `--labels` but implementation uses `--include-labels`
3. Tests expect `markdown` as valid output format, but implementation only accepts `['text', 'json']`

**Resolution:** Tests need updating:
- Use `--include-checklist` and `--include-labels`
- Remove test for `markdown` output format or add it to implementation

---

## Detailed Failure List

| Test | Error Type | Needs Fix |
|------|------------|-----------|
| test_cli_args.py::TestParseCommitIssuesCLI::test_required_message | CLI behavior | Test |
| test_cli_args.py::TestLinkCommitCLI::test_all_required_args_present | `--commit` vs positional | Test |
| test_cli_args.py::TestLinkCommitCLI::test_optional_message_and_repo | `--commit` vs positional | Test |
| test_cli_args.py::TestLinkPRCLI::test_issue_key_and_pr_url_required | `--pr` vs `--pr-url` | Test |
| test_cli_args.py::TestLinkPRCLI::test_status_choices | `--pr` vs `--pr-url` | Test |
| test_cli_args.py::TestCreatePRDescriptionCLI::test_optional_flags | `--include-*` args | Test |
| test_cli_args.py::TestCreatePRDescriptionCLI::test_output_format_choices | `markdown` not valid | Test or Impl |
| test_git_integration.py (7 tests) | Dict return type | Test |
| test_pr_management.py (6 tests) | Dict return type | Test |
| test_parametrized.py (4 tests) | Dict return type | Test |

---

## Recommendations

### Priority 1: Update Tests for Dictionary Return Types (17 failures)

The implementations were intentionally changed to return richer data structures. Tests should be updated to access the appropriate dictionary keys:

```python
# Before
result = create_branch_name('PROJ-123')
assert result.startswith('feature/')

# After
result = create_branch_name('PROJ-123')
assert result['branch_name'].startswith('feature/')
```

### Priority 2: Update Tests for CLI Argument Names (7 failures)

The CLI arguments in the tests don't match the implementations. Tests should be updated:

| Script | Test Uses | Implementation Uses | Action |
|--------|-----------|---------------------|--------|
| link_commit.py | positional commit_sha | `--commit` | Update tests |
| link_pr.py | `--pr-url` | `--pr` | Update tests |
| create_pr_description.py | `--checklist` | `--include-checklist` | Update tests |
| create_pr_description.py | `--labels` | `--include-labels` | Update tests |
| create_pr_description.py | `--output markdown` | only `text`, `json` | Update tests OR add `markdown` to impl |

### No Implementation Changes Required

All failures are due to test/implementation interface mismatches. The implementations appear correct; only the tests need updating to match the actual API contracts.

---

## Test Files to Update

1. `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-dev/tests/test_cli_args.py`
2. `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-dev/tests/test_git_integration.py`
3. `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-dev/tests/test_pr_management.py`
4. `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/.claude/skills/jira-dev/tests/test_parametrized.py`
