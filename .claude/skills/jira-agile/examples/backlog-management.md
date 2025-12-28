# Backlog Management Examples

Detailed examples for viewing and ranking backlog issues.

## Viewing Backlog

```bash
# Get full backlog for a board
python get_backlog.py --board 123

# Filter backlog by JQL
python get_backlog.py --board 123 --filter "priority=High"

# Group backlog by epic
python get_backlog.py --board 123 --group-by epic

# Limit results
python get_backlog.py --board 123 --max-results 50

# Export as JSON
python get_backlog.py --board 123 --output json
```

### Example Output

```
Backlog: 25/100 issues

[No Epic] (5 issues)
  PROJ-201 - Bug fix for login
  PROJ-202 - Update dependencies
  ...

[PROJ-100] (8 issues)
  PROJ-101 - User authentication (5 pts)
  PROJ-102 - Dashboard layout (8 pts)
  ...

[PROJ-150] (12 issues)
  PROJ-151 - API endpoints (3 pts)
  ...
```

## Ranking Issues in Backlog

```bash
# Rank issue before another
python rank_issue.py PROJ-1 --before PROJ-2

# Rank issue after another
python rank_issue.py PROJ-1 --after PROJ-3

# Move issue to top of backlog
python rank_issue.py PROJ-1 --top

# Move issue to bottom of backlog
python rank_issue.py PROJ-1 --bottom

# Bulk rank multiple issues
python rank_issue.py PROJ-1,PROJ-2,PROJ-3 --before PROJ-10
```

## Common Workflows

### Backlog Refinement Session

1. View backlog grouped by epic:
   ```bash
   python get_backlog.py --board 123 --group-by epic
   ```

2. Find unestimated items:
   ```bash
   python jql_search.py "sprint IS EMPTY AND 'Story Points' IS EMPTY AND type IN (Story, Task)"
   ```

3. Prioritize high-value items:
   ```bash
   python rank_issue.py PROJ-201 --top
   python rank_issue.py PROJ-205 --before PROJ-201
   ```

4. Bulk estimate similar items:
   ```bash
   python estimate_issue.py --jql "labels=quick-win" --points 2 --dry-run
   ```

### Sprint Planning Prep

1. Review top backlog items:
   ```bash
   python get_backlog.py --board 123 --max-results 20
   ```

2. Filter high-priority items:
   ```bash
   python get_backlog.py --board 123 --filter "priority IN (High, Highest)"
   ```

3. Move items to sprint:
   ```bash
   python move_to_sprint.py --sprint 456 --issues PROJ-201,PROJ-202 --rank top
   ```

## See Also

- [Sprint Lifecycle](sprint-lifecycle.md) - Move backlog items to sprints
- [Estimation](estimation.md) - Estimate backlog items
- [Best Practices](../docs/BEST_PRACTICES.md#backlog-refinement) - Backlog refinement guidance
