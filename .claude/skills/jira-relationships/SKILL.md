# jira-relationships

Issue linking and dependency management for JIRA - create, view, and analyze issue relationships.

## When to use this skill

Use this skill when you need to:
- Link issues together (blocks, duplicates, relates to, clones)
- View issue dependencies and blockers
- Find blocker chains and critical paths
- Analyze issue relationships and dependencies
- Bulk link multiple issues
- Clone issues with their relationships

## What this skill does

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
   - Transitive dependency tracking

7. **Bulk Operations**: Link multiple issues at once
   - Link from JQL query results
   - Progress tracking
   - Skip existing links

8. **Clone Issues**: Duplicate issues with relationships
   - Copy fields to new issue
   - Create "clones" link to original
   - Optionally copy subtasks and links

## Available scripts

- `get_link_types.py` - List available link types
- `link_issue.py` - Create link between issues
- `get_links.py` - View links for an issue
- `unlink_issue.py` - Remove issue links
- `get_blockers.py` - Find blocker chain (recursive)
- `get_dependencies.py` - Find all dependencies
- `bulk_link.py` - Bulk link multiple issues
- `clone_issue.py` - Clone issue with links

## Examples

```bash
# View available link types
python get_link_types.py
python get_link_types.py --filter "block"

# Create links (semantic flags)
python link_issue.py PROJ-1 --blocks PROJ-2
python link_issue.py PROJ-1 --duplicates PROJ-2
python link_issue.py PROJ-1 --relates-to PROJ-2
python link_issue.py PROJ-1 --clones PROJ-2

# Create links (explicit type)
python link_issue.py PROJ-1 --type "Blocks" --to PROJ-2 --comment "Dependency"

# View links
python get_links.py PROJ-123
python get_links.py PROJ-123 --inward
python get_links.py PROJ-123 --type blocks

# Remove links
python unlink_issue.py PROJ-1 --from PROJ-2
python unlink_issue.py PROJ-1 --type blocks --all

# Find blockers
python get_blockers.py PROJ-123
python get_blockers.py PROJ-123 --recursive --depth 3
python get_blockers.py PROJ-123 --output tree

# Bulk link
python bulk_link.py --issues PROJ-1,PROJ-2,PROJ-3 --blocks PROJ-100
python bulk_link.py --jql "project=PROJ AND fixVersion=1.0" --relates-to PROJ-500
python bulk_link.py --issues PROJ-1,PROJ-2 --blocks PROJ-100 --dry-run
python bulk_link.py --issues PROJ-1,PROJ-2 --blocks PROJ-100 --skip-existing

# Clone issue
python clone_issue.py PROJ-123
python clone_issue.py PROJ-123 --include-subtasks --include-links
python clone_issue.py PROJ-123 --to-project OTHER
python clone_issue.py PROJ-123 --summary "Clone: Custom title" --no-link

# Export dependency graphs
python get_dependencies.py PROJ-123 --output mermaid
python get_dependencies.py PROJ-123 --output dot > deps.dot
```

## Link Types

Common JIRA link types:

| Name | Outward | Inward |
|------|---------|--------|
| Blocks | blocks | is blocked by |
| Cloners | clones | is cloned by |
| Duplicate | duplicates | is duplicated by |
| Relates | relates to | relates to |

## Configuration

Uses shared configuration from `.claude/settings.json` and `.claude/settings.local.json`.
Requires JIRA credentials via environment variables or settings files.

## Related skills

- **jira-issue**: For creating and updating issues
- **jira-lifecycle**: For transitioning issues through workflows
- **jira-search**: For finding issues to link
- **jira-agile**: For epic and sprint management
