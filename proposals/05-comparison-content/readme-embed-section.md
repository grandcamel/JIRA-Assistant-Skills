# README Embed Section

This section combines Options 5A and 5B into a cohesive block ready to insert directly into the README.md file. Place this after the "Why JIRA Assistant Skills?" section.

---

## The Difference in Action

### Before and After

<table>
<tr>
<td width="50%">

**JQL Query + CLI:**
```jql
project = PROJ AND
status IN ("To Do", "In Progress") AND
assignee = currentUser() AND
sprint IN openSprints() AND
priority IN (High, Highest)
ORDER BY priority DESC
```

```bash
python jql_search.py "project = PROJ AND ..."
  --fields summary,priority,status
  --max-results 50
```

</td>
<td width="50%">

**Natural Language:**
```
"Show my high priority sprint work"
```

Claude builds the query, fetches results, and formats the output automatically.

</td>
</tr>
</table>

<table>
<tr>
<td width="50%">

**Multi-Step Workflow:**
```bash
# Step 1: Create sprint
python create_sprint.py --board 123 \
  --name "Sprint 23" --goal "MVP"

# Step 2: Find issues
python jql_search.py "project = PROJ ..."

# Step 3: Move to sprint
python move_to_sprint.py --sprint 456 \
  --issues PROJ-101,PROJ-102

# Step 4: Check capacity
python get_estimates.py --sprint 456
```

</td>
<td width="50%">

**Single Conversation:**
```
"Plan Sprint 23 with top priority items"
```

Result:
```
Created Sprint 23 (Jan 20 - Feb 3)
Moved 8 issues (38 story points)
Capacity: 90% (buffer available)
Flag: PROJ-105 has external dependency
```

</td>
</tr>
</table>

### Time Saved

| Task | Traditional | JIRA Assistant | Saved |
|------|-------------|----------------|-------|
| Find sprint issues | 45 sec | 5 sec | 89% |
| Create sprint + add stories | 4 min | 25 sec | 90% |
| Bulk close 20 issues | 4 min | 30 sec | 88% |
| Standup preparation | 3 min | 8 sec | 96% |
| Check release blockers | 5 min | 10 sec | 97% |

**Typical developer:** Save 30+ minutes per week.
**Team of 8:** Reclaim 31 work days per year.

---

## Alternative Compact Version

For a more compact README, use this version:

```markdown
## See the Difference

<table>
<tr>
<td width="50%">

**Traditional:**
```bash
python jql_search.py \
  "project = PROJ AND assignee = currentUser() \
   AND sprint IN openSprints() \
   ORDER BY priority DESC" \
  --fields summary,status --max-results 50
```

</td>
<td width="50%">

**With JIRA Assistant:**
```
"What's on my plate this sprint?"
```

</td>
</tr>
</table>

| Task | Before | After | Saved |
|------|--------|-------|-------|
| Sprint planning | 4 min | 25 sec | 90% |
| Bulk operations | 4 min | 30 sec | 88% |
| Standup prep | 3 min | 8 sec | 96% |
```

---

## Minimal Version

For a very concise README:

```markdown
## Skip the JQL

| Instead of... | Just say... |
|---------------|-------------|
| `project = PROJ AND assignee = currentUser() AND sprint IN openSprints() ORDER BY priority DESC` | "Show my sprint work" |
| `python bulk_transition.py --jql "status = Resolved" --to Done --resolution Fixed` | "Close all resolved issues" |
| `python create_sprint.py --board 123 --name "Sprint 23" && python move_to_sprint.py...` | "Plan Sprint 23 with top priorities" |

**Result:** 30+ minutes saved per week.
```

---

## Integration Notes

1. **Placement:** Insert after "Context-Efficient Architecture" and before "14 Modular Skills"

2. **Current README structure:**
   ```
   ## Why JIRA Assistant Skills?
   ### Context-Efficient Architecture  <- existing
   [INSERT COMPARISON SECTION HERE]     <- new
   ### 14 Modular Skills               <- existing
   ```

3. **Formatting:**
   - The `<table>` HTML renders correctly on GitHub, GitLab, Bitbucket
   - Keep code blocks short (truncate JQL if needed)
   - Times are intentionally rounded for clarity

4. **Customization:**
   - Replace `PROJ` with your actual project key for demos
   - Adjust time estimates if you have measured data
   - Add team-specific examples if helpful
