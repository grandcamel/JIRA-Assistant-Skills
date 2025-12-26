# Fix jira-fields Unit Test Failures

**Date:** 2025-12-26
**File Modified:** `.claude/skills/jira-fields/tests/test_cli_args.py`
**Failures Fixed:** 8 of 8
**Final Result:** 93/93 tests passing

## Summary

Fixed 8 failing unit tests in `test_cli_args.py` by aligning test expectations with the actual CLI implementations of the scripts.

## Changes Made

| Test | Original (Incorrect) | Fixed (Correct) |
|------|---------------------|-----------------|
| `test_type_filter` | `--type custom/system/all` | `--all` (boolean flag) |
| `test_search_filter` | `--search story` | `--filter story` |
| `test_output_format` | `['text', 'json', 'table']` | `['text', 'json']` |
| `test_valid_field_types` | `MyField --type text` (positional) | `--name MyField --type text` |
| `test_optional_description` | `MyField --type text` (positional) | `--name MyField --type text` |
| `test_valid_project` | `--project PROJ` | `PROJ` (positional) |
| `test_discover_flag` | `--project PROJ --discover` | `PROJ` (auto-discovery) |
| `test_profile_option` | `--project PROJ --profile dev` | `PROJ --profile dev` |

## Detailed Changes

### 1. TestListFieldsCLI::test_type_filter (lines 38-51)
- Changed from testing `--type` option with multiple values to testing `--all` flag
- The script uses a simple boolean flag `--all` to show all fields (not just custom)

### 2. TestListFieldsCLI::test_search_filter (lines 53-65)
- Changed `--search` to `--filter` to match the actual script argument
- Updated docstring to reflect the change

### 3. TestListFieldsCLI::test_output_format (lines 67-80)
- Removed `'table'` from the format list, keeping only `['text', 'json']`
- The script only supports these two output formats

### 4. TestCreateFieldCLI::test_valid_field_types (lines 122-137)
- Changed from positional `MyField` to `--name MyField`
- The create_field.py script uses `--name` as a required option

### 5. TestCreateFieldCLI::test_optional_description (lines 139-155)
- Changed from positional `MyField` to `--name MyField`
- Same correction as test_valid_field_types

### 6. TestConfigureAgileFieldsCLI::test_valid_project (lines 173-185)
- Changed from `--project PROJ` to positional `PROJ`
- Updated docstring to reflect the positional argument

### 7. TestConfigureAgileFieldsCLI::test_discover_flag (lines 187-200)
- Removed `--discover` flag (discovery is automatic in the script)
- Changed `--project PROJ` to positional `PROJ`
- Updated docstring to explain auto-discovery behavior

### 8. TestConfigureAgileFieldsCLI::test_profile_option (lines 202-218)
- Changed `--project PROJ` to positional `PROJ`
- Updated docstring to reflect the change

## Test Execution

```bash
cd .claude/skills/jira-fields/tests && pytest . -v --ignore=live_integration -p no:cacheprovider
```

**Result:** 93 passed in 0.47s

## Root Cause

The tests were written speculatively before the script implementations were finalized. The actual CLI interfaces evolved differently than what the tests expected, resulting in argument parsing failures (exit code 2).
