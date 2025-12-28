# JIRA Assistant Skills - Quick Demo Storyboard

## Overview
- **Duration:** 30 seconds
- **Format:** Animated GIF (silent)
- **Resolution:** 1280x720
- **Target:** README embedding, social media
- **Tool:** VHS (charmbracelet/vhs)

---

## Scene 1: The Problem (0-5 seconds)

### Visual Description
```
+------------------------------------------------------------------+
|                                                                  |
|  $ # The old way: JQL headaches...                              |
|  $ project = "PROJ" AND issuetype = Bug AND status NOT IN       |
|    (Closed, Resolved, Done) AND priority IN (High, Highest,     |
|    Critical) AND assignee = currentUser() AND updated >=        |
|    startOfDay(-7d) ORDER BY priority DESC, created DESC         |
|                                                                  |
|  $ # Complex. Error-prone. Time-consuming.                      |
|                                                                  |
+------------------------------------------------------------------+
```

### Elements
- **Text:** Complex JQL query spanning multiple lines
- **Color:** Dracula theme (dark background, colored syntax)
- **Timing:**
  - 0.0s: Clear screen
  - 0.5s: Type comment
  - 1.3s: Type JQL (slow, emphasizing complexity)
  - 4.0s: Show frustration comment
- **Emotion:** Overwhelm, complexity

---

## Scene 2: The Solution (5-15 seconds)

### Visual Description
```
+------------------------------------------------------------------+
|                                                                  |
|  $ # The new way: Just ask.                                     |
|  $ claude "Show my high priority bugs from this week"           |
|                                                                  |
|  $ # [Claude searches JIRA...]                                  |
|  $ # Found 3 bugs:                                              |
|  $   PROJ-456  Critical  Login fails on Safari                  |
|  $   PROJ-457  High      Payment timeout error                  |
|  $   PROJ-458  High      Cart items disappear                   |
|                                                                  |
+------------------------------------------------------------------+
```

### Elements
- **Text:** Natural language query, formatted results
- **Contrast:** Simple one-liner vs. complex JQL
- **Timing:**
  - 5.0s: Clear, new comment
  - 5.5s: Type natural language command
  - 6.5s: Press Enter
  - 7.5s: Show loading indicator
  - 8.5s: Display results (formatted table)
- **Emotion:** Relief, simplicity

---

## Scene 3: Show Power (15-25 seconds)

### Visual Description
```
+------------------------------------------------------------------+
|                                                                  |
|  $ # Create, track, manage - all in natural language            |
|                                                                  |
|  $ claude "Create a bug: Checkout button unresponsive"          |
|  $ # Created PROJ-789                                           |
|                                                                  |
|  $ claude "Move PROJ-789 to In Progress and assign to me"       |
|  $ # Done. PROJ-789 is now In Progress.                         |
|                                                                  |
|  $ claude "Log 2 hours on PROJ-789"                             |
|  $ # Logged 2h. Remaining: 6h                                   |
|                                                                  |
+------------------------------------------------------------------+
```

### Elements
- **Text:** Three rapid-fire commands showing different skills
- **Skills Demonstrated:**
  1. Issue creation (jira-issue)
  2. Transitions + assignment (jira-lifecycle)
  3. Time tracking (jira-time)
- **Timing:**
  - 15.0s: Intro comment
  - 15.5s: Create issue command
  - 17.0s: Transition command
  - 19.0s: Time log command
- **Emotion:** Power, efficiency

---

## Scene 4: Call to Action (25-30 seconds)

### Visual Description
```
+------------------------------------------------------------------+
|                                                                  |
|  # 12 Skills. Zero JQL. Infinite Possibilities.                 |
|  #                                                              |
|  # Issue Management | Sprint Planning | Time Tracking           |
|  # Bulk Operations | Search | Relationships | And more...       |
|  #                                                              |
|  # Get started in 5 minutes:                                    |
|  # github.com/your-org/Jira-Assistant-Skills                    |
|                                                                  |
+------------------------------------------------------------------+
```

### Elements
- **Text:** Tagline, skill list, GitHub URL
- **Visual Hierarchy:**
  - Large tagline
  - Skill categories (abbreviated)
  - Clear CTA with URL
- **Timing:**
  - 25.0s: Clear screen
  - 25.3s: Display tagline
  - 26.0s: Show skill categories
  - 27.5s: Display GitHub URL
  - 28.0s-30.0s: Hold for reading
- **Emotion:** Excitement, action

---

## Technical Specifications

### VHS Configuration
```vhs
Set FontSize 20        # Large enough for mobile viewing
Set Width 1280         # 720p width
Set Height 720         # 720p height
Set Theme "Dracula"    # High contrast, developer-friendly
Set Padding 40         # Breathing room
Set Framerate 30       # Smooth animation
Set TypingSpeed 50ms   # Fast but readable
```

### Color Palette (Dracula Theme)
- Background: #282a36
- Foreground: #f8f8f2
- Comments: #6272a4
- Cyan: #8be9fd
- Green: #50fa7b
- Orange: #ffb86c
- Pink: #ff79c6
- Purple: #bd93f9
- Red: #ff5555
- Yellow: #f1fa8c

### File Output
- **Primary:** `jira-assistant-demo-30s.gif`
- **Alternate:** `jira-assistant-demo-30s.mp4`
- **Size Target:** < 5MB for GIF

---

## Accessibility Notes

1. **Text Size:** Font size 20 ensures readability on mobile
2. **Contrast:** Dracula theme provides WCAG AA contrast
3. **No Audio:** Silent GIF works in all contexts
4. **Timing:** Each scene holds long enough to read
5. **Simplicity:** One concept per scene

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-27 | Initial storyboard |
