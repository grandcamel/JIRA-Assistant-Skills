# Estimation Examples

Detailed examples for setting story points and viewing estimation summaries.

## Setting Story Points

```bash
# Set story points on a single issue
python estimate_issue.py PROJ-1 --points 5

# Set story points on multiple issues
python estimate_issue.py PROJ-1,PROJ-2,PROJ-3 --points 3

# Clear story point estimate
python estimate_issue.py PROJ-1 --points 0

# Bulk update via JQL query
python estimate_issue.py --jql "sprint=456 AND type=Story" --points 2

# Validate against Fibonacci sequence
python estimate_issue.py PROJ-1 --points 5 --validate-fibonacci

# Output as JSON
python estimate_issue.py PROJ-1 --points 8 --output json
```

## Bulk Estimation

```bash
# Preview bulk estimation
python estimate_issue.py --jql "sprint=456 AND type=Story" --points 3 --dry-run

# Estimate all stories in a sprint
python estimate_issue.py --jql "sprint=456 AND type=Story AND 'Story Points' IS EMPTY" --points 2

# Estimate by label
python estimate_issue.py --jql "labels=quick-win" --points 1 --dry-run
```

## Getting Estimation Summaries

```bash
# Get story point summary for a sprint
python get_estimates.py --sprint 456

# Get story point summary for an epic
python get_estimates.py --epic PROJ-100

# Group by assignee
python get_estimates.py --sprint 456 --group-by assignee

# Group by status
python get_estimates.py --sprint 456 --group-by status

# Export as JSON
python get_estimates.py --sprint 456 --output json
```

### Example Output

```
Sprint 456 Estimates
Total: 55 points (25 issues)

By Status:
  Done: 32 points (58%)
  In Progress: 15 points (27%)
  To Do: 8 points (15%)

By Assignee:
  Alice: 20 points (36%)
  Bob: 18 points (33%)
  Charlie: 17 points (31%)
```

## Common Workflows

### Planning Poker Session

1. Find unestimated stories:
   ```bash
   python jql_search.py "sprint=456 AND 'Story Points' IS EMPTY"
   ```

2. Estimate each story after team discussion:
   ```bash
   python estimate_issue.py PROJ-101 --points 5 --validate-fibonacci
   python estimate_issue.py PROJ-102 --points 3 --validate-fibonacci
   ```

3. Review sprint capacity:
   ```bash
   python get_estimates.py --sprint 456 --group-by status
   ```

### Sprint Capacity Planning

1. View current sprint estimates:
   ```bash
   python get_estimates.py --sprint 456
   ```

2. Compare to team velocity (manual check or use reports)

3. Add or remove items as needed:
   ```bash
   python move_to_sprint.py --sprint 456 --issues PROJ-105
   python move_to_sprint.py --backlog --issues PROJ-110
   ```

### Epic Forecasting

1. Get epic story point totals:
   ```bash
   python get_estimates.py --epic PROJ-100
   ```

2. Calculate sprints needed:
   ```
   Remaining Points / Average Velocity = Sprints Required
   ```

## See Also

- [Sprint Lifecycle](sprint-lifecycle.md) - View sprint progress
- [Epic Management](epic-management.md) - Epic-level estimation
- [Best Practices](../docs/BEST_PRACTICES.md#story-point-estimation) - Estimation guidance
