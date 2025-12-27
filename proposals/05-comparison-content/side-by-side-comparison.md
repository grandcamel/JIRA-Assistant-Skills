# Side-by-Side Comparison Examples (Option 5A)

These markdown blocks are ready to embed directly into the README. Each example showcases the dramatic difference between traditional approaches and natural language with JIRA Assistant Skills.

---

## Comparison 1: Finding Sprint Work

<table>
<tr>
<td width="50%">

### The Traditional Way

**JQL Query:**
```jql
project = PROJ AND
status IN ("To Do", "In Progress") AND
assignee = currentUser() AND
sprint IN openSprints() AND
priority IN (High, Highest)
ORDER BY priority DESC, created ASC
```

**CLI Command:**
```bash
python jql_search.py \
  "project = PROJ AND status IN ('To Do', 'In Progress') \
   AND assignee = currentUser() AND sprint IN openSprints() \
   AND priority IN (High, Highest) ORDER BY priority DESC" \
  --fields summary,priority,status \
  --max-results 50
```

*Requires memorizing syntax, operators, and field names.*

</td>
<td width="50%">

### The JIRA Assistant Way

```
"Show my high priority sprint work"
```

Claude interprets intent, builds the query, selects fields, and formats output automatically.

**Result:**
```
Found 8 issues in active sprint:

PROJ-456 [Highest] Login timeout fix
PROJ-423 [High] API rate limiting
PROJ-412 [High] Dashboard performance
...
```

*Just describe what you need.*

</td>
</tr>
</table>

---

## Comparison 2: Sprint Planning

<table>
<tr>
<td width="50%">

### The Traditional Way

**Step 1:** Create sprint
```bash
python create_sprint.py \
  --board 123 \
  --name "Sprint 23" \
  --goal "Payment System v2" \
  --start 2025-01-20 \
  --end 2025-02-03
```

**Step 2:** Find candidate issues
```bash
python jql_search.py \
  "project = PROJ AND status = 'Backlog' \
   AND priority IN (High, Highest) \
   AND labels = payment" \
  --fields key,summary,customfield_10016
```

**Step 3:** Move issues to sprint
```bash
python move_to_sprint.py \
  --sprint 456 \
  --issues PROJ-101,PROJ-102,PROJ-103,PROJ-104
```

**Step 4:** Check capacity
```bash
python get_estimates.py --sprint 456
```

*Multiple commands, manual coordination, easy to forget steps.*

</td>
<td width="50%">

### The JIRA Assistant Way

```
"Plan Sprint 23 for the payment system
 with our top priority backlog items"
```

Claude handles the complete workflow:

```
Created Sprint 23 on Board 123
Goal: Payment System v2
Dates: Jan 20 - Feb 3

Analyzed velocity: avg 42 points (last 3 sprints)
Selected 8 issues totaling 38 points:
  PROJ-101 [8 pts] Payment gateway integration
  PROJ-102 [5 pts] Refund processing
  PROJ-103 [5 pts] Transaction history
  ...

Capacity: 38/42 points (90%)
Buffer available for unplanned work.

Note: PROJ-105 has external dependency on API team
```

*One conversation, complete visibility.*

</td>
</tr>
</table>

---

## Comparison 3: Bulk Issue Transitions

<table>
<tr>
<td width="50%">

### The Traditional Way

**Option A: JIRA UI**
1. Open advanced search
2. Enter JQL filter
3. Select all matching issues
4. Click "Bulk Change"
5. Select transition
6. Add resolution
7. Confirm
8. Wait for processing
9. Review results

*9 steps, 3-5 minutes, no preview*

**Option B: Script**
```bash
python bulk_transition.py \
  --jql "project = PROJ AND sprint = 456 \
         AND status = 'Resolved'" \
  --to "Done" \
  --resolution "Fixed" \
  --dry-run
# Review output, then run again without --dry-run
```

*Must remember flag syntax and run twice.*

</td>
<td width="50%">

### The JIRA Assistant Way

```
"Close all resolved issues from
 Sprint 23 as Fixed"
```

Claude provides preview and confirmation:

```
Found 23 issues to transition:
  PROJ-101 Resolved -> Done (Fixed)
  PROJ-102 Resolved -> Done (Fixed)
  PROJ-103 Resolved -> Done (Fixed)
  ...

Proceed with transition? (yes/no)
> yes

Transitioned 23 issues successfully.
```

*Preview built-in, confirmation automatic.*

</td>
</tr>
</table>

---

## Comparison 4: Incident Response

<table>
<tr>
<td width="50%">

### The Traditional Way

**Step 1:** Create JSM ticket
```bash
python create_request.py \
  --service-desk 1 \
  --request-type "Incident" \
  --summary "Payment processing failing" \
  --priority Critical
```

**Step 2:** Search for related issues
```bash
python jql_search.py \
  "project = PLATFORM AND \
   text ~ 'payment' AND \
   created >= -30d" \
  --max-results 20
```

**Step 3:** Link related issues
```bash
python link_issue.py INC-789 --relates-to PROJ-234
python link_issue.py INC-789 --relates-to PROJ-567
```

**Step 4:** Check SLA
```bash
python get_sla.py INC-789
```

*4+ commands, context switching, manual correlation.*

</td>
<td width="50%">

### The JIRA Assistant Way

```
"P1 incident: Payment processing is failing
 in production"
```

Claude orchestrates the complete response:

```
Created Incident INC-789 (Critical)
SLA: 1-hour response, 4-hour resolution

Linked related issues:
  PROJ-234: Payment timeout errors (closed 2w ago)
  PROJ-567: Database connection pool (open, @jane)
  INC-456: Similar incident last month

Historical match found:
  INC-456 root cause: Redis memory pressure
  Suggested action: Check Redis cluster health

Notified: @oncall-payments
```

*Complete context, intelligent correlation.*

</td>
</tr>
</table>

---

## Comparison 5: Daily Standup Preparation

<table>
<tr>
<td width="50%">

### The Traditional Way

**Query 1:** Yesterday's work
```bash
python jql_search.py \
  "assignee = currentUser() AND \
   updated >= -1d AND \
   status changed DURING (-1d, now())" \
  --fields summary,status
```

**Query 2:** Today's work
```bash
python jql_search.py \
  "assignee = currentUser() AND \
   sprint IN openSprints() AND \
   status != Done" \
  --fields summary,status,priority
```

**Query 3:** Blockers
```bash
python jql_search.py \
  "assignee = currentUser() AND \
   status = Blocked"
```

*3 queries, manual assembly, 2+ minutes.*

</td>
<td width="50%">

### The JIRA Assistant Way

```
"Prep my standup: what did I do yesterday,
 what's on my plate today, any blockers?"
```

Claude provides a ready-to-share summary:

```
Yesterday:
- Completed PROJ-456: Login timeout fix
- Moved PROJ-423 to Review
- Added 2 comments on PROJ-412

Today (5 items, 18 story points):
- PROJ-423: API rate limiting (In Review)
- PROJ-412: Dashboard performance (In Progress)
- PROJ-489: Error handling (To Do)
- PROJ-492: Logging improvements (To Do)
- PROJ-495: Cache layer (To Do)

Blockers:
- PROJ-412 waiting on DevOps for metrics access

Estimated capacity: 6 hours available
```

*Complete standup prep in seconds.*

</td>
</tr>
</table>

---

## Comparison 6: Export and Reporting

<table>
<tr>
<td width="50%">

### The Traditional Way

```bash
# Export large dataset
python streaming_export.py \
  "project = PROJ AND \
   created >= 2025-01-01 AND \
   created < 2025-04-01" \
  --output q1-2025.csv \
  --fields key,summary,status,priority,\
           assignee,reporter,created,resolved \
  --enable-checkpoint \
  --page-size 200

# If interrupted, check checkpoints
python streaming_export.py --list-checkpoints

# Resume if needed
python streaming_export.py \
  --resume export-20250115-143022
```

*Complex flags, manual checkpoint management.*

</td>
<td width="50%">

### The JIRA Assistant Way

```
"Export all Q1 2025 issues to CSV
 for the quarterly report"
```

Claude handles the details:

```
Exporting 2,847 issues from Q1 2025...
Progress: [====================] 100%

Saved to: q1-2025-report.csv
Fields: key, summary, status, priority,
        assignee, reporter, created, resolved

Summary:
- Total issues: 2,847
- Resolved: 2,156 (76%)
- Avg resolution time: 4.2 days
```

*Automatic field selection, progress tracking.*

</td>
</tr>
</table>

---

## Usage Notes

1. **Embedding in README:** Copy any comparison block (including the `<table>` tags) directly into your README.md

2. **Customization:** Replace `PROJ`, board IDs, and sprint numbers with your actual values for documentation

3. **Tone:** These comparisons highlight efficiency gains without disparaging the traditional approach - power users who prefer JQL can still use it directly

4. **Accuracy:** All CLI commands shown are actual commands from the JIRA Assistant Skills scripts

5. **Rendering:** The side-by-side format renders correctly on GitHub, GitLab, and most markdown viewers
