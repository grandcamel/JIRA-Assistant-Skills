# Skill Review Findings

This directory contains detailed findings from systematic reviews of JIRA Assistant Skills documentation against actual CLI implementations.

## Recent Reviews

### jira-time (2026-01-31)

**Status:** 14 issues found (2 high, 8 medium, 4 low) - 77% accuracy

The jira-time skill documentation has comprehensive coverage of all 9 CLI commands (log, worklogs, update-worklog, delete-worklog, estimate, tracking, report, export, bulk-log), but contains several critical errors that will cause runtime failures.

**Critical Issues:**
1. Line 155: Example uses unsupported `--reduce-by` flag with log command
2. Lines 79-83: Common Options table missing worklogs filter options
3. Lines 92-94: Documentation incorrectly claims `--reduce-by` works with log command

**Key Findings:**
- 2 examples that will fail at runtime
- 5 missing or incomplete option documentations
- 4 example style inconsistencies
- Several command-specific feature limitations not documented

**Files:**
- `jira-time.json` - Structured findings (14 issues with IDs, types, severity levels)
- `jira-time-review.md` - Comprehensive narrative report with detailed explanations and recommendations

**Files Generated:**
- `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/docs/reviews/findings/jira-time.json`
- `/Users/jasonkrueger/IdeaProjects/Jira-Assistant-Skills/docs/reviews/findings/jira-time-review.md`

## Review Methodology

Reviews follow a systematic approach:

1. **Documentation Review**: Read the complete SKILL.md file
2. **CLI Analysis**: Run actual CLI commands and subcommands with --help
3. **Comparison**: Map documented features against actual CLI behavior
4. **Categorization**: Classify issues by type and severity
5. **Reporting**: Generate both structured (JSON) and narrative (Markdown) reports

## Issue Categories

- **WRONG_SYNTAX**: Examples that don't match actual CLI syntax
- **MISSING_COMMAND**: Documented command doesn't exist
- **UNDOCUMENTED_COMMAND**: CLI command not mentioned in documentation
- **UNDOCUMENTED_OPTION**: CLI option not documented
- **OUTDATED_OPTION**: Documentation uses outdated or inconsistent flag forms
- **MISSING_OPTION**: Command supports option not documented
- **EXAMPLE_ERROR**: Example has syntax errors or inconsistencies

## Severity Levels

- **HIGH**: Issues that cause runtime failures or critical inaccuracies
- **MEDIUM**: Issues that cause confusion or mislead users
- **LOW**: Minor style or consistency issues

## Report Format

Each review generates:

1. **JSON Report** (`{skill}.json`)
   - Structured data with individual findings
   - Machine-readable format for processing
   - Includes issue IDs, types, severity, line numbers
   - Command accuracy summary
   - Options discrepancies

2. **Markdown Report** (`{skill}-review.md`)
   - Human-readable comprehensive review
   - Detailed explanations with examples
   - Testing recommendations
   - Priority-based fix list
   - Risk assessment

## Navigation

To view detailed findings:

```bash
# For high-level summary
cat jira-time.json | jq '.summary'

# For individual findings
cat jira-time.json | jq '.findings[] | select(.severity == "high")'

# For complete narrative review
less jira-time-review.md
```

## Action Items

For each review, recommended fixes are categorized as:

- **MUST FIX**: Blocking issues that cause runtime failures
- **SHOULD FIX**: High-value improvements that prevent user confusion
- **NICE TO FIX**: Polish improvements for consistency

