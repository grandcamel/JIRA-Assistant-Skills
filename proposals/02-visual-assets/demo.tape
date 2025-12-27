# VHS Tape Script for JIRA Assistant Skills Demo GIF
# https://github.com/charmbracelet/vhs
#
# Usage:
#   1. Install VHS: brew install vhs
#   2. Run: vhs demo.tape
#   3. Output: demo.gif
#
# This creates a polished terminal recording demonstrating
# the natural language interface to JIRA.

# Configuration
Output demo.gif
Set FontFamily "SF Mono"
Set FontSize 16
Set Width 900
Set Height 600
Set Padding 20
Set Framerate 24
Set TypingSpeed 50ms
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set WindowBarSize 40
Set CursorBlink true
Set LoopOffset 50%

# Initial pause to show clean terminal
Sleep 1s

# Scene 1: Show the problem
Type "# Traditional way: complex JQL queries"
Enter
Sleep 500ms
Type "jql_search.py 'project = PROJ AND status != Done AND assignee = currentUser() AND sprint in openSprints() ORDER BY priority DESC'"
Sleep 1s
Enter
Sleep 500ms

# Simulate output (in real recording, this would be actual output)
Type "# ... lots of output ..."
Enter
Sleep 1s

# Clear for next scene
Type "clear"
Enter
Sleep 500ms

# Scene 2: The better way
Type "# With JIRA Assistant Skills:"
Enter
Sleep 500ms

# Natural language question
Type '> "What am I working on this sprint?"'
Enter
Sleep 1s

# Simulated thinking
Type "Searching your assigned issues in current sprint..."
Enter
Sleep 800ms

# Pretty output
Type ""
Enter
Type "┌─────────────────────────────────────────────────────────────────┐"
Enter
Type "│  Your Sprint Items (Sprint 42)                                 │"
Enter
Type "├───────────┬────────────────────────────┬─────────┬─────────────┤"
Enter
Type "│ Key       │ Summary                    │ Status  │ Points      │"
Enter
Type "├───────────┼────────────────────────────┼─────────┼─────────────┤"
Enter
Type "│ PROJ-123  │ Add user authentication    │ In Prog │ 8           │"
Enter
Type "│ PROJ-124  │ Fix login redirect bug     │ To Do   │ 3           │"
Enter
Type "│ PROJ-125  │ Update API documentation   │ To Do   │ 2           │"
Enter
Type "└───────────┴────────────────────────────┴─────────┴─────────────┘"
Enter
Sleep 1s

# Scene 3: Quick action
Type ""
Enter
Type '> "Start working on the login bug"'
Enter
Sleep 800ms

Type "Transitioning PROJ-124 to 'In Progress'..."
Enter
Sleep 500ms
Type "Done! PROJ-124 is now In Progress and assigned to you."
Enter
Sleep 1s

# Scene 4: Time tracking
Type ""
Enter
Type '> "Log 2 hours on PROJ-123"'
Enter
Sleep 800ms

Type "Logging 2h on PROJ-123 (Add user authentication)..."
Enter
Sleep 500ms
Type "Worklog added! Remaining estimate: 6h"
Enter
Sleep 1s

# Scene 5: Quick status check
Type ""
Enter
Type '> "What blockers do we have?"'
Enter
Sleep 800ms

Type "Analyzing blocker relationships..."
Enter
Sleep 600ms
Type ""
Enter
Type "Found 2 blockers:"
Enter
Type "  PROJ-130 (Critical): Waiting for API keys"
Enter
Type "    Blocks: PROJ-123, PROJ-131"
Enter
Type "  PROJ-132 (High): Design review pending"
Enter
Type "    Blocks: PROJ-140"
Enter
Sleep 1.5s

# Final message
Type ""
Enter
Type "# No JQL required. Just talk to JIRA."
Enter
Sleep 2s

# Hold final frame
Sleep 1s
