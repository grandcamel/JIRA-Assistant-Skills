# Common Options Reference

All jira-agile scripts support these common options.

## Profile Selection

```bash
--profile <name>    # Use a specific JIRA profile (dev, staging, prod)
```

**Examples:**
```bash
python get_epic.py PROJ-100 --profile development
python create_sprint.py --board 123 --name "Sprint 1" --profile staging
```

Profiles are configured in `.claude/settings.json` or `.claude/settings.local.json`.

## Output Format

```bash
--output <format>   # Output format: text (default), json
```

**Examples:**
```bash
python get_epic.py PROJ-100 --output json
python get_sprint.py 456 --with-issues --output json
python get_backlog.py --board 123 --output json
python get_estimates.py --sprint 456 --output json
```

JSON output is useful for:
- Piping to other tools (`jq`, scripts)
- Programmatic processing
- Integration with CI/CD pipelines

## Dry Run Mode

For scripts that modify data, preview changes before applying:

```bash
--dry-run           # Preview changes without making them
```

**Examples:**
```bash
python add_to_epic.py --epic PROJ-100 --issues PROJ-101,PROJ-102 --dry-run
python move_to_sprint.py --sprint 456 --jql "status='To Do'" --dry-run
python estimate_issue.py --jql "sprint=456" --points 3 --dry-run
```

Dry run shows:
- Which issues would be affected
- What changes would be made
- Any validation errors

## Exit Codes

All scripts return standard exit codes:

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Operation completed successfully |
| 1 | Error | Operation failed (validation, API error, etc.) |
| 130 | Cancelled | Operation cancelled by user (Ctrl+C) |

**Shell script usage:**
```bash
python add_to_epic.py --epic PROJ-100 --issues PROJ-101
if [ $? -eq 0 ]; then
    echo "Issues added successfully"
else
    echo "Failed to add issues"
fi
```

## Getting Help

All scripts support:
```bash
--help    # Show usage, options, and examples
```

**Example:**
```bash
python create_sprint.py --help
```

## See Also

- [Quick Start](QUICK_START.md) - Essential workflows
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues
