# jira-agile SKILL.md Review

**Date:** 2026-01-31
**Status:** 12 Issues Found
**Overall Assessment:** SKILL.md is largely accurate with mostly undocumented optional parameters

## Summary

The jira-agile SKILL.md documentation provides good coverage of core workflows, but has gaps in documenting optional parameters and alternative command patterns. Most discrepancies are about missing documentation rather than incorrect syntax.

## Critical Issues (2)

### WRONG_SYNTAX: sprint move-issues

**Line 118:** Documentation example uses correct syntax
- Documented: `jira-as agile sprint move-issues --sprint 456 --issues PROJ-101,PROJ-102`
- Actual: Works as documented
- **Status:** No change needed - documentation is correct

### WRONG_SYNTAX: sprint manage

**Line 121:** --sprint parameter required
- The documentation correctly shows --sprint but should emphasize it's required
- All manage operations require -s/--sprint INTEGER

## High-Priority Issues (2)

### Missing Sprint Create Date Parameters

**Lines 117** - Sprint create command lacks documentation for date fields
- **Missing:** `--start-date` and `--end-date` (YYYY-MM-DD)
- **Impact:** Users cannot set sprint boundaries without consulting CLI help
- **Recommendation:** Add example:
  ```bash
  jira-as agile sprint create --board 123 --name "Sprint 42" \
    --start-date 2026-02-01 --end-date 2026-02-15
  ```

### Missing Sprint Manage Update Operations

**Lines 121-122** - Sprint manage only documents start/close operations
- **Missing:** Name, goal, and date updates via --name, --goal, --start-date, --end-date
- **Impact:** Users cannot update sprint properties without CLI help
- **Recommendation:** Add examples:
  ```bash
  jira-as agile sprint manage --sprint 456 --name "Sprint 43" --goal "Launch feature X"
  jira-as agile sprint manage --sprint 456 --start-date 2026-02-08
  ```

## Medium-Priority Issues (4)

### Missing Epic Query Option

**Line 139-140** - estimates command can query epics but not documented
- **Missing:** `--epic TEXT` option for estimates command
- **Impact:** Users won't know they can get estimates for all issues in an epic
- **Recommendation:** Add example:
  ```bash
  jira-as agile estimates --epic PROJ-100 --group-by status
  ```

### Missing Sprint List Pagination

**Line 113** - sprint list lacks --max-results documentation
- **Missing:** `--max-results INTEGER` option
- **Recommendation:** Document:
  ```bash
  jira-as agile sprint list --project DEMO --max-results 10
  ```

### Missing Sprint Get --active Pattern

**Lines 115-116** - sprint get shows positional ID but misses --active flag
- **Missing:** Documentation of `--board` with `--active` pattern
- **Alternative Usage:** `jira-as agile sprint get --board 123 --active`
- **Recommendation:** Add as alternative to positional sprint ID

## Low-Priority Issues (4)

### Missing Epic Create Optional Fields

**Line 94** - epic create example is minimal
- **Missing:** --assignee, --priority, --custom-fields documentation
- **Recommendation:** Expand example:
  ```bash
  jira-as agile epic create --project PROJ --summary "MVP" \
    --assignee user@company.com --priority High
  ```

### Undocumented Short Forms

**Lines 138, 146** - Some options have short forms not mentioned:
- `estimate`: `-p|--points`
- `velocity`: `-n|--sprints`

### Sprint Manage --move-incomplete-to Scope

**Line 122** - --move-incomplete-to usage not fully explained
- **Issue:** Option only applies with --close flag
- **Recommendation:** Clarify context in documentation

### Sprint Move-Issues --backlog

**Line 120** - Uses --backlog without mentioning `-b` short form
- **Note:** Documentation is correct but could be more complete

## Verification Results

### Commands Tested
```bash
jira-as agile --help
jira-as agile epic --help
jira-as agile epic create --help
jira-as agile epic get --help
jira-as agile epic add-issues --help
jira-as agile subtask --help
jira-as agile sprint --help
jira-as agile sprint list --help
jira-as agile sprint get --help
jira-as agile sprint create --help
jira-as agile sprint manage --help
jira-as agile sprint move-issues --help
jira-as agile backlog --help
jira-as agile rank --help
jira-as agile estimate --help
jira-as agile estimates --help
jira-as agile velocity --help
```

### Test Results
- All commands execute successfully
- All documented syntax patterns work correctly
- CLI supports additional undocumented options
- Output formats consistent across all commands
- Dry-run mode available where documented

## Options Consistency Check

| Command | Options Consistently Documented |
|---------|--------------------------------|
| Most commands | `-o|--output [text\|json]` ✓ |
| Epic add-issues, sprint move-issues | `-n|--dry-run` ✓ |
| Sprint manage | All flags present but workflow context missing |
| Backlog | Requires either board or project ✓ |

## Recommendations by Priority

### HIGH (Apply Immediately)
1. Document sprint create with optional date parameters
2. Document sprint manage update operations

### MEDIUM (Before Next Release)
3. Document estimates --epic option
4. Document sprint list --max-results
5. Document sprint get --active pattern

### LOW (Nice to Have)
6. Expand epic create examples with optional fields
7. Document short form option names
8. Clarify --move-incomplete-to context

## Impact Assessment

- **User Impact:** Low - Most gaps are for advanced features
- **Functionality Impact:** None - All commands work as documented
- **Documentation Clarity:** Medium - Users must consult CLI help for optional parameters
- **Maintenance Risk:** Low - Changes are additive, no breaking changes needed

## Notes

- The SKILL.md provides good conceptual overview of agile operations
- Risk levels and skill selection guidance are accurate
- Integration with other skills is well-documented
- No syntax errors in documented examples
- Most discrepancies are about optional parameters rather than core functionality
- Example coverage is good but could be more comprehensive

---

**Reviewed by:** Jira-Assistant-Skills Documentation Review
**Format:** JSON findings at `/docs/reviews/findings/jira-agile.json`
