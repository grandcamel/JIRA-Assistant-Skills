# Skill Selection Guide

When to use jira-agile vs other JIRA skills.

## Decision Matrix

| Task | Primary Skill | When to Use |
|------|---------------|-------------|
| Create story/task/bug | **jira-issue** | Always for individual issues |
| Create epic | **jira-agile** | For organizing multiple stories |
| Add story to epic | **jira-agile** | After creating story with jira-issue |
| Create subtask | **jira-agile** | For breaking down stories |
| Transition issue status | **jira-lifecycle** | For workflow state changes |
| Search by JQL | **jira-search** | For finding issues across project |
| Add comment | **jira-collaborate** | For issue discussions |
| Log time | **jira-time** | For worklog entries |
| Discover field IDs | **jira-fields** | For custom field configuration |

## Use jira-agile When

- Creating epics to organize large features
- Adding issues to epics for hierarchical planning
- Creating and managing sprints on Scrum boards
- Setting story points for estimation
- Ranking backlog items by priority
- Tracking epic and sprint progress
- Managing sprint lifecycle (start/close)
- Breaking down stories into subtasks

## Do NOT Use jira-agile When

| Scenario | Use Instead |
|----------|-------------|
| Creating individual stories/tasks | jira-issue |
| Searching issues by JQL | jira-search |
| Transitioning issues through workflow | jira-lifecycle |
| Managing time tracking/worklogs | jira-time |
| Discovering field configurations | jira-fields |
| Adding comments or attachments | jira-collaborate |
| Creating issue links (blocks, relates) | jira-relationships |

## Common Multi-Skill Workflows

### Epic-Driven Development

1. **jira-agile**: Create epic
2. **jira-issue**: Create stories for epic
3. **jira-agile**: Add stories to epic
4. **jira-agile**: Estimate with story points
5. **jira-agile**: Move to sprint
6. **jira-lifecycle**: Transition through workflow
7. **jira-agile**: Track epic progress

### Sprint Planning

1. **jira-search**: Find unestimated items
2. **jira-agile**: Estimate issues
3. **jira-agile**: Create sprint
4. **jira-agile**: Move issues to sprint
5. **jira-agile**: Start sprint

### Release Planning

1. **jira-agile**: Create epics for release
2. **jira-issue**: Create stories with fixVersion
3. **jira-search**: Find release items
4. **jira-agile**: Track epic progress

## See Also

- [SKILL.md](../SKILL.md) - jira-agile overview
- [jira-issue SKILL.md](../../jira-issue/SKILL.md)
- [jira-search SKILL.md](../../jira-search/SKILL.md)
- [jira-lifecycle SKILL.md](../../jira-lifecycle/SKILL.md)
