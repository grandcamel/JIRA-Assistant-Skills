# jira-agile

Agile and Scrum workflow management for JIRA - epics, sprints, backlogs, and story points.

## When to use this skill

Use this skill when you need to:
- Create and manage epics for organizing large features
- Link issues to epics for hierarchical planning
- Create subtasks under parent issues
- Track epic progress and story point completion
- Organize work using Agile/Scrum methodologies

## What this skill does

This skill provides comprehensive Agile/Scrum workflow operations:

### 1. Epic Management

**Create Epics**: Create epic issues with Agile-specific fields:
- Epic Name field (customfield_10011)
- Epic Color for visual organization
- Summary and description (supports Markdown via ADF conversion)
- Standard issue fields (priority, assignee, labels)

**Add Issues to Epics**: Link stories and tasks to epics:
- Single or bulk operations
- Add by issue keys or JQL query
- Remove issues from epics
- Dry-run mode for previewing changes
- Individual failure tracking for bulk operations

**Get Epic Details**: Retrieve epic information with progress tracking:
- Basic epic metadata (summary, status, Epic Name, color)
- List all child issues
- Calculate progress percentage (done/total issues)
- Sum story points (completed/total)
- Text and JSON output formats

### 2. Subtask Management

**Create Subtasks**: Create subtask issues linked to parent issues:
- Automatic project inheritance from parent
- Validates parent can have subtasks (no sub-subtasks)
- Time estimate tracking (originalEstimate field)
- Description with Markdown support
- Standard fields (assignee, priority, labels)

## Available scripts

### Epic Management
- `create_epic.py` - Create new epic issues with Epic Name and Color
- `add_to_epic.py` - Add or remove issues from epics (bulk operations supported)
- `get_epic.py` - Retrieve epic details with progress and story point calculations

### Subtask Management
- `create_subtask.py` - Create subtasks linked to parent issues

## Usage Examples

### Creating Epics

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
```

### Managing Epic Relationships

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

### Viewing Epic Progress

```bash
# Get basic epic info
python get_epic.py PROJ-100

# Get epic with all children and progress
python get_epic.py PROJ-100 --with-children

# Export epic data as JSON
python get_epic.py PROJ-100 --with-children --output json
```

Example output:
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

### Creating Subtasks

```bash
# Create basic subtask
python create_subtask.py --parent PROJ-101 --summary "Implement login API"

# Create subtask with assignee
python create_subtask.py --parent PROJ-101 \
  --summary "Write unit tests" \
  --assignee self

# Create subtask with time estimate
python create_subtask.py --parent PROJ-101 \
  --summary "Code review" \
  --estimate 2h \
  --priority High

# Create subtask with full details
python create_subtask.py --parent PROJ-101 \
  --summary "Implement JWT authentication" \
  --description "## Requirements\n- Use RS256 algorithm\n- 1 hour expiry" \
  --assignee self \
  --estimate 4h \
  --priority High
```

## Custom Field IDs

The following custom field IDs are commonly used in JIRA Cloud but may vary per instance:

- **Epic Name**: `customfield_10011`
- **Epic Color**: `customfield_10012`
- **Epic Link**: `customfield_10014` (links issues to epics)
- **Story Points**: `customfield_10016`

If your JIRA instance uses different field IDs, you can:
1. Check your instance's field configuration at: `https://your-domain.atlassian.net/rest/api/3/field`
2. Update the field IDs in the script source code
3. Use `--custom-fields` parameter to pass additional fields as JSON

## Integration with Other Skills

### jira-issue skill
- Use `create_issue.py` for creating standard issues (Stories, Tasks, Bugs)
- Then use `add_to_epic.py` to link them to epics
- Use `get_issue.py` to view issue details including parent/subtask relationships

### jira-search skill
- Use `jql_search.py` to find issues for bulk epic operations
- Example: `jql_search.py "project=PROJ AND Sprint=42"` then pipe to `add_to_epic.py`

### jira-lifecycle skill
- Use `transition_issue.py` to move epic children through workflow states
- Progress calculations in `get_epic.py` reflect current status of all children

## Notes

- All scripts support the `--profile` flag for managing multiple JIRA instances
- Descriptions support Markdown which is automatically converted to Atlassian Document Format (ADF)
- Epic operations validate issue types (e.g., subtasks cannot have subtasks)
- Bulk operations include individual failure tracking rather than failing completely
- Dry-run modes are available for preview before making changes

## Common Workflows

### Epic-Driven Development

1. Create epic for large feature:
   ```bash
   python create_epic.py --project PROJ --summary "User Management" --epic-name "Auth"
   ```

2. Create stories and tasks for the epic (using jira-issue skill)

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

### Sprint Planning

1. Create epic for sprint goal
2. Add issues to epic using JQL:
   ```bash
   python add_to_epic.py --epic PROJ-200 --jql "Sprint=42"
   ```
3. Monitor progress during sprint:
   ```bash
   python get_epic.py PROJ-200 --with-children
   ```

## Troubleshooting

### "Epic Link field not found"
- Custom field IDs vary by JIRA instance
- Check your instance's epic link field ID and update EPIC_LINK_FIELD constant in script

### "Issue type 'Epic' not found"
- Ensure your project has Epic issue type enabled
- Check project settings → Issue Types

### "Subtask cannot have subtasks"
- JIRA enforces a one-level hierarchy for subtasks
- Use epics for multi-level organization instead

### Story points not showing
- Ensure Story Points field exists in your JIRA instance
- Check STORY_POINTS_FIELD constant matches your field ID
