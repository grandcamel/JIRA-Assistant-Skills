---
name: "jira-issue-relationships"
description: "Issue linking and dependency management - create links, view blockers, analyze dependencies, clone issues. Use when linking issues, finding blocker chains, or cloning with relationships."
version: "1.0.0"
author: "jira-assistant-skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# jira-relationships

Issue linking and dependency management for JIRA - create, view, and analyze issue relationships.

## Risk Levels

| Operation | Risk | Notes |
|-----------|------|-------|
| Get link types | `-` | Read-only |
| Get links/blockers | `-` | Read-only |
| Get dependencies | `-` | Read-only |
| Link statistics | `-` | Read-only |
| Create link | `-` | Easily reversible (can unlink) |
| Remove link | `!` | Link data lost, can recreate |
| Bulk link | `!` | Many links created, can remove |
| Clone issue | `-` | Creates new issue, can delete |
| Clone with subtasks | `!` | Creates multiple issues |

**Risk Legend**: `-` Safe, read-only | `!` Caution, modifiable | `!!` Warning, destructive but recoverable | `!!!` Danger, irreversible

## When to use this skill

Use this skill when you need to:
- Link issues together (blocks, duplicates, relates to, clones)
- View issue dependencies and blockers
- Find blocker chains and critical paths
- Analyze issue relationships and dependencies
- Get link statistics for issues or projects
- Bulk link multiple issues
- Clone issues with their relationships

## What this skill does

**IMPORTANT:** Always use the `jira-as` CLI. Never run Python scripts directly.

This skill provides issue relationship operations:

1. **Get Link Types**: View available link types in JIRA instance
   - Lists all configured link types
   - Shows inward/outward descriptions
   - Filter by name pattern

2. **Link Issues**: Create relationships between issues
   - Semantic flags for common types (--blocks, --relates-to, etc.)
   - Support for all JIRA link types
   - Optional comment on link creation
   - Dry-run mode for preview

3. **View Links**: See all relationships for an issue
   - Filter by direction (inward/outward)
   - Filter by link type
   - Shows linked issue status and summary

4. **Remove Links**: Delete issue relationships
   - Remove specific links between issues
   - Remove all links of a type
   - Dry-run and confirmation modes

5. **Blocker Analysis**: Find blocking dependencies
   - Direct blockers for an issue
   - Recursive blocker chain traversal
   - Circular dependency detection
   - Critical path identification

6. **Dependency Graphs**: Visualize relationships
   - Export to DOT format for Graphviz
   - Export to Mermaid diagrams
   - Export to PlantUML format
   - Export to D2 diagrams (Terrastruct)
   - Transitive dependency tracking

7. **Link Statistics**: Analyze link patterns
   - Stats for single issue or entire project
   - Link breakdown by type and direction
   - Find orphaned issues (no links)
   - Identify most-connected issues
   - Status distribution of linked issues

8. **Bulk Operations**: Link multiple issues at once
   - Link from JQL query results
   - Progress tracking
   - Skip existing links

9. **Clone Issues**: Duplicate issues with relationships
   - Copy fields to new issue
   - Create "clones" link to original
   - Optionally copy subtasks and links

## Available Commands

| Command | Description |
|---------|-------------|
| `jira-as relationships link-types` | List available link types |
| `jira-as relationships link` | Create link between issues |
| `jira-as relationships get-links` | View links for an issue |
| `jira-as relationships unlink` | Remove issue links |
| `jira-as relationships get-blockers` | Find blocker chain (recursive) |
| `jira-as relationships get-dependencies` | Find all dependencies |
| `jira-as relationships stats` | Analyze link statistics for issues/projects |
| `jira-as relationships bulk-link` | Bulk link multiple issues |
| `jira-as relationships clone` | Clone issue with links |

All commands support `--help` for full documentation.

## Common Options

All commands support these common options:

| Option | Description |
|--------|-------------|
| `-o/--output FORMAT` | Output format (see table below) |
| `--help` | Show help message and exit |

### Output Formats by Command

| Command | Supported Formats |
|---------|-------------------|
| `link-types` | text, json |
| `link` | text, json |
| `get-links` | text, json |
| `unlink` | text, json |
| `get-blockers` | text, json |
| `get-dependencies` | text, json, mermaid, dot, plantuml, d2 |
| `stats` | text, json |
| `bulk-link` | text, json |
| `clone` | text, json |

## Examples

### Quick Start - Common Operations

```bash
# View available link types in your JIRA instance
jira-as relationships link-types
jira-as relationships link-types --filter block
jira-as relationships link-types --output json

# Create links using semantic flags
jira-as relationships link PROJ-1 --blocks PROJ-2
jira-as relationships link PROJ-1 --is-blocked-by PROJ-2   # Inverse direction
jira-as relationships link PROJ-1 --duplicates PROJ-2
jira-as relationships link PROJ-1 --clones PROJ-2          # Mark as clone
jira-as relationships link PROJ-1 --relates-to PROJ-2
jira-as relationships link PROJ-1 --type "Blocks" --to PROJ-2

# View and remove links
jira-as relationships get-links PROJ-123
jira-as relationships get-links PROJ-123 --direction outward
jira-as relationships unlink PROJ-1 PROJ-2
jira-as relationships unlink PROJ-1 PROJ-2 --dry-run
jira-as relationships unlink PROJ-1 --type blocks --all

# Clone an issue with its relationships
jira-as relationships clone PROJ-123 --clone-subtasks -l  # -l is short for --clone-links
jira-as relationships clone PROJ-123 -p OTHER  # -p is short for --to-project
jira-as relationships clone PROJ-123 --summary "Custom summary"
jira-as relationships clone PROJ-123 --no-link  # Skip creating "clones" link
```

### Advanced - Blocker Analysis & Statistics

```bash
# Find blocker chains for sprint planning
jira-as relationships get-blockers PROJ-123 --recursive
jira-as relationships get-blockers PROJ-123 --recursive --include-done
jira-as relationships get-blockers PROJ-123 -r --depth 3  # Limit recursion depth (0 = unlimited)
jira-as relationships get-blockers PROJ-123 -r --depth 0  # Unlimited depth
jira-as relationships get-blockers PROJ-123 -d inward  # -d/--direction: inward or outward

# Analyze dependencies (with link type filtering)
jira-as relationships get-dependencies PROJ-123
jira-as relationships get-dependencies PROJ-123 -t blocks,relates  # -t/--type for filtering

# Link statistics - multiple modes
# KEY_OR_PROJECT: optional positional argument for issue key or project key
# -p/--project: alternative option to specify project for project-wide analysis
jira-as relationships stats PROJ-123                       # Single issue stats (positional arg)
jira-as relationships stats PROJ                           # Project-wide stats (positional arg)
jira-as relationships stats -p PROJ                        # Project-wide stats (-p/--project option)
jira-as relationships stats --jql "type = Epic"            # JQL-filtered stats
jira-as relationships stats -p PROJ -t 20                  # Show top 20 connected (-t/--top)
jira-as relationships stats -p PROJ --max-results 100      # Limit issues analyzed

# Bulk link issues from JQL query (--output json for JSON output)
jira-as relationships bulk-link --jql "project=PROJ AND fixVersion=1.0" --relates-to PROJ-500 --dry-run
jira-as relationships bulk-link --issues PROJ-1,PROJ-2,PROJ-3 --blocks PROJ-100
jira-as relationships bulk-link --issues PROJ-1,PROJ-2 --blocks PROJ-100 --output json
jira-as relationships bulk-link --jql "sprint in openSprints()" --relates-to PROJ-500 --skip-existing  # Skip already linked
```

### Visualization - Dependency Graphs

```bash
# Export for documentation (Mermaid for GitHub/GitLab)
jira-as relationships get-dependencies PROJ-123 --output mermaid

# Export for publication (Graphviz)
jira-as relationships get-dependencies PROJ-123 --output dot > deps.dot
dot -Tpng deps.dot -o deps.png

# Export for PlantUML
jira-as relationships get-dependencies PROJ-123 --output plantuml > deps.puml

# Export for D2/Terrastruct
jira-as relationships get-dependencies PROJ-123 --output d2 > deps.d2
d2 deps.d2 deps.svg
```

## Exporting Dependency Graphs

Use `jira-as relationships get-dependencies` with `--output` flag to generate diagrams:
- Formats: `text` (default), `json`, `mermaid` (GitHub docs), `dot` (Graphviz), `plantuml`, `d2`
- All formats include status-based coloring and link type labels
- Run `jira-as relationships get-dependencies --help` for rendering instructions

## Link Types

Standard JIRA link types and when to use them:

| Link Type | Outward | Inward | When to Use |
|-----------|---------|--------|-------------|
| **Blocks** | blocks | is blocked by | Sequential dependencies: Task A must finish before B starts |
| **Duplicate** | duplicates | is duplicated by | Mark redundant issues; close the duplicate |
| **Relates** | relates to | relates to | General association; cross-team awareness |
| **Cloners** | clones | is cloned by | Issue templates; multi-platform variants |

**Link Direction:** When A blocks B, A is "outward" (blocks) and B is "inward" (is blocked by).
Use `--blocks` when source issue blocks target; use `--is-blocked-by` when source is blocked by target.

**Note:** Issue links are labels only - they do not enforce workflow rules. Combine with automation or team discipline.

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Error (validation failed, API error, or issue not found) |

## Troubleshooting

### "Issue does not exist" error
- Verify the issue key format is correct (e.g., PROJ-123)
- Check that you have permission to view the issue
- Confirm the project exists in your JIRA instance

### "Link type not found" error
- Run `jira-as relationships link-types` to see available link types
- Link type names are case-sensitive in some JIRA instances
- Custom link types may have different names than standard ones

### "Permission denied" when creating links
- Ensure you have "Link Issues" permission in the project
- Some projects may restrict who can create certain link types

### Bulk link operations timing out
- Reduce the number of issues in a single operation
- Use `--max-results` to limit JQL query results
- Consider breaking large operations into smaller batches

### Clone operation fails
- Verify you have "Create Issues" permission in the target project
- Check that required fields for the target project are satisfied
- Some fields may not be cloneable (e.g., custom field restrictions)

### Circular dependency detected
- The blocker analysis command automatically detects and reports cycles
- Review the blocker chain to identify and break the cycle
- Consider whether the blocking relationship is correctly modeled

## Configuration

Requires JIRA credentials via environment variables (`JIRA_SITE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`).

## Architecture Patterns

For strategic guidance on blocker chains, circular dependencies, cross-project linking, and visualization strategies, see [Patterns Guide](docs/PATTERNS.md).

## Related skills

- **jira-issue**: For creating and updating issues
- **jira-lifecycle**: For transitioning issues through workflows
- **jira-search**: For finding issues to link
- **jira-agile**: For epic and sprint management
