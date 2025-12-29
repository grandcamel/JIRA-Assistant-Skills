---
description: "Get detailed information about a specific JIRA skill"
arguments:
  - name: skill_name
    description: "Name of the skill to get info about (e.g., jira-issue, jira-agile)"
    required: true
---

# Skill Info: $ARGUMENTS

Get detailed information about the **$ARGUMENTS** skill.

## Instructions

1. Read the SKILL.md file for the requested skill from `.claude/skills/$ARGUMENTS/SKILL.md`
2. Present a summary including:
   - Full description
   - When to use this skill
   - Available scripts/commands
   - Example usage
   - Configuration requirements

## Skill Locations

Skills are located at:
- `.claude/skills/jira-issue/SKILL.md`
- `.claude/skills/jira-lifecycle/SKILL.md`
- `.claude/skills/jira-search/SKILL.md`
- `.claude/skills/jira-collaborate/SKILL.md`
- `.claude/skills/jira-relationships/SKILL.md`
- `.claude/skills/jira-agile/SKILL.md`
- `.claude/skills/jira-time/SKILL.md`
- `.claude/skills/jira-bulk/SKILL.md`
- `.claude/skills/jira-dev/SKILL.md`
- `.claude/skills/jira-fields/SKILL.md`
- `.claude/skills/jira-ops/SKILL.md`
- `.claude/skills/jira-admin/SKILL.md`
- `.claude/skills/jira-jsm/SKILL.md`
- `.claude/skills/jira-assistant/SKILL.md`

## Output

Present the skill information in a clear, readable format with sections for:
- **Description**: What this skill does
- **When to Use**: Trigger conditions
- **Key Features**: Main capabilities
- **Example Commands**: How to use it
- **Related Skills**: Other skills that work well together
