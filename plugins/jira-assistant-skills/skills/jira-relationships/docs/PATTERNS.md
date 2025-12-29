# Issue Relationships: Architecture Patterns

Strategic guidance for managing complex issue relationships in JIRA.

---

## Blocker Chain Analysis

### Prioritizing Blockers

When analyzing blocker chains with `get_blockers.py --recursive`:

1. **Work leaves first**: Blockers with no sub-blockers can start immediately
2. **High-impact blockers**: Issues blocking multiple downstream issues
3. **Long chain blockers**: Issues on critical paths (depth > 2)

### Sprint Planning Pattern

```bash
# Before committing to a story, check blocker depth
python get_blockers.py STORY-100 --recursive --depth 5

# Decision criteria:
# - Depth 0-1: Safe to commit
# - Depth 2-3: Review blockers for resolution timeline
# - Depth 4+: Consider deferring or breaking dependencies
```

### Blocker Hygiene

**Daily:** Update blocker status, remove resolved links
**Weekly:** Escalate blockers > 5 days old
**Sprint:** Audit all blocker chains before planning

---

## Managing Circular Dependencies

### Detection

```bash
python get_blockers.py PROJ-100 --recursive --output tree
# Output shows [CIRCULAR] when cycle detected
```

### Breaking Strategies

| Strategy | When to Use | Example |
|----------|-------------|---------|
| **Remove false dependency** | One link is "nice to have" | Unlink the weakest |
| **Insert intermediary** | Both need shared resource | Create API contract issue |
| **Parallelize** | Both can start with partial info | Change to "relates to" |
| **Timebox** | Dependency unclear until work starts | Remove, add sync label |

### Prevention

Dependencies should flow as a DAG (Directed Acyclic Graph):
- Foundation -> Features -> Integration -> Deployment
- Infrastructure -> Platform -> Product
- Design -> Development -> Testing -> Release

---

## Cross-Project Linking

### When to Link Across Projects

- Team A building API that Team B consumes
- Infrastructure team unblocking feature teams
- Platform migrations affecting multiple products
- Shared services with multiple consumers

### Best Practices

```bash
# Bulk link all teams waiting on platform upgrade
python bulk_link.py \
  --jql "project IN (TEAM-A, TEAM-B, TEAM-C) AND labels = needs-platform-v2" \
  --is-blocked-by PLATFORM-500
```

**Coordination checklist:**
- Ensure blocker team's sprint includes the blocker
- Set up notification when blocker resolves
- Align version/release schedules

### Anti-Patterns

| Problem | Impact | Solution |
|---------|--------|----------|
| Duplicate tracking | Both teams track same work | Single issue, both as watchers |
| Phantom dependencies | Could be parallel | Challenge if real; parallelize |
| Abandoned blockers | Blocks never resolved | Weekly cross-team review |
| No ownership | No one accountable | Assign blocker, set due date |

---

## Issue Cloning Strategies

### When to Clone

| Scenario | Strategy |
|----------|----------|
| Multi-platform features | Clone per platform (iOS -> Android) |
| Recurring workflows | Clone as template (onboarding epic) |
| Environment promotion | Clone dev -> staging -> prod |
| Team replication | Clone for other squad |

### Clone Options

```bash
# Fresh start (no historical dependencies)
python clone_issue.py PROJ-100

# Preserve structure
python clone_issue.py PROJ-100 --include-links --include-subtasks

# Different project
python clone_issue.py PROJ-100 --to-project OTHER
```

### Post-Clone Checklist

- Clear sprint assignment (will be planned separately)
- Reset story points (re-estimate for new context)
- Update assignee (may be different team)
- Clear time tracking (clone starts fresh)

---

## Dependency Visualization

### Choosing the Right Format

| Format | Best For | Renders In |
|--------|----------|------------|
| `mermaid` | GitHub/GitLab docs, wikis | Markdown viewers |
| `dot` | Publication-quality, complex graphs | Graphviz CLI |
| `plantuml` | Architecture docs, formal specs | PlantUML server |
| `d2` | Modern diagramming | D2 CLI |
| `text` | Quick terminal preview | Console |

### Scope Guidelines

```bash
# Too broad - overwhelming
python get_dependencies.py PROJECT-ROOT --output mermaid

# Better - focused on current sprint
python get_dependencies.py SPRINT-EPIC --output mermaid
```

### Regular Updates

```bash
# Weekly release dependency update
python get_dependencies.py RELEASE-EPIC --output dot > weekly-deps.dot
dot -Tpng weekly-deps.dot -o release-deps-$(date +%Y%m%d).png
```

---

## Link Hygiene

### Anti-Patterns to Avoid

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Link inflation | Linking "just in case" | Only link for real dependencies |
| Wrong type | Using "Blocks" for everything | Use appropriate type |
| Phantom blockers | Marked blocked but could proceed | Challenge if real |
| Stale links | Links to closed issues | Weekly cleanup |
| Duplicate links | Multiple links between same issues | Check before adding |

### Maintenance Schedule

**Daily:** Update blocker status in standup
**Weekly:** Remove stale links, consolidate duplicates
**Monthly:** Generate `link_stats.py --project PROJ` report, review issues with >10 links

---

## JQL for Dependency Tracking

```jql
# Find all issues you're blocking others with
issueFunction in linkedIssuesOf("assignee = currentUser()", "blocks")

# Find issues blocked by resolved issues (stale blockers)
issueFunction in linkedIssuesOf("status = Done", "is blocked by")

# Find issues blocking sprint work
issueFunction in linkedIssuesOf("sprint = 42", "is blocked by")
  AND status != Done

# Circular dependency candidates (issues that both block and are blocked)
issueFunction in linkedIssuesOf("project = PROJ", "blocks")
  AND issueFunction in linkedIssuesOf("project = PROJ", "is blocked by")
```

---

*This guide covers strategic patterns. For operational usage, see `--help` on each script.*
