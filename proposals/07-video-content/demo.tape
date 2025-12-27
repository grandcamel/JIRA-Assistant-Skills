# JIRA Assistant Skills - Quick Demo (30 seconds)
# VHS Tape File for Terminal Recording
#
# Usage:
#   brew install vhs
#   vhs demo.tape
#
# Output: jira-assistant-demo-30s.gif

# === Configuration ===
Output jira-assistant-demo-30s.gif
Set FontSize 20
Set Width 1280
Set Height 720
Set Theme "Dracula"
Set Padding 40
Set Framerate 30
Set TypingSpeed 50ms
Set LoopOffset 0%

# === Scene 1: The Problem (0-5 seconds) ===
# Show the pain of complex JQL

Hide
Type "clear"
Enter
Show

Sleep 500ms
Type "# The old way: JQL headaches..."
Enter
Sleep 800ms

Type 'project = "PROJ" AND issuetype = Bug AND status NOT IN (Closed, Resolved, Done) AND priority IN (High, Highest, Critical) AND assignee = currentUser() AND updated >= startOfDay(-7d) ORDER BY priority DESC, created DESC'
Sleep 2s
Enter

# Error feedback (simulated)
Sleep 300ms
Type "# Complex. Error-prone. Time-consuming."
Enter
Sleep 1s

# === Scene 2: The Solution (5-15 seconds) ===
# Natural language with Claude

Type "clear"
Enter
Sleep 300ms

Type "# The new way: Just ask."
Enter
Sleep 500ms

# First example: Natural language search
Type 'claude "Show my high priority bugs from this week"'
Sleep 500ms
Enter
Sleep 1s

# Simulated Claude response
Type "# [Claude searches JIRA...]"
Enter
Sleep 1s
Type "# Found 3 bugs:"
Enter
Sleep 300ms
Type "#   PROJ-456  Critical  Login fails on Safari"
Enter
Type "#   PROJ-457  High      Payment timeout error"
Enter
Type "#   PROJ-458  High      Cart items disappear"
Enter
Sleep 1s

# === Scene 3: Show Power (15-25 seconds) ===
# Multiple capabilities rapid-fire

Type "# Create, track, manage - all in natural language"
Enter
Sleep 500ms

# Create issue
Type 'claude "Create a bug: Checkout button unresponsive on mobile"'
Sleep 300ms
Enter
Sleep 800ms
Type "# Created PROJ-789"
Enter
Sleep 500ms

# Transition
Type 'claude "Move PROJ-789 to In Progress and assign to me"'
Sleep 300ms
Enter
Sleep 800ms
Type "# Done. PROJ-789 is now In Progress."
Enter
Sleep 500ms

# Time logging
Type 'claude "Log 2 hours on PROJ-789"'
Sleep 300ms
Enter
Sleep 600ms
Type "# Logged 2h. Remaining: 6h"
Enter
Sleep 500ms

# === Scene 4: Call to Action (25-30 seconds) ===
# GitHub link and star

Type "clear"
Enter
Sleep 300ms

Type "# 12 Skills. Zero JQL. Infinite Possibilities."
Enter
Sleep 500ms
Type "#"
Enter
Type "# Issue Management | Sprint Planning | Time Tracking"
Enter
Type "# Bulk Operations | Search | Relationships | And more..."
Enter
Sleep 500ms
Type "#"
Enter
Type "# Get started in 5 minutes:"
Enter
Sleep 300ms
Type "# github.com/your-org/Jira-Assistant-Skills"
Enter
Sleep 1.5s
