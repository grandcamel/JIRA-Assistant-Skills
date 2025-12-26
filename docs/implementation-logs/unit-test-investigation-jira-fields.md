# Unit Test Investigation: jira-fields Skill

**Date:** 2025-12-26
**Test File:** `.claude/skills/jira-fields/tests/test_cli_args.py`
**Total Failures:** 8 of 93 tests

## Summary

All 8 failing tests are in `test_cli_args.py` and result from **mismatches between what the tests expect and what the scripts actually implement**. The tests were written speculatively for a CLI interface that was never implemented.

**Verdict: All 8 tests need updating, not the implementations.**

---

## Failure Analysis

### 1. TestListFieldsCLI::test_type_filter

**Test expects:** `--type` option with values `custom`, `system`, `all`
**Script provides:** `--all` flag (boolean) and no `--type` option

```python
# Test (line 42-43):
for field_type in ['custom', 'system', 'all']:
    with patch('sys.argv', ['list_fields.py', '--type', field_type]):

# Script (line 103-108):
parser.add_argument('--filter', '-f', help='Filter fields by name pattern')
parser.add_argument('--agile', '-a', action='store_true', help='Show only Agile-related fields')
parser.add_argument('--all', action='store_true', help='Show all fields (not just custom)')
```

**Action needed:** Update test to use `--all` flag or remove test. The script's approach is simpler and sufficient.

---

### 2. TestListFieldsCLI::test_search_filter

**Test expects:** `--search` option
**Script provides:** `--filter` (or `-f`) option

```python
# Test (line 57):
with patch('sys.argv', ['list_fields.py', '--search', 'story']):

# Script (line 103):
parser.add_argument('--filter', '-f', help='Filter fields by name pattern')
```

**Action needed:** Update test to use `--filter` instead of `--search`.

---

### 3. TestListFieldsCLI::test_output_format

**Test expects:** `--output` with values `text`, `json`, `table`
**Script provides:** `--output` with values `text`, `json` only

```python
# Test (line 71):
for fmt in ['text', 'json', 'table']:

# Script (line 111-114):
parser.add_argument('--output', '-o',
                    choices=['text', 'json'],
                    default='text',
                    help='Output format')
```

**Action needed:** Update test to only test `text` and `json`. The `table` format is redundant since `text` already uses tabulate.

---

### 4. TestCreateFieldCLI::test_valid_field_types

**Test expects:** Positional `name` argument
**Script provides:** `--name` required option

```python
# Test (line 129):
with patch('sys.argv', ['create_field.py', 'MyField', '--type', field_type]):

# Script (line 139):
parser.add_argument('--name', '-n', required=True, help='Field name')
```

**Action needed:** Update test to use `--name MyField --type <type>` format.

---

### 5. TestCreateFieldCLI::test_optional_description

**Test expects:** Positional `name` argument
**Script provides:** `--name` required option

```python
# Test (line 143-147):
with patch('sys.argv', [
    'create_field.py', 'MyField',
    '--type', 'text',
    '--description', 'A custom field for testing'
]):

# Script (line 139):
parser.add_argument('--name', '-n', required=True, help='Field name')
```

**Action needed:** Update test to use `--name MyField` instead of positional `MyField`.

---

### 6. TestConfigureAgileFieldsCLI::test_valid_project

**Test expects:** `--project` option
**Script provides:** Positional `project` argument

```python
# Test (line 177):
with patch('sys.argv', ['configure_agile_fields.py', '--project', 'PROJ']):

# Script (line 241-242):
parser.add_argument('project', help='Project key')
```

**Action needed:** Update test to use positional `PROJ` instead of `--project PROJ`.

---

### 7. TestConfigureAgileFieldsCLI::test_discover_flag

**Test expects:** `--project` option and `--discover` flag
**Script provides:** Positional `project` argument, no `--discover` flag

```python
# Test (line 191):
with patch('sys.argv', ['configure_agile_fields.py', '--project', 'PROJ', '--discover']):

# Script (line 241-256):
parser.add_argument('project', help='Project key')
# No --discover flag exists - discovery is automatic
```

**Action needed:** Update test to use positional `PROJ` and remove `--discover` (discovery is automatic in the script).

---

### 8. TestConfigureAgileFieldsCLI::test_profile_option

**Test expects:** `--project` option
**Script provides:** Positional `project` argument

```python
# Test (line 205-209):
with patch('sys.argv', [
    'configure_agile_fields.py',
    '--project', 'PROJ',
    '--profile', 'development'
]):

# Script (line 241-242):
parser.add_argument('project', help='Project key')
```

**Action needed:** Update test to use positional `PROJ` instead of `--project PROJ`.

---

## Recommended Test Updates

| Test | Current CLI | Correct CLI |
|------|-------------|-------------|
| `test_type_filter` | `--type custom` | `--all` (boolean flag) |
| `test_search_filter` | `--search story` | `--filter story` |
| `test_output_format` | `text, json, table` | `text, json` only |
| `test_valid_field_types` | `MyField --type text` | `--name MyField --type text` |
| `test_optional_description` | `MyField --type text` | `--name MyField --type text` |
| `test_valid_project` | `--project PROJ` | `PROJ` (positional) |
| `test_discover_flag` | `--project PROJ --discover` | `PROJ` (no `--discover`) |
| `test_profile_option` | `--project PROJ --profile dev` | `PROJ --profile dev` |

---

## Implementation Notes

The script implementations follow consistent patterns with other skills in the project:

1. **list_fields.py**: Uses `--filter` for search, `--all` flag for field type selection
2. **create_field.py**: Uses `--name` and `--type` as named required arguments (consistent with other create scripts)
3. **configure_agile_fields.py**: Uses positional project argument (consistent with other project-focused scripts), auto-discovers Agile fields

The tests were written speculatively before the implementations were finalized and need to be updated to match the actual CLI interfaces.
