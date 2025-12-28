# Scripts Guide

Detailed documentation for all jira-ops command-line scripts.

## discover_project.py

Discover JIRA project context and save to skill directory for intelligent defaults.

### Usage

```bash
# Discover and save to shareable skill directory
python discover_project.py PROJ

# Use specific profile
python discover_project.py PROJ --profile development

# Save to personal settings.local.json instead
python discover_project.py PROJ --personal

# Save to both skill directory and settings.local.json
python discover_project.py PROJ --both

# Custom sample size and period
python discover_project.py PROJ --sample-size 200 --days 60

# Output as JSON without saving
python discover_project.py PROJ --output json --no-save
```

### What Gets Discovered

- **Metadata**: Issue types, components, versions, priorities, assignable users
- **Workflows**: Valid status transitions for each issue type
- **Patterns**: Common assignees, labels, priorities based on recent activity
- **Defaults**: Auto-generated sensible defaults based on patterns

### Output Structure

Creates a skill directory at `.claude/skills/jira-project-{PROJECT_KEY}/`:
```
jira-project-PROJ/
  SKILL.md              # Skill documentation
  context/
    metadata.json       # Issue types, components, versions
    workflows.json      # Status transitions per issue type
    patterns.json       # Usage patterns from recent issues
  defaults.json         # Auto-generated default values
```

## cache_status.py

Display JIRA cache statistics and status.

### Usage

```bash
# Show cache status
python cache_status.py

# Output as JSON
python cache_status.py --json
```

### Output

```
Cache Statistics:
  Total Size: 12.5 MB / 100 MB
  Entries: 1,234
  Hit Rate: 78% (1000 hits, 234 misses)

By Category:
  issue: 800 entries, 8 MB
  project: 50 entries, 1 MB
  user: 200 entries, 2 MB
  field: 184 entries, 1.5 MB
```

## cache_clear.py

Clear JIRA cache entries.

### Usage

```bash
# Clear all cache
python cache_clear.py --force

# Clear specific category
python cache_clear.py --category issue --force

# Clear by pattern
python cache_clear.py --pattern "PROJ-*" --category issue --force

# Dry run (preview what will be cleared)
python cache_clear.py --dry-run
```

### Options

| Option | Description |
|--------|-------------|
| `--force` | Skip confirmation prompt |
| `--category` | Clear only specific category (issue, project, user, field, search) |
| `--pattern` | Clear entries matching pattern (supports wildcards) |
| `--dry-run` | Preview what would be cleared without clearing |

## cache_warm.py

Pre-warm JIRA cache with commonly accessed data.

### Usage

```bash
# Cache projects
python cache_warm.py --projects

# Cache field definitions
python cache_warm.py --fields

# Cache everything
python cache_warm.py --all --profile production --verbose
```

### Options

| Option | Description |
|--------|-------------|
| `--projects` | Warm project metadata |
| `--fields` | Warm field definitions |
| `--all` | Warm all categories |
| `--profile` | Use specific JIRA profile |
| `--verbose` | Show detailed progress |
