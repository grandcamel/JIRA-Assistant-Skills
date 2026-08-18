---
name: jira-discover-project
description: Discover JIRA project context for intelligent defaults and usage patterns
---

# JIRA Project Discovery

You are helping the user discover and configure JIRA project context. This context enables intelligent defaults when creating issues.

## What Gets Discovered

- **Metadata**: Issue types, components, versions, priorities, assignable users
- **Patterns**: Top assignees, common labels, and per-issue-type breakdowns based on recent activity
- **Field usage**: Per-field fill rates and value distributions (issue type, status, priority) from sampled issues
- **Hierarchy**: Parent hierarchy usage (how often sampled issues have a parent)

## Step 1: Get Project Key

Ask the user which project they want to configure:

"Which JIRA project would you like to discover context for? Please provide the project key (e.g., PROJ, DEV, MYAPP)."

If the user provides multiple projects, handle them one at a time.

## Step 2: Run Discovery

Run discovery with the `jira-as` CLI (credentials come from the environment or settings — run `/jira-assistant-setup` first if not configured):

```bash
jira-as ops discover-project {PROJECT_KEY}
```

Useful options:

| Option | Description |
|--------|-------------|
| `-s, --sample-size N` | Number of issues to sample for patterns |
| `-d, --days N` | Sample period in days |
| `-o, --output [text\|json]` | Output format (`json` returns the full discovery data) |
| `-v, --verbose` | Verbose output |

The command prints everything to stdout — it does not write any files. Capture the output.

## Step 3: Review Results

After discovery completes, summarize what was found:

**For the user, display:**
- Number of issue types found
- Number of components found
- Number of versions
- Top assignees by activity
- Most common labels
- Field fill rates and value distributions worth noting
- Parent hierarchy usage
- Sample size and period

Example output:
```
Discovery complete for PROJ!

Discovered:
- 6 issue types: Bug, Story, Task, Epic, Subtask, Improvement
- 8 components: Backend, Frontend, API, Database, CI/CD, Docs, Testing, UX
- 3 versions: v2.1.0, v2.2.0, v3.0.0-beta

Patterns (last 30 days, 85 issues sampled):
- Top assignees: John Doe (35%), Jane Smith (28%), Bob Wilson (15%)
- Common labels: backend, needs-review, urgent, regression
- Priority distribution: High (45%), Medium (35%), Low (20%)
- Field fill rates: description 60%, components 40%, duedate 5%
- Parent hierarchy: 20% of sampled issues have a parent
```

## Step 4: Save the Context (Optional)

The CLI only prints to stdout, so ask the user whether they want to save the discovery data:

"Would you like to save this project context for reuse?

1. **Shared (Recommended)**: Save to `.claude/jira-project-{PROJECT_KEY}/context.json`
   - Can be committed to your repo and shared with your team

2. **Personal only**: Save somewhere gitignored (e.g., your local notes)
   - Use if you want different defaults than your team

3. **No**: Just use the results in this conversation"

To save, re-run discovery with JSON output and redirect it:

```bash
mkdir -p .claude/jira-project-{PROJECT_KEY}
jira-as ops discover-project {PROJECT_KEY} -o json > .claude/jira-project-{PROJECT_KEY}/context.json
```

## Step 5: Customize Defaults (Optional)

Ask if they want to derive default values from the discovered patterns:

"Based on your team's patterns, I can suggest default values for issue creation. Would you like to set any defaults?

For example:
- Set a default priority for Bug issues
- Set a default assignee for Story issues
- Add default labels for all issues"

If yes, help them write a `defaults.json` in the project context directory based on the discovered patterns (most common priority, top assignee, frequent labels), then review it together:

```bash
# Show current defaults
cat .claude/jira-project-{PROJECT_KEY}/defaults.json
```

## Step 6: Confirm Success

Summarize what was created:

"Project context for {PROJECT_KEY} is now configured!

Created (if saved):
- `.claude/jira-project-{PROJECT_KEY}/context.json` - Full discovery data (metadata, patterns, field fill rates, distributions, parent hierarchy)
- `.claude/jira-project-{PROJECT_KEY}/defaults.json` - Default values (if customized)

**Next steps:**
1. Review and customize `defaults.json` as needed
2. Commit the context directory to share with your team
3. When creating issues, I'll automatically use these defaults

To refresh the context later, run:
```
/jira-discover-project
```
or run `jira-as ops discover-project {PROJECT_KEY}` directly."

## Troubleshooting

**Authentication errors:**
- Ensure JIRA credentials are configured (run `/jira-assistant-setup` if needed)
- Check environment variables: `JIRA_SITE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`

**"Project not found" error:**
- Verify the project key is correct (case-sensitive, usually uppercase)
- Ensure you have permission to access the project

**Empty patterns:**
- If there are no recent issues, patterns will be empty
- Try increasing the sample period: `--days 60` or `--days 90`

**Rate limiting:**
- The discovery makes multiple API calls
- If rate limited, wait a few minutes and try again
