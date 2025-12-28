# Sprint Lifecycle Examples

Detailed examples for creating, managing, and closing sprints.

## Creating Sprints

```bash
# Create basic sprint
python create_sprint.py --board 123 --name "Sprint 42"

# Create sprint with dates
python create_sprint.py --board 123 --name "Sprint 42" \
  --start 2025-01-20 --end 2025-02-03

# Create sprint with goal
python create_sprint.py --board 123 --name "Sprint 42" \
  --goal "Launch MVP" --start 2025-01-20 --end 2025-02-03

# Create sprint and output as JSON
python create_sprint.py --board 123 --name "Sprint 42" --output json
```

## Managing Sprint Lifecycle

```bash
# Start a sprint
python manage_sprint.py --sprint 456 --start

# Close a sprint
python manage_sprint.py --sprint 456 --close

# Close and move incomplete issues to next sprint
python manage_sprint.py --sprint 456 --close --move-incomplete-to 457

# Update sprint goal
python manage_sprint.py --sprint 456 --goal "Updated goal: Ship v2.0"

# Get active sprint for a board
python manage_sprint.py --board 123 --get-active
```

## Moving Issues to Sprints

```bash
# Move single issue to sprint
python move_to_sprint.py --sprint 456 --issues PROJ-101

# Move multiple issues
python move_to_sprint.py --sprint 456 --issues PROJ-101,PROJ-102,PROJ-103

# Move issues matching JQL query
python move_to_sprint.py --sprint 456 --jql "project=PROJ AND status='To Do'"

# Preview changes without making them
python move_to_sprint.py --sprint 456 --issues PROJ-101,PROJ-102 --dry-run

# Move issues to top of sprint backlog
python move_to_sprint.py --sprint 456 --issues PROJ-101 --rank top

# Remove issues from sprint (move to backlog)
python move_to_sprint.py --backlog --issues PROJ-101
```

## Viewing Sprint Details

```bash
# Get basic sprint info
python get_sprint.py 456

# Get sprint with issues and progress
python get_sprint.py 456 --with-issues

# Get active sprint for a board
python get_sprint.py --board 123 --active

# Export sprint data as JSON
python get_sprint.py 456 --with-issues --output json
```

### Example Output

```
Sprint: Sprint 42
State: active
Dates: 2025-01-20 -> 2025-02-03 (10 days remaining)
Goal: Launch MVP
Progress: 15/25 issues (60%)
Story Points: 32/55 (58%)

Issues:
  [Done] PROJ-101 - User auth (5 pts)
  [In Progress] PROJ-102 - Dashboard (8 pts)
  [To Do] PROJ-103 - Settings (3 pts)
  ...
```

## Common Workflows

### Sprint Planning Session

1. Create the sprint:
   ```bash
   python create_sprint.py --board 123 --name "Sprint 42" \
     --start 2025-01-20 --end 2025-02-03 \
     --goal "Launch user authentication MVP"
   ```

2. Add high-priority items to sprint:
   ```bash
   python move_to_sprint.py --sprint 456 \
     --jql "project=PROJ AND status='To Do' AND priority IN (High, Highest)" \
     --rank top --dry-run
   ```

3. Review and confirm:
   ```bash
   python get_sprint.py 456 --with-issues
   ```

4. Start the sprint:
   ```bash
   python manage_sprint.py --sprint 456 --start
   ```

### Sprint Close and Carryover

1. Review sprint status:
   ```bash
   python get_sprint.py 456 --with-issues
   ```

2. Close sprint and move incomplete work:
   ```bash
   python manage_sprint.py --sprint 456 --close --move-incomplete-to 457
   ```

## See Also

- [Epic Management](epic-management.md) - Add sprint issues to epics
- [Backlog Management](backlog-management.md) - Move issues from backlog
- [Best Practices](../docs/BEST_PRACTICES.md#sprint-planning) - Sprint planning guidance
