---
name: jira-discover-project
description: Discover JIRA project context for intelligent defaults and workflow understanding
---

# JIRA Project Discovery

You are helping the user discover and configure JIRA project context. This context enables intelligent defaults when creating issues and understanding workflows.

## What Gets Discovered

- **Metadata**: Issue types, components, versions, priorities, assignable users
- **Workflows**: Valid status transitions for each issue type
- **Patterns**: Common assignees, labels, priorities based on recent activity
- **Defaults**: Auto-generated sensible defaults based on patterns

## Step 1: Get Project Key

Ask the user which project they want to configure:

"Which JIRA project would you like to discover context for? Please provide the project key (e.g., PROJ, DEV, MYAPP)."

If the user provides multiple projects, handle them one at a time.

## Step 2: Confirm Profile

Check which JIRA profile to use:

"Which JIRA profile should I use for discovery?"

Options:
1. Use the default profile (check `JIRA_PROFILE` env var or config)
2. Specify a profile name (development, production, etc.)

## Step 3: Run Discovery

Run the discovery script:

```bash
python .claude/skills/jira-ops/scripts/discover_project.py {PROJECT_KEY} --profile {profile}
```

Wait for the script to complete and capture the output.

## Step 4: Review Results

After discovery completes, summarize what was found:

**For the user, display:**
- Number of issue types found
- Number of components found
- Number of active versions
- Top 5 assignees by activity
- Most common labels
- Sample size and period

Example output:
```
Discovery complete for PROJ!

Discovered:
- 6 issue types: Bug, Story, Task, Epic, Subtask, Improvement
- 8 components: Backend, Frontend, API, Database, CI/CD, Docs, Testing, UX
- 3 active versions: v2.1.0, v2.2.0, v3.0.0-beta

Patterns (last 30 days, 85 issues sampled):
- Top assignees: John Doe (35%), Jane Smith (28%), Bob Wilson (15%)
- Common labels: backend, needs-review, urgent, regression
- Priority distribution: High (45%), Medium (35%), Low (20%)

Defaults generated based on patterns.
```

## Step 5: Storage Decision

Ask the user how they want to store the context:

"How would you like to store this project context?

1. **Shared (Recommended)**: Save to `.claude/skills/jira-project-{PROJECT_KEY}/`
   - Can be committed to your repo and shared with your team
   - Already saved by the discovery script

2. **Personal only**: Save to `.claude/settings.local.json`
   - Private to you (gitignored)
   - Use if you want different defaults than your team

3. **Both**: Save to both locations
   - Shared context with personal overrides"

If they choose personal or both, run:
```bash
python .claude/skills/jira-ops/scripts/discover_project.py {PROJECT_KEY} --personal --profile {profile}
```

## Step 6: Customize Defaults (Optional)

Ask if they want to customize the auto-generated defaults:

"The discovery script generated default values based on your team's patterns. Would you like to customize any defaults?

For example:
- Set a default priority for Bug issues
- Set a default assignee for Story issues
- Add default labels for all issues"

If yes, help them edit the `defaults.json` file in the skill directory:

```bash
# Show current defaults
cat .claude/skills/jira-project-{PROJECT_KEY}/defaults.json
```

Then help them modify the file with their preferred values.

## Step 7: Confirm Success

Summarize what was created:

"Project context for {PROJECT_KEY} is now configured!

Created:
- `.claude/skills/jira-project-{PROJECT_KEY}/SKILL.md` - Skill documentation
- `.claude/skills/jira-project-{PROJECT_KEY}/context/metadata.json` - Issue types, components, versions
- `.claude/skills/jira-project-{PROJECT_KEY}/context/workflows.json` - Status transitions
- `.claude/skills/jira-project-{PROJECT_KEY}/context/patterns.json` - Usage patterns
- `.claude/skills/jira-project-{PROJECT_KEY}/defaults.json` - Default values

**Next steps:**
1. Review and customize `defaults.json` as needed
2. Commit the skill directory to share with your team
3. When creating issues, I'll automatically use these defaults

To refresh the context later, run:
```
/jira-discover-project
```
or
```bash
python .claude/skills/jira-ops/scripts/discover_project.py {PROJECT_KEY}
```"

## Troubleshooting

**"Profile not found" error:**
- Check available profiles with `python .claude/skills/jira-ops/scripts/cache_status.py --list-profiles`
- Ensure JIRA credentials are configured (run `/jira-assistant-setup` if needed)

**"Project not found" error:**
- Verify the project key is correct (case-sensitive, usually uppercase)
- Ensure you have permission to access the project

**Empty patterns:**
- If there are no recent issues, patterns will be empty
- Try increasing the sample period: `--days 60` or `--days 90`

**Rate limiting:**
- The discovery makes multiple API calls
- If rate limited, wait a few minutes and try again
