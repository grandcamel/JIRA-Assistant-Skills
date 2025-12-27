# JIRA Assistant Skills Demo - VHS Tape File
# Generate with: vhs demo.tape
# Requires: brew install vhs ttyd ffmpeg

# Output settings
Output demo.gif
Output demo.webm

# Terminal appearance
Set FontSize 18
Set FontFamily "JetBrains Mono"
Set Width 1000
Set Height 600
Set Theme "Catppuccin Mocha"
Set Padding 20
Set Margin 10
Set MarginFill "#1e1e2e"
Set BorderRadius 10
Set WindowBar Colorful
Set TypingSpeed 50ms

# Intro
Hide
Type "clear"
Enter
Show
Sleep 500ms

Type "# JIRA Assistant Skills - Demo"
Enter
Sleep 1s

Type "# Twelve modular skills for AI-powered JIRA automation"
Enter
Sleep 1s

Type ""
Enter
Sleep 500ms

# Demo 1: Get Issue Details
Type "# 1. Retrieve issue details"
Enter
Sleep 500ms

Type "python .claude/skills/jira-issue/scripts/get_issue.py PROJ-123 --detailed"
Enter
Sleep 1s

# Simulated output for get_issue
Type@100ms "Issue: PROJ-123"
Enter
Type@100ms "Summary: Implement user authentication"
Enter
Type@100ms "Type: Story | Priority: High | Status: In Progress"
Enter
Type@100ms "Assignee: John Developer"
Enter
Type@100ms "Sprint: Sprint 14"
Enter
Type@100ms "Story Points: 5"
Enter
Sleep 2s

Type ""
Enter

# Demo 2: Search with JQL
Type "# 2. Search issues with JQL"
Enter
Sleep 500ms

Type "python .claude/skills/jira-search/scripts/jql_search.py \"project = PROJ AND status = 'In Progress'\" --max-results 5"
Enter
Sleep 1s

# Simulated search results
Type@100ms "Found 5 issue(s)"
Enter
Type@100ms ""
Enter
Type@100ms "  Key       | Type    | Priority | Summary"
Enter
Type@100ms "  ----------|---------|----------|----------------------------------"
Enter
Type@100ms "  PROJ-123  | Story   | High     | Implement user authentication"
Enter
Type@100ms "  PROJ-124  | Bug     | Critical | Login button not responding"
Enter
Type@100ms "  PROJ-125  | Task    | Medium   | Update API documentation"
Enter
Type@100ms "  PROJ-126  | Story   | High     | Add dark mode support"
Enter
Type@100ms "  PROJ-127  | Bug     | Low      | Minor UI alignment issue"
Enter
Sleep 2s

Type ""
Enter

# Demo 3: Transition Issue
Type "# 3. Transition an issue"
Enter
Sleep 500ms

Type "python .claude/skills/jira-lifecycle/scripts/transition_issue.py PROJ-123 \"Done\""
Enter
Sleep 1s

Type@100ms "Transitioned PROJ-123 from 'In Progress' to 'Done'"
Enter
Sleep 1.5s

Type ""
Enter

# Demo 4: Add Comment
Type "# 4. Collaborate on issues"
Enter
Sleep 500ms

Type "python .claude/skills/jira-collaborate/scripts/add_comment.py PROJ-123 \"Code review completed. Ready for QA.\""
Enter
Sleep 1s

Type@100ms "Added comment to PROJ-123 (comment ID: 10542)"
Enter
Sleep 1.5s

Type ""
Enter

# Demo 5: Log Time
Type "# 5. Track time spent"
Enter
Sleep 500ms

Type "python .claude/skills/jira-time/scripts/log_time.py PROJ-123 2h --comment \"Implemented OAuth flow\""
Enter
Sleep 1s

Type@100ms "Logged 2h to PROJ-123"
Enter
Type@100ms "  Time Spent: 6h"
Enter
Type@100ms "  Remaining: 2h"
Enter
Sleep 1.5s

Type ""
Enter

# Demo 6: Agile Operations
Type "# 6. Manage sprints and backlogs"
Enter
Sleep 500ms

Type "python .claude/skills/jira-agile/scripts/move_to_sprint.py PROJ-128 --sprint \"Sprint 15\""
Enter
Sleep 1s

Type@100ms "Moved PROJ-128 to Sprint 15"
Enter
Sleep 1.5s

Type ""
Enter

# Demo 7: Bulk Operations
Type "# 7. Bulk operations with dry-run"
Enter
Sleep 500ms

Type "python .claude/skills/jira-bulk/scripts/bulk_transition.py \"project = PROJ AND status = 'Code Review'\" \"Done\" --dry-run"
Enter
Sleep 1s

Type@100ms "[DRY RUN] Would transition 3 issues to 'Done':"
Enter
Type@100ms "  - PROJ-129: Fix pagination bug"
Enter
Type@100ms "  - PROJ-130: Add unit tests"
Enter
Type@100ms "  - PROJ-131: Update README"
Enter
Sleep 2s

Type ""
Enter

# Demo 8: Issue Relationships
Type "# 8. Track dependencies"
Enter
Sleep 500ms

Type "python .claude/skills/jira-relationships/scripts/get_blockers.py PROJ-200 --recursive"
Enter
Sleep 1s

Type@100ms "Blocker chain for PROJ-200:"
Enter
Type@100ms "  PROJ-200 is blocked by:"
Enter
Type@100ms "    -> PROJ-198 (API refactoring)"
Enter
Type@100ms "       -> PROJ-195 (Database migration)"
Enter
Type@100ms "  Total: 2 blocking issues"
Enter
Sleep 2s

Type ""
Enter

# Outro
Type "# Learn more: github.com/grandcamel/jira-assistant-skills"
Enter
Sleep 2s

Type ""
Enter

# Final pause
Sleep 1s
