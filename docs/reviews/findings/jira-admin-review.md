# JIRA Admin Skill Documentation Review

**Date:** 2026-01-31
**Reviewer:** Claude Code
**Skill:** jira-admin (SKILL.md)
**Target:** `jira-as admin` CLI commands

---

## Executive Summary

The jira-admin SKILL.md documentation is well-structured with comprehensive coverage of 8 major administration areas. However, there are **5 significant findings** that affect command usability:

- **3 HIGH severity** issues affecting command syntax clarity
- **2 MEDIUM severity** issues affecting command discoverability

The documentation covers all major command categories but lacks precision in:
1. Optional vs required parameters
2. Shorthand flag options
3. Available filter options
4. Preview/dry-run capabilities

---

## Review Methodology

1. **Documentation Analysis:** Read complete SKILL.md file to identify all documented CLI commands
2. **CLI Interrogation:** Ran `jira-as admin --help` and 20+ subcommand helps to capture actual syntax
3. **Comparative Analysis:** Matched documented commands against actual CLI capabilities
4. **Validation:** Verified each finding with multiple --help invocations

### Commands Reviewed

| Category | Subcommands Tested |
|----------|-------------------|
| Project Management | list, get, create, update, delete, archive, restore |
| Configuration | config get |
| Categories | list, create, assign |
| Automation | list, get, search, enable, disable, toggle, invoke, automation-template |
| Permissions | permission-scheme (list, get, create, assign), permission (list, check) |
| Users & Groups | user (search, get), group (list, members, create, delete, add-user, remove-user) |
| Notifications | notification-scheme (list, get, create), notification (add, remove) |
| Screens | screen (list, get, tabs, fields, add-field, remove-field), screen-scheme (list, get) |
| Issue Types | issue-type (list, get, create, update, delete), issue-type-scheme (list, get, create, assign, project) |
| Workflows | workflow (list, get, search, for-issue), workflow-scheme (list, get, assign), status (list) |

---

## Detailed Findings

### Finding 1: WRONG_SYNTAX - automation list requires clarity (HIGH)

**Location:** Line 158, Available Commands section

**Documented:**
```bash
jira-as admin automation list --project PROJ  # List automation rules
```

**Actual CLI:**
```bash
jira-as admin automation list [OPTIONS]
```

**Options:**
- `-p, --project TEXT` - optional filter
- `-s, --state [enabled|disabled]` - optional filter
- `--all` - optional flag for all pages
- `-o, --output [text|json]` - optional output format

**Issue:** The documentation shows `--project PROJ` as if it's required, but it's actually optional. Users expecting to list ALL automation rules without filtering won't know they can omit `--project`.

**Impact:** Moderate - users may be confused about the command's flexibility

**Recommendation:**
- Update line 158 to: `jira-as admin automation list`
- Add examples showing both filtered and unfiltered usage:
  ```bash
  jira-as admin automation list                    # All rules
  jira-as admin automation list --project PROJ    # Rules for specific project
  jira-as admin automation list --state enabled   # Enabled rules only
  ```

---

### Finding 2: WRONG_SYNTAX - permission check uses required option (HIGH)

**Location:** Line 181, Permission Diagnostics section

**Documented:**
```bash
jira-as admin permission check --project DEMO
```

**Actual CLI:**
```bash
jira-as admin permission check [OPTIONS]
```

**Required Options:**
- `-p, --project TEXT` - required, not shown clearly as such

**Issue:** The documented example is correct, but the documentation doesn't clearly indicate that `--project` is REQUIRED. Users might attempt to run the command without the project parameter and receive an error.

**Impact:** Moderate - users may misunderstand the command's requirements

**Additional Issue:** Troubleshooting section (lines 327, 338) shows inconsistent presentation of the same command without emphasizing the required parameter.

**Recommendation:**
- Clarify that `-p/--project` is required
- Update line 181 to include a note:
  ```bash
  jira-as admin permission check --project DEMO  # Check permissions on a project (--project required)
  ```
- Ensure consistency across all documented examples (lines 327, 338)

---

### Finding 3: MISSING_OPTION - group delete lacks --dry-run and shorthand (HIGH)

**Location:** Line 191, User & Group Management section

**Documented:**
```bash
jira-as admin group delete GROUP_NAME --confirm
```

**Actual CLI:**
```bash
jira-as admin group delete GROUP_NAME [OPTIONS]
```

**Available Options:**
- `-y, --confirm` - shorthand available as `-y`
- `--dry-run` - preview deletion without executing
- `-o, --output [text|json]` - output format

**Issue:** The documentation omits:
1. Shorthand `-y` flag (equivalent to `--confirm`)
2. `--dry-run` flag for safe preview before deletion

Given the DANGER risk level noted in the skill (line 41: "Delete group - !!! - Members lose group access"), the omission of `--dry-run` is particularly significant.

**Impact:** High - users may not know they can preview deletions before executing

**Recommendation:**
- Update line 191 to:
  ```bash
  jira-as admin group delete GROUP_NAME --confirm  # or -y
  ```
- Add new documentation about safety patterns (e.g., in "Common Patterns" section):
  ```bash
  jira-as admin group delete GROUP_NAME --dry-run  # Preview deletion
  jira-as admin group delete GROUP_NAME --confirm  # Execute deletion
  ```

---

### Finding 4: MISSING_OPTION - group remove-user incomplete (MEDIUM)

**Location:** Line 193, User & Group Management section

**Documented:**
```bash
jira-as admin group remove-user GROUP_NAME --user EMAIL --confirm
```

**Actual CLI:**
```bash
jira-as admin group remove-user GROUP_NAME [OPTIONS]
```

**Available Options:**
- `-u, --user TEXT` - shorthand available as `-u`, accepts account ID OR email
- `-y, --confirm` - shorthand available as `-y`
- `-o, --output [text|json]` - output format

**Issue:** The documentation:
1. Omits shorthand `-u` flag option
2. Doesn't clarify that both account IDs and email addresses are accepted
3. Doesn't show `-y` as shorthand for `--confirm`

**Impact:** Medium - users may not discover shorthand options or may try email when account ID is required

**Recommendation:**
- Update line 193 to clarify parameter flexibility:
  ```bash
  jira-as admin group remove-user GROUP_NAME --user ACCOUNT_ID_OR_EMAIL --confirm
  ```
- Add note explaining: "The --user parameter accepts either account ID or email address"
- Show shorthand variant: `jira-as admin group remove-user GROUP_NAME -u EMAIL -y`

---

### Finding 5: MISSING_OPTION - user search lacks documented filters (MEDIUM)

**Location:** Lines 186, 261, User & Group Management section

**Documented:**
```bash
jira-as admin user search "name"              # Search for users by name or email
jira-as admin user search "your.name" --include-groups  # From line 261
```

**Actual CLI:**
```bash
jira-as admin user search QUERY [OPTIONS]
```

**Available Options:**
- `-g, --include-groups` - include group memberships (shown in example at line 261)
- `-p, --project TEXT` - filter by assignable to project
- `-a, --assignable` - search only assignable users (requires --project)
- `--all` - include inactive users
- `--max-results INTEGER` - limit results
- `-o, --output [text|json]` - output format

**Issue:** The main command reference (line 186) doesn't document available filter options. Line 261 includes one example with `--include-groups`, which is good, but other powerful filters are not mentioned:
- `--assignable` for finding assignable users in a project
- `--all` for including inactive users
- `--max-results` for pagination

**Impact:** Medium - users won't discover filtering capabilities that could optimize searches

**Recommendation:**
- Expand the user search documentation in the main reference section:
  ```bash
  jira-as admin user search "name"                              # Search by name/email
  jira-as admin user search "name" --include-groups            # Show group membership
  jira-as admin user search "name" --project PROJ --assignable # Find assignable users
  jira-as admin user search "name" --all                       # Include inactive users
  ```
- Add a subsection "User Search Filters" with examples of each option
- Cross-reference the examples already shown in the "Getting Started" section (line 261)

---

## Documentation Strengths

The SKILL.md demonstrates excellent practices in several areas:

| Strength | Location | Example |
|----------|----------|---------|
| Risk level clarity | Lines 18-41 | Clear matrix of operation risks |
| Comprehensive coverage | Lines 51-62 | 8 major admin areas documented |
| Troubleshooting guide | Lines 322-346 | Addresses common permission issues |
| Common patterns section | Lines 274-291 | Shows dry-run and JSON output |
| Permission requirements | Lines 295-307 | Clear permission matrix |
| Best practices reference | Lines 397-410 | Links to detailed guides |
| Related skills integration | Lines 381-393 | Shows workflow between skills |

---

## Documentation Weaknesses

Areas where documentation could be enhanced:

| Weakness | Impact | Location |
|----------|--------|----------|
| Optional parameters not marked | Medium | Throughout "Available Commands" |
| Shorthand flags not documented | Low | User/Group operations |
| Filter options incomplete | Medium | User search, automation list |
| --dry-run capability underexposed | High | Deletion operations |
| Inconsistent parameter naming | Low | Examples (PROJ vs PROJECT_KEY) |
| automation search vs list distinction unclear | Low | Automation Rules section |

---

## Alignment with CLAUDE.md Standards

The documentation follows the project's patterns well:

✓ **Skills** - Uses third-person description for triggering
✓ **Component Conventions** - Body in imperative form directed at Claude
✓ **Risk Assessment** - Comprehensive risk levels defined
✓ **Error Handling** - Common errors section included
✓ **Related Skills** - Integration with other skills documented

**Areas for improvement:**
- Could better distinguish between list and search operations (automation list vs automation search)
- Some common patterns need visibility (particularly --dry-run for destructive operations)

---

## Summary of Changes Required

### Critical (Must Fix)

1. **Line 158:** Clarify that `--project` is optional for automation list
2. **Line 181:** Emphasize that `--project` is required for permission check
3. **Line 191:** Document `--dry-run` capability for group delete
4. **Line 193:** Clarify that `--user` accepts both account ID and email

### Important (Should Fix)

5. **Line 186:** Expand user search documentation with available filters
6. **Lines 261, 327, 338:** Ensure consistent presentation of permission check requirements

### Nice to Have (Could Improve)

- Document shorthand flag options (-u, -y, etc.)
- Clarify automation search vs list distinction
- Add more examples showing filter combinations
- Cross-reference related filtering options between commands

---

## Recommendations Summary

| Finding | Severity | Recommendation | Effort |
|---------|----------|-----------------|--------|
| automation list option clarity | HIGH | Rewrite line 158 with examples | Low |
| permission check requirement clarity | HIGH | Add note emphasizing required --project | Low |
| group delete --dry-run omission | HIGH | Add to Common Patterns section | Low |
| group remove-user parameter clarity | MEDIUM | Update parameter description | Low |
| user search filters undocumented | MEDIUM | Expand with filter examples | Medium |

**Total effort:** Low to Medium. Most findings can be addressed with documentation clarifications rather than code changes.

---

## References

- **SKILL.md Location:** `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/skills/jira-admin/SKILL.md`
- **CLI Tests:** Verified via `jira-as admin [subcommand] --help` on 2026-01-31
- **Related Project Docs:** CLAUDE.md provides skill architecture guidelines
