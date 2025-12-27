# JIRA Assistant Skills - Video Script

## Production Information

| Field | Value |
|-------|-------|
| **Title** | JIRA Assistant Skills Quick Demo |
| **Duration** | 30 seconds |
| **Format** | Terminal recording (GIF/MP4) |
| **Audio** | None (silent) |
| **Tool** | VHS (charmbracelet/vhs) |
| **Output** | `jira-assistant-demo-30s.gif` |

---

## Script

### SCENE 1: THE PROBLEM
**Time:** 0:00 - 0:05 (5 seconds)

```
ACTION:
- Screen clears
- Comment appears: "The old way: JQL headaches..."
- Complex JQL query types out slowly, wrapping across lines
- Second comment: "Complex. Error-prone. Time-consuming."

ON SCREEN TEXT:
# The old way: JQL headaches...
project = "PROJ" AND issuetype = Bug AND status NOT IN (Closed, Resolved, Done) AND priority IN (High, Highest, Critical) AND assignee = currentUser() AND updated >= startOfDay(-7d) ORDER BY priority DESC, created DESC
# Complex. Error-prone. Time-consuming.

PURPOSE:
Establish the pain point. Viewers who use JIRA will immediately recognize
the complexity and feel the frustration. This creates contrast for Scene 2.

TIMING BREAKDOWN:
- 0.0s: Clear screen
- 0.5s: First comment types
- 1.3s: JQL query begins typing (2.5 seconds)
- 4.0s: Frustration comment
- 5.0s: Transition to Scene 2
```

---

### SCENE 2: THE SOLUTION
**Time:** 0:05 - 0:15 (10 seconds)

```
ACTION:
- Screen clears
- Comment: "The new way: Just ask."
- Natural language query typed
- Claude "processes" the request
- Results appear in clean, formatted list

ON SCREEN TEXT:
# The new way: Just ask.
claude "Show my high priority bugs from this week"

# [Claude searches JIRA...]
# Found 3 bugs:
#   PROJ-456  Critical  Login fails on Safari
#   PROJ-457  High      Payment timeout error
#   PROJ-458  High      Cart items disappear

PURPOSE:
Demonstrate the simplicity of natural language. The same query that took
multiple lines of complex JQL is now a single English sentence.

KEY MESSAGE:
"Same result. One sentence. No JQL required."

TIMING BREAKDOWN:
- 5.0s: Clear, new comment appears
- 5.5s: Natural language command types
- 6.5s: Enter pressed
- 7.5s: Loading indicator
- 8.5s: Results appear line by line
- 15.0s: Transition to Scene 3
```

---

### SCENE 3: RAPID CAPABILITIES
**Time:** 0:15 - 0:25 (10 seconds)

```
ACTION:
- Intro comment: "Create, track, manage - all in natural language"
- Three commands fire in quick succession:
  1. Create issue
  2. Transition + assign
  3. Log time
- Each shows immediate confirmation

ON SCREEN TEXT:
# Create, track, manage - all in natural language

claude "Create a bug: Checkout button unresponsive on mobile"
# Created PROJ-789

claude "Move PROJ-789 to In Progress and assign to me"
# Done. PROJ-789 is now In Progress.

claude "Log 2 hours on PROJ-789"
# Logged 2h. Remaining: 6h

PURPOSE:
Show breadth of capabilities. In 10 seconds, demonstrate three different
skills working together in a realistic workflow.

SKILLS HIGHLIGHTED:
1. jira-issue: Create issues with natural language
2. jira-lifecycle: Transition and assign in one command
3. jira-time: Time tracking without navigating UI

TIMING BREAKDOWN:
- 15.0s: Intro comment
- 15.5s: Create command + response
- 17.5s: Transition command + response
- 20.0s: Time log command + response
- 22.5s: Brief pause
- 25.0s: Transition to Scene 4
```

---

### SCENE 4: CALL TO ACTION
**Time:** 0:25 - 0:30 (5 seconds)

```
ACTION:
- Screen clears
- Tagline appears
- Skill categories listed
- GitHub URL displayed
- Hold for reading

ON SCREEN TEXT:
# 12 Skills. Zero JQL. Infinite Possibilities.
#
# Issue Management | Sprint Planning | Time Tracking
# Bulk Operations | Search | Relationships | And more...
#
# Get started in 5 minutes:
# github.com/your-org/Jira-Assistant-Skills

PURPOSE:
Drive action. Viewers now know what the tool does; give them a clear
next step and memorable tagline.

KEY ELEMENTS:
- "12 Skills" - Specific number creates credibility
- "Zero JQL" - Clear value proposition
- "5 minutes" - Low barrier to entry
- GitHub URL - Clear, direct CTA

TIMING BREAKDOWN:
- 25.0s: Clear screen
- 25.3s: Tagline types
- 26.0s: Skills list appears
- 27.5s: GitHub URL appears
- 28.0s-30.0s: Hold for reading
```

---

## Production Notes

### Pre-Production Checklist
- [ ] Install VHS: `brew install vhs`
- [ ] Test tape file syntax: `vhs validate demo.tape`
- [ ] Verify terminal theme matches design
- [ ] Test at target resolution (1280x720)

### Recording Tips
1. **Clean Environment:** Run in fresh terminal session
2. **Font Verification:** Ensure monospace font renders correctly
3. **Color Test:** Verify Dracula theme colors display properly
4. **Timing Review:** Watch full recording, adjust Sleep values if needed

### Post-Production
1. **File Size Check:** GIF should be < 5MB
2. **Optimization:** If too large, consider:
   - Reduce framerate from 30 to 24
   - Reduce resolution to 1024x576
   - Use lossy GIF optimization (gifsicle)
3. **MP4 Alternative:** Generate MP4 for platforms that support video

### Quality Checklist
- [ ] Text is readable at 50% zoom
- [ ] No typos in commands or output
- [ ] Timing feels natural (not too fast/slow)
- [ ] Commands are realistic and accurate
- [ ] Issue keys follow PROJ-### format
- [ ] GitHub URL is correct

---

## Alternate Versions

### Version A: Extended (45 seconds)
Add Scene 2.5: Show a sprint planning example
```
claude "Create a sprint called 'Q1 Release' and add PROJ-456, PROJ-457"
# Sprint created. 2 issues added.
```

### Version B: Minimal (15 seconds)
Skip Scene 1, start directly with natural language demo
- 0-10s: Scene 2 (Solution)
- 10-15s: Scene 4 (CTA)

### Version C: Feature-Specific
Create separate 15-second demos for each skill:
- `demo-issue-management.tape`
- `demo-sprint-planning.tape`
- `demo-time-tracking.tape`
- `demo-bulk-operations.tape`

---

## Distribution Checklist

### Immediate
- [ ] Add to README.md at top of file
- [ ] Upload to GitHub releases as asset
- [ ] Add to CONTRIBUTING.md

### Social Media
- [ ] Twitter/X post with GIF
- [ ] LinkedIn article embed
- [ ] Dev.to article embed

### Future
- [ ] YouTube upload (MP4 version)
- [ ] Product Hunt launch video
- [ ] Documentation site hero section

---

## Revision Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-27 | Claude | Initial script |
