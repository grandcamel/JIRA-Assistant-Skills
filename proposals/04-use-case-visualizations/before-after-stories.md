# Before/After Narrative Visualizations

Real-world scenarios demonstrating time savings and workflow improvements with JIRA Assistant Skills.

---

## Story 1: The Monday Morning Standup

```
+-----------------------------------------------------------------------------+
| THE MONDAY MORNING STANDUP PROBLEM                                          |
+-----------------------------------------------------------------------------+

BEFORE: Sarah's Monday Routine                                    Total: 15 min
--------------------------------------------------------------------------------
1. Open browser, navigate to JIRA                                        2 min
2. Find the right board among 12 projects                                1 min
3. Filter by assignee (always forgets the syntax)                        3 min
4. Click each issue to check status and details                          5 min
5. Hunt for sprint velocity report                                       2 min
6. Copy issue keys to meeting notes                                      2 min

AFTER: Sarah's Monday with JIRA Assistant                         Total: 45 sec
--------------------------------------------------------------------------------

Sarah: "What's my sprint work and what did I complete yesterday?"

Claude: Here's your Sprint 42 status:

        IN PROGRESS (2)
        +----------------------------------------------------------+
        | PROJ-123  Implement user auth       3 pts   Due: Wed     |
        | PROJ-124  Fix login redirect        2 pts   Due: Thu     |
        +----------------------------------------------------------+

        COMPLETED YESTERDAY (2)
        +----------------------------------------------------------+
        | PROJ-120  Add password reset        2 pts   Done         |
        | PROJ-121  Update email templates    1 pts   Done         |
        +----------------------------------------------------------+

        Sprint Progress: 18/31 points (58%)
        Velocity: On track for completion

--------------------------------------------------------------------------------
TIME SAVED: 14 min per standup x 200 standups/year = 47 hours/year saved
+-----------------------------------------------------------------------------+
```

---

## Story 2: The Release Manager's Friday

```
+-----------------------------------------------------------------------------+
| RELEASE DAY CHAOS                                                           |
+-----------------------------------------------------------------------------+

BEFORE: Marcus's Release Check                                    Total: 45 min
--------------------------------------------------------------------------------
1. Search for all issues in fixVersion                                   5 min
2. Manually check each issue is in "Done" status                        15 min
3. Look for any blocking relationships                                   8 min
4. Generate release notes by copying from each issue                    12 min
5. Transition any stragglers to "Done"                                   5 min

AFTER: Marcus's Release with JIRA Assistant                        Total: 3 min
--------------------------------------------------------------------------------

Marcus: "Show me the release status for version 2.4.0"

Claude: Release 2.4.0 Status Report

        READY TO SHIP (47 issues)
        +----------------------------------------------------------+
        | 12 Features  |  28 Bug Fixes  |  7 Improvements          |
        +----------------------------------------------------------+

        BLOCKERS FOUND (2 issues)
        +----------------------------------------------------------+
        | PROJ-892  Blocked by: PROJ-891 (In Code Review)          |
        | PROJ-893  Blocked by: PROJ-890 (Waiting for QA)          |
        +----------------------------------------------------------+

        NOT DONE (3 issues)
        +----------------------------------------------------------+
        | PROJ-894  Status: In Progress   Assignee: @tom           |
        | PROJ-895  Status: In Review     Assignee: @jane          |
        | PROJ-896  Status: In Progress   Assignee: @tom           |
        +----------------------------------------------------------+

Marcus: "Generate release notes and export to CSV"

Claude: Release notes generated:

        v2.4.0 Release Notes
        ====================
        Features:
        - PROJ-800: New dashboard widgets
        - PROJ-812: Dark mode support
        ...

        CSV exported to: release-2.4.0-notes.csv

--------------------------------------------------------------------------------
TIME SAVED: 42 min per release x 12 releases/year = 8.4 hours/year saved
+-----------------------------------------------------------------------------+
```

---

## Story 3: The Sprint Planning Marathon

```
+-----------------------------------------------------------------------------+
| SPRINT PLANNING SIMPLIFIED                                                  |
+-----------------------------------------------------------------------------+

BEFORE: Team's Sprint Planning                                   Total: 90 min
--------------------------------------------------------------------------------
1. Create new sprint in board settings                                   3 min
2. Review backlog (endless scrolling)                                   20 min
3. Drag and drop stories one by one                                     25 min
4. Manually sum story points                                            10 min
5. Check for unestimated stories                                        15 min
6. Assign sprint to team members                                        12 min
7. Start sprint with goals                                               5 min

AFTER: Team's Sprint Planning                                    Total: 15 min
--------------------------------------------------------------------------------

Scrum Master: "Create Sprint 43 starting Monday for 2 weeks"

Claude: Sprint 43 created
        Start: Monday, Jan 6, 2025
        End: Friday, Jan 17, 2025
        Board: PROJ Main Board

Scrum Master: "Show unestimated stories in the backlog"

Claude: Found 4 unestimated stories:
        +----------------------------------------------------------+
        | PROJ-900  User profile page redesign                     |
        | PROJ-901  API rate limiting                              |
        | PROJ-902  Mobile responsive fixes                        |
        | PROJ-903  Password policy update                         |
        +----------------------------------------------------------+

        [Team estimates stories in discussion: 10 minutes]

Scrum Master: "Move top 12 backlog stories to Sprint 43"

Claude: Moved 12 stories to Sprint 43
        +----------------------------------------------------------+
        | Total Points: 34                                         |
        | Stories: 8 features, 3 bugs, 1 tech debt                 |
        | Team Velocity (avg): 32 points                           |
        | Capacity Check: Slightly over - consider removing 1      |
        +----------------------------------------------------------+

Scrum Master: "Start Sprint 43 with goal 'Complete auth redesign'"

Claude: Sprint 43 is now ACTIVE
        Goal: Complete auth redesign
        12 stories | 34 points | 2 weeks

--------------------------------------------------------------------------------
TIME SAVED: 75 min per sprint x 26 sprints/year = 32.5 hours/year saved
+-----------------------------------------------------------------------------+
```

---

## Story 4: The On-Call Incident

```
+-----------------------------------------------------------------------------+
| PRODUCTION INCIDENT RESPONSE                                                |
+-----------------------------------------------------------------------------+

BEFORE: Alex's Incident Workflow                                  Total: 12 min
--------------------------------------------------------------------------------
1. Create incident ticket (fill out all fields)                          4 min
2. Set priority to Highest                                               1 min
3. Assign to on-call engineer                                            1 min
4. Link to related infrastructure ticket                                 2 min
5. Add initial investigation notes                                       2 min
6. Notify stakeholders                                                   2 min

AFTER: Alex's Incident Response                                    Total: 1 min
--------------------------------------------------------------------------------

Alex: "Create urgent bug 'Production API timeout errors' priority highest
       assign to @oncall-team link to INFRA-456"

Claude: Incident created and configured:

        +----------------------------------------------------------+
        | INCIDENT-999: Production API timeout errors              |
        +----------------------------------------------------------+
        | Priority:  HIGHEST                                       |
        | Assignee:  @oncall-team                                  |
        | Status:    Open                                          |
        | Linked:    INFRA-456 (is caused by)                      |
        | Created:   Just now                                      |
        +----------------------------------------------------------+

        Watchers notified: @platform-team, @engineering-lead

Alex: "Add comment 'Initial investigation: Load balancer showing
       connection pool exhaustion. Scaling up instances.'"

Claude: Comment added to INCIDENT-999
        Timestamp: 2025-01-06 03:45:22 UTC

        [After resolution]

Alex: "Resolve INCIDENT-999 with 'Scaled LB pool from 50 to 200
       connections. Root cause: traffic spike from partner API'"

Claude: INCIDENT-999 resolved
        Resolution: Scaled LB pool from 50 to 200 connections
        Time to Resolution: 23 minutes
        Follow-up task created: INCIDENT-1000 (Post-mortem)

--------------------------------------------------------------------------------
TIME SAVED: 11 min per incident x 50 incidents/year = 9 hours/year saved
(Plus faster MTTR = reduced business impact)
+-----------------------------------------------------------------------------+
```

---

## Story 5: The Contractor Onboarding

```
+-----------------------------------------------------------------------------+
| NEW TEAM MEMBER ONBOARDING                                                  |
+-----------------------------------------------------------------------------+

BEFORE: Manually Creating Onboarding Tasks                        Total: 25 min
--------------------------------------------------------------------------------
1. Create parent task for onboarding                                     3 min
2. Create 8 subtasks (access, equipment, training, etc.)                16 min
3. Assign due dates to each subtask                                      4 min
4. Add links to documentation in descriptions                            2 min

AFTER: Onboarding with JIRA Assistant                              Total: 2 min
--------------------------------------------------------------------------------

HR Manager: "Create epic 'Onboard new contractor: Jamie Chen' with
            subtasks for IT access, equipment setup, security training,
            codebase orientation, team introductions, first sprint assignment"

Claude: Onboarding epic created:

        +----------------------------------------------------------+
        | ONBOARD-100: Onboard new contractor: Jamie Chen          |
        +----------------------------------------------------------+
        | Type: Epic                                               |
        | Status: Open                                             |
        | Due: Jan 20, 2025 (2 weeks from start)                   |
        +----------------------------------------------------------+

        Subtasks created (6):
        +----------------------------------------------------------+
        | ONBOARD-101  IT access requests          Assigned: @IT   |
        | ONBOARD-102  Equipment setup             Assigned: @IT   |
        | ONBOARD-103  Security training           Assigned: @sec  |
        | ONBOARD-104  Codebase orientation        Assigned: @lead |
        | ONBOARD-105  Team introductions          Assigned: @mgr  |
        | ONBOARD-106  First sprint assignment     Assigned: @sm   |
        +----------------------------------------------------------+

        All subtasks linked to epic with default 3-day durations.

--------------------------------------------------------------------------------
TIME SAVED: 23 min per onboard x 15 new hires/year = 5.75 hours/year saved
+-----------------------------------------------------------------------------+
```

---

## Annual Time Savings Summary

| Scenario | Time Saved Per Event | Frequency | Annual Savings |
|----------|---------------------|-----------|----------------|
| Daily Standup | 14 minutes | 200/year | 47 hours |
| Release Prep | 42 minutes | 12/year | 8.4 hours |
| Sprint Planning | 75 minutes | 26/year | 32.5 hours |
| Incident Response | 11 minutes | 50/year | 9 hours |
| Team Onboarding | 23 minutes | 15/year | 5.75 hours |
| **Total** | | | **102.65 hours/year** |

> That's nearly **13 full workdays** returned to productive development work annually per team.
