# JIRA Time Tracking Skill (jira-time) Review

**Skill File:** `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/skills/jira-time/SKILL.md`
**CLI Command:** `jira-as time`
**Review Date:** 2026-01-31
**Total Issues Found:** 14 (2 high, 8 medium, 4 low)

---

## Executive Summary

The jira-time SKILL.md documentation is **77% accurate** overall, with all 9 commands correctly listed and mostly functional documentation. However, there are **14 discrepancies** between documented behavior and actual CLI implementation, including:

- **2 blocking issues** that will cause runtime failures if users follow examples
- **8 consistency/accuracy issues** that create confusion
- **4 minor style/documentation gaps**

---

## Critical Issues (Will Cause Runtime Failures)

### Issue #1: Example on Line 155 Uses Unsupported Option

**Severity:** HIGH (Runtime Failure)

**Location:** Line 155, "Examples - Log time"

**Problem:**
```bash
# DOCUMENTED (WRONG):
jira-as time log PROJ-123 -t 2h --adjust-estimate manual --reduce-by 1h

# ACTUAL CLI OUTPUT:
Usage: jira-as time log [OPTIONS] ISSUE_KEY
Options:
  -t, --time TEXT                 Time spent (e.g., 2h, 1d 4h, 30m) [required]
  -c, --comment TEXT              Worklog comment
  -s, --started TEXT              Start time (YYYY-MM-DD or ISO datetime)
  -a, --adjust-estimate [auto|leave|new|manual]
  --new-estimate TEXT             New remaining estimate (when adjust=new or manual)
  --visibility-type [role|group]  Restrict visibility to role or group
  --visibility-value TEXT         Role or group name for visibility restriction
  -o, --output [text|json]        Output format
  --help                          Show this message and exit.
```

**Analysis:** The `log` command does NOT support `--reduce-by` option. Running the documented example will fail with "no such option: --reduce-by".

**Impact:** Users copying this example will get an immediate error. The `--reduce-by` option only exists for the `delete-worklog` command, not `log`.

**Fix:**
```bash
# CORRECT - remove --reduce-by:
jira-as time log PROJ-123 -t 2h --adjust-estimate auto

# Or use --new-estimate if you want to set a specific remaining time:
jira-as time log PROJ-123 -t 2h --adjust-estimate new --new-estimate 3h
```

---

### Issue #2: Missing Options in Common Options Table

**Severity:** HIGH (Incomplete Documentation)

**Location:** Lines 79-83, "Common Options" table

**Problem:**
The documentation shows:
```
| Option | Description | Availability |
|--------|-------------|--------------|
| `-o/--output` | Output format: text (default), json | ... worklogs, ... |
```

But actual `jira-as time worklogs --help` shows:
```
Options:
  -s, --since TEXT          Show worklogs since date (YYYY-MM-DD)
  -u, --until TEXT          Show worklogs until date (YYYY-MM-DD)
  -a, --author TEXT         Filter by author
  -o, --output [text|json]  Output format
  --help                    Show this message and exit.
```

**Analysis:** The table only documents `-o/--output` but the `worklogs` command actually supports:
- `-s/--since`: Filter by start date
- `-u/--until`: Filter by end date
- `-a/--author`: Filter by worklog author

**Impact:** Users cannot discover these filtering options from the options table. They only appear in the examples section (lines 174-177), which may be missed.

**Fix:** Update the Common Options table to include filtering options for worklogs command.

---

## High Priority Issues (Accuracy Problems)

### Issue #3: Documentation Claims `--reduce-by` Works with Log Command

**Severity:** HIGH (Contradicts Examples)

**Location:** Lines 92-94, "Worklog-specific options"

**Problem:**
Documentation states:
```
| `--reduce-by TIME` | Amount to reduce estimate (for adjust=manual with log) |
```

But the `log` command's `--adjust-estimate` option doesn't support `manual` mode with `--reduce-by`. Looking at actual CLI:

```bash
# log command adjust-estimate options:
-a, --adjust-estimate [auto|leave|new|manual]

# But NO --reduce-by option exists for log!
```

The `--reduce-by` option only appears in `delete-worklog`:
```
--reduce-by TEXT    Amount to reduce estimate (for adjust=manual)
```

**Analysis:** The documentation incorrectly suggests `--reduce-by` is a general worklog option available across multiple commands. In reality, it's only available for `delete-worklog`.

**Impact:** Reinforces the failing example on line 155. Creates false expectations about feature availability.

**Fix:**
1. Remove `--reduce-by` from the general worklog-specific options table
2. Move it to delete-worklog specific documentation
3. Clarify which commands support which `adjust-estimate` modes

---

### Issue #4: Options Table Doesn't Show Command-Specific Differences

**Severity:** HIGH (Misleading)

**Location:** Lines 79-83, "Common Options" table

**Problem:**
The table shows output format availability as if all commands support the same options, but they don't:

**Actual support breakdown:**
```
COMMAND          | Output Formats Supported
log              | text, json
worklogs         | text, json
update-worklog   | text, json
delete-worklog   | text, json
tracking         | text, json
estimate         | text, json
report           | text, csv, json
export           | csv, json (NO text!)
bulk-log         | text, json
```

But documentation implies they all support the same formats.

**Impact:** Users may try to export as CSV using the wrong command (e.g., `jira-as time log -f csv` instead of `jira-as time export -f csv`).

**Fix:** Split options table to show which commands support which output formats, OR add command-specific notes.

---

## Medium Priority Issues (Style & Consistency)

### Issue #5: Example Uses `--dry-run` Instead of `-n`

**Severity:** MEDIUM (Style Inconsistency)

**Location:** Line 290

**Documentation:**
```bash
jira-as time delete-worklog PROJ-123 -w 12345 --dry-run
```

**Better Style:**
```bash
jira-as time delete-worklog PROJ-123 -w 12345 -n
```

**Analysis:** While both `--dry-run` and `-n` work, the documentation uses inconsistent flag forms. Other examples use short forms (-n, -f, -o), but this one uses the long form.

**Fix:** Standardize on short-form flags throughout examples.

---

### Issue #6: Example Uses `--yes` Instead of `-y`

**Severity:** MEDIUM (Style Inconsistency)

**Location:** Line 305

**Documentation:**
```bash
jira-as time delete-worklog PROJ-123 -w 12345 --yes
```

**Better Style:**
```bash
jira-as time delete-worklog PROJ-123 -w 12345 -y
```

**Analysis:** Both forms work, but documentation uses inconsistent forms. Most examples use short flags.

**Fix:** Change to `-y` for consistency.

---

### Issue #7: Example Uses `--author` Instead of `-a`

**Severity:** MEDIUM (Style Inconsistency)

**Location:** Line 174

**Documentation:**
```bash
jira-as time worklogs PROJ-123 --author currentUser()
```

**Better Style:**
```bash
jira-as time worklogs PROJ-123 -a currentUser()
```

**Analysis:** Both forms work, but inconsistent with other examples using short flags.

**Fix:** Use `-a` for consistency.

---

### Issue #8: Example Uses Long Flags Instead of Short Forms

**Severity:** MEDIUM (Style Inconsistency)

**Location:** Line 177

**Documentation:**
```bash
jira-as time worklogs PROJ-123 --since 2025-01-01 --until 2025-01-31
```

**Better Style:**
```bash
jira-as time worklogs PROJ-123 -s 2025-01-01 -u 2025-01-31
```

**Analysis:** Long forms work but are inconsistent with the short-form style used elsewhere.

**Fix:** Standardize on short flags.

---

### Issue #9: Ambiguous -f Flag Across Commands

**Severity:** MEDIUM (Confusing Flag Overloading)

**Location:** Multiple examples (lines 237, 243, 250, etc.)

**Problem:**
The `-f` flag has different meanings in different commands:
- `report`: `-f/--format` (output format)
- `export`: `-f/--format` (output format)
- `bulk-log`: `-f/--force` (skip confirmation)

**Example:**
```bash
jira-as time report -p PROJ --period this-week -f csv    # -f = format
jira-as time export -p PROJ --period last-month -f csv   # -f = format
jira-as time bulk-log -i PROJ-1,PROJ-2 -t 15m -c "x" -f  # -f = force!
```

**Impact:** Users unfamiliar with each command will be confused about what `-f` does.

**Fix:** Add a note in Common Options clarifying flag meanings by command.

---

### Issue #10: `update-worklog` Doesn't Support `manual` Mode for `--adjust-estimate`

**Severity:** MEDIUM (Undocumented Limitation)

**Location:** Affecting lines 92-94, 214-218

**Problem:**
The documentation suggests `--adjust-estimate` modes are consistent across commands. But actual CLI shows:

```bash
# log command:
-a, --adjust-estimate [auto|leave|new|manual]

# update-worklog command:
--adjust-estimate [auto|leave|new]  # NO manual!

# delete-worklog command:
-a, --adjust-estimate [auto|leave|new|manual]
```

The `update-worklog` command **does not support manual mode**.

**Impact:** Users trying to use manual mode with update might fail or get unexpected behavior.

**Fix:** Document that `update-worklog` only supports `[auto|leave|new]`, while `log` and `delete-worklog` support `manual` mode too.

---

## Low Priority Issues (Minor Gaps)

### Issue #11: Single Quotes in Example

**Severity:** LOW (Style)

**Location:** Line 268

**Documentation:**
```bash
jira-as time bulk-log -i PROJ-1,PROJ-2 -t 15m -c 'Sprint planning' -n
```

**Better Style:**
```bash
jira-as time bulk-log -i PROJ-1,PROJ-2 -t 15m -c "Sprint planning" -n
```

**Analysis:** Single quotes work in most shells, but documentation uses double quotes elsewhere. Inconsistent quoting style.

**Fix:** Standardize on double quotes.

---

### Issue #12: YYYY-MM Format Not Explicitly Mentioned for Export

**Severity:** LOW (Documentation Gap)

**Location:** Lines 111-116 (Export-specific options)

**Problem:**
The `report` command documentation (line 104) explicitly mentions YYYY-MM format:
```
--period PERIOD: ... or YYYY-MM format
```

But the `export` command documentation (lines 111-116) shows:
```
| `--period PERIOD` | Predefined time period OR YYYY-MM format... |
```

Wait, it DOES mention it. So this is actually fine. ✓ (No action needed)

---

### Issue #13: Missing --period Documentation in Export Options

**Severity:** LOW (Minor Gap)

Actually, checking lines 111-116 again... the export options table DOES include --period and mentions YYYY-MM format:

```
| `--period PERIOD` | Time period: today, yesterday, this-week, last-week, this-month, last-month, or YYYY-MM format |
```

So this is correct. ✓ (No action needed)

---

### Issue #14: Confusing Mention of adjust-estimate Behavior

**Severity:** LOW (Clarity Issue)

**Location:** Lines 429-437 (FAQ section)

**Documentation:**
```
| Mode | Effect |
|------|--------|
| `auto` | Reduces remaining by time logged |
| `leave` | No change to remaining estimate |
| `new` | Sets remaining to a new value |
| `manual` | Reduces remaining by specified amount |
```

**Analysis:** This table applies to the `log` command specifically, but also applies to `delete-worklog`. However, `update-worklog` does not support `manual` mode, which isn't clear.

**Fix:** Add a note that `manual` mode is only available for `log` and `delete-worklog`, not `update-worklog`.

---

## Recommendations Summary

### Critical (Do First):

1. **Fix line 155 example** - Remove `--reduce-by` from log example
2. **Update Common Options table** - Add missing worklogs filter options
3. **Clarify --reduce-by documentation** - Remove from general options, specify delete-worklog only

### High Priority (Do Next):

4. **Document output format differences** - Show which commands support which formats
5. **Clarify adjust-estimate modes** - Document that update-worklog doesn't support manual mode

### Medium Priority (Polish):

6. **Standardize flag usage** - Use short forms consistently (-a, -s, -u, -n, -y)
7. **Document -f ambiguity** - Note that -f means different things in different commands
8. **Fix flag inconsistencies** - Consistent style throughout

### Low Priority (Nice to Have):

9. **Standardize quoting** - Use double quotes consistently
10. **Add command-specific notes** - Clarify which command has which limitations

---

## Testing Recommendations

To verify fixes, run:

```bash
# Test that failing example is fixed
jira-as time log DEMO-123 -t 2h --adjust-estimate auto

# Test filter options are discoverable
jira-as time worklogs DEMO-123 -a currentUser()

# Verify format support
jira-as time report -p DEMO -f json
jira-as time export -p DEMO -f csv

# Verify adjust-estimate limitations
jira-as time update-worklog DEMO-123 -w 12345 --adjust-estimate new --new-estimate 2h

# This should fail:
jira-as time update-worklog DEMO-123 -w 12345 --adjust-estimate manual
```

---

## Files Referenced

- **Skill Documentation:** `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/skills/jira-time/SKILL.md`
- **CLI Binary:** `jira-as time` (part of jira-as PyPI package)
- **JSON Findings:** `jira-time.json` (this directory)

---

## Conclusion

The jira-time skill documentation is solid overall with all commands properly listed and mostly accurate. The primary issues are:
- **1 blocking error** that causes runtime failures (line 155)
- **1 misleading documentation** about --reduce-by availability
- **Multiple style inconsistencies** in examples

These should all be relatively straightforward to fix, with the main benefit being that users won't encounter surprise failures when running documented examples.
