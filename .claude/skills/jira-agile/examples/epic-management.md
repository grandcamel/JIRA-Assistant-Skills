# Epic Management Examples

Detailed examples for creating epics, linking issues, and tracking epic progress.

## Creating Epics

```bash
# Create basic epic
python create_epic.py --project PROJ --summary "Mobile App MVP"

# Create epic with Epic Name and color
python create_epic.py --project PROJ --summary "Mobile App MVP" \
  --epic-name "MVP" --color blue

# Create epic with full details
python create_epic.py --project PROJ \
  --summary "Mobile App MVP" \
  --description "## Goal\nDeliver MVP by Q2" \
  --epic-name "MVP" \
  --color blue \
  --assignee self \
  --priority High

# Create epic and output as JSON
python create_epic.py --project PROJ --summary "Mobile App MVP" --output json
```

## Managing Epic Relationships

```bash
# Add single issue to epic
python add_to_epic.py --epic PROJ-100 --issues PROJ-101

# Add multiple issues to epic
python add_to_epic.py --epic PROJ-100 --issues PROJ-101,PROJ-102,PROJ-103

# Add issues via JQL query
python add_to_epic.py --epic PROJ-100 --jql "project=PROJ AND status='To Do'"

# Preview changes without making them
python add_to_epic.py --epic PROJ-100 --issues PROJ-101,PROJ-102 --dry-run

# Remove issue from epic
python add_to_epic.py --remove --issues PROJ-101
```

## Viewing Epic Progress

```bash
# Get basic epic info
python get_epic.py PROJ-100

# Get epic with all children and progress
python get_epic.py PROJ-100 --with-children

# Export epic data as JSON
python get_epic.py PROJ-100 --with-children --output json
```

### Example Output

```
Epic: PROJ-100
Summary: Mobile App MVP
Epic Name: MVP
Status: In Progress
Progress: 12/20 issues (60%)
Story Points: 45/80 (56%)

Children:
  PROJ-101 [Done] - User authentication
  PROJ-102 [In Progress] - Dashboard layout
  PROJ-103 [To Do] - Profile settings
  ...
```

## Common Workflows

### Epic-Driven Development

1. Create epic for large feature:
   ```bash
   python create_epic.py --project PROJ --summary "User Management" --epic-name "Auth"
   ```

2. Create stories and tasks (using jira-issue skill)

3. Link issues to the epic:
   ```bash
   python add_to_epic.py --epic PROJ-100 --jql "project=PROJ AND labels=auth"
   ```

4. Break down complex stories into subtasks:
   ```bash
   python create_subtask.py --parent PROJ-101 --summary "API endpoints"
   python create_subtask.py --parent PROJ-101 --summary "Database schema"
   python create_subtask.py --parent PROJ-101 --summary "Unit tests"
   ```

5. Track epic progress regularly:
   ```bash
   python get_epic.py PROJ-100 --with-children
   ```

## See Also

- [Sprint Lifecycle](sprint-lifecycle.md) - Add epic issues to sprints
- [Estimation](estimation.md) - Estimate story points for epic planning
- [Field Reference](../docs/FIELD_REFERENCE.md) - Epic custom field IDs
