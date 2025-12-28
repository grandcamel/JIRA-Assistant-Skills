# Video Content Strategy

## Overview
Video content provides the highest engagement but requires the most production effort. This proposal outlines different video types, formats, and production approaches for different budgets and skill levels.

---

## 1. Video Types

### Type A: Terminal Recording (Lowest Effort)
**Concept:** Record actual terminal sessions showing JIRA Assistant in action

**Tools:**
- [asciinema](https://asciinema.org) - Record and share terminal sessions
- [VHS](https://github.com/charmbracelet/vhs) - Write scripts, generate GIFs/videos
- [ttygif](https://github.com/icholy/ttygif) - Convert terminal recordings to GIF

**Pros:**
- Authentic, shows real usage
- No video editing required
- Small file sizes
- Easy to update

**Cons:**
- Text-only, no visual flair
- May be hard to read on mobile
- Limited audience appeal

**Sample VHS Script:**
```vhs
# demo.tape
Output demo.gif
Set FontSize 18
Set Width 1200
Set Height 600
Set Theme "Dracula"

Type "# Let's create a bug report with JIRA Assistant"
Sleep 500ms
Enter
Sleep 1s

Type "claude 'Create a high priority bug: Login fails with error 500 on Safari'"
Sleep 500ms
Enter
Sleep 3s

Type "# Bug created! Let's check it..."
Enter
Sleep 1s

Type "claude 'Show me PROJ-456'"
Enter
Sleep 2s
```

---

### Type B: Annotated Screen Recording (Medium Effort)
**Concept:** Screen recording with callouts, highlights, and text overlays

**Tools:**
- [ScreenFlow](https://www.telestream.net/screenflow/) (Mac)
- [Camtasia](https://www.techsmith.com/video-editor.html) (Cross-platform)
- [OBS Studio](https://obsproject.com/) + [DaVinci Resolve](https://www.blackmagicdesign.com/products/davinciresolve/) (Free)
- [Loom](https://www.loom.com/) (Quick, cloud-based)

**Pros:**
- Can add annotations and highlights
- More polished than raw terminal
- Voiceover optional

**Cons:**
- Requires video editing skills
- Larger file sizes
- More time to produce

**Production Notes:**
- Record at 1920x1080 or higher
- Use a clean desktop/terminal theme
- Zoom into relevant areas
- Add text callouts for key moments

---

### Type C: Explainer Video (Highest Effort)
**Concept:** Produced video with animation, narration, and graphics

**Tools:**
- [After Effects](https://www.adobe.com/products/aftereffects.html) (Professional)
- [Motion](https://www.apple.com/final-cut-pro/motion/) (Mac)
- [Vyond](https://www.vyond.com/) (Animated, no-code)
- [Canva Video](https://www.canva.com/video-editor/) (Easy, templates)

**Pros:**
- Highest production value
- Can explain complex concepts visually
- Strong marketing impact

**Cons:**
- Expensive/time-consuming
- Needs regular updates as product evolves
- May feel "salesy"

---

## 2. Video Content Options

### Option 7A: Quick Demo (30 seconds)
**Purpose:** Embed in README, social media
**Format:** GIF or silent MP4
**Content:**

```
Scene 1 (0-5s): Show problem
  - Text: "Tired of complex JQL?"
  - Visual: Wall of JQL code

Scene 2 (5-15s): Show solution
  - Text: "Just ask."
  - Visual: Type natural language query
  - Visual: Results appear

Scene 3 (15-25s): Show result
  - Text: "14 skills. Zero JQL."
  - Visual: Formatted issue list

Scene 4 (25-30s): CTA
  - Text: "Get started in 5 minutes"
  - Visual: GitHub link
```

**Specs:**
- Duration: 30 seconds
- Resolution: 1280x720 minimum
- Format: GIF (< 5MB) or MP4 (< 10MB)
- Audio: None (plays silently)

---

### Option 7B: Feature Tour (2-3 minutes)
**Purpose:** Overview for evaluators
**Format:** MP4 with audio
**Content:**

```
0:00-0:15  Hook
  "What if you could talk to JIRA like a teammate?"

0:15-0:45  Problem
  Show JQL complexity, clicking through UI
  "The average developer spends 3 hours/week in JIRA"

0:45-1:30  Solution Overview
  Introduce JIRA Assistant Skills
  Show natural language → result flow

1:30-2:15  Feature Highlights
  - Issue creation (15s)
  - Sprint management (15s)
  - Bulk operations (15s)

2:15-2:45  Getting Started
  Show 3-step setup

2:45-3:00  CTA
  "Star on GitHub, join the community"
```

**Specs:**
- Duration: 2-3 minutes
- Resolution: 1920x1080
- Format: MP4 (H.264)
- Audio: Voiceover + light background music
- Subtitles: Required for accessibility

---

### Option 7C: Deep Dive Tutorial Series
**Purpose:** Teach specific skills
**Format:** YouTube playlist
**Content:**

| Episode | Topic | Duration |
|---------|-------|----------|
| 1 | Getting Started | 5 min |
| 2 | Issue Management | 8 min |
| 3 | Sprint Planning | 10 min |
| 4 | Time Tracking | 6 min |
| 5 | Bulk Operations | 7 min |
| 6 | Advanced Search | 8 min |
| 7 | JSM Integration | 10 min |
| 8 | Developer Workflows | 8 min |

**Specs:**
- Duration: 5-10 minutes each
- Resolution: 1920x1080
- Format: MP4 uploaded to YouTube
- Audio: Clear voiceover, minimal music
- Structure: Problem → Solution → Demo → Summary

---

### Option 7D: Use Case Scenarios
**Purpose:** Show real-world applications
**Format:** Short videos (1-2 min each)
**Content:**

1. **"Monday Standup Prep"**
   - Show checking sprint status
   - Log yesterday's work
   - Identify blockers

2. **"Sprint Planning Session"**
   - Create sprint
   - Move stories from backlog
   - Set up sprint goal

3. **"Incident Response"**
   - Create urgent bug
   - Assign to on-call
   - Track to resolution

4. **"Release Readiness"**
   - Check blockers
   - Bulk close resolved issues
   - Export release notes

---

### Option 7E: Comparison Videos
**Purpose:** Show value vs alternatives
**Format:** Side-by-side comparison
**Content:**

```
Split screen:
Left side: "The Old Way" - Manual JIRA
Right side: "The New Way" - JIRA Assistant

Timer overlay showing real-time difference

Tasks:
1. Find my bugs (45s vs 5s)
2. Create sprint (3min vs 15s)
3. Log time on 5 issues (2min vs 20s)

End with total time saved
```

---

## 3. Production Approaches

### Approach A: DIY (Zero Budget)
**Tools:** Free/open source only
**Process:**
1. Write script with VHS tape file
2. Record with asciinema or OBS
3. Edit with DaVinci Resolve (free)
4. Host on GitHub (GIF) or YouTube

**Timeline:** 2-4 hours per video
**Quality:** Functional, not polished

---

### Approach B: Prosumer ($0-500)
**Tools:** Mix of free and affordable
**Process:**
1. Script in Google Docs
2. Record with ScreenFlow or Loom
3. Edit with ScreenFlow or Camtasia
4. Add stock music (Epidemic Sound, Artlist)
5. Host on YouTube with custom thumbnail

**Timeline:** 4-8 hours per video
**Quality:** Good, presentable

---

### Approach C: Professional ($500-2000)
**Tools:** Professional software
**Process:**
1. Professional script writing
2. High-quality screen recording
3. After Effects animations
4. Professional voiceover (Fiverr, Voices.com)
5. YouTube optimization

**Timeline:** 1-2 weeks per video
**Quality:** High, marketing-ready

---

### Approach D: Agency ($2000+)
**Tools:** Full production
**Process:**
1. Brief agency
2. Storyboard approval
3. Professional production
4. Multiple revision rounds
5. Delivery in multiple formats

**Timeline:** 4-6 weeks
**Quality:** Broadcast-ready

---

## 4. Distribution Strategy

### Platform Options

| Platform | Purpose | Format | Duration |
|----------|---------|--------|----------|
| README (GitHub) | Primary landing | GIF | 5-15s |
| YouTube | Discovery, SEO | MP4 | 2-10 min |
| Twitter/X | Awareness | MP4/GIF | 15-60s |
| LinkedIn | Professional | MP4 | 1-3 min |
| Dev.to | Community | Embedded | Any |
| Product Hunt | Launch | MP4 | 60s |

### Hosting Recommendations

**For GIFs (< 5MB):**
- Commit to repo in `assets/`
- GitHub serves directly

**For Videos:**
- YouTube (free, SEO benefits)
- Vimeo (cleaner player, paid)
- Cloudinary (developer-friendly CDN)

---

## 5. Content Calendar Template

### Phase 1: Foundation (Month 1)
- [ ] Quick Demo GIF (Option 7A)
- [ ] Getting Started tutorial (5 min)

### Phase 2: Expansion (Month 2)
- [ ] Feature Tour video (Option 7B)
- [ ] 3 use case scenarios

### Phase 3: Depth (Month 3+)
- [ ] Deep Dive series (episodes 1-4)
- [ ] Comparison video

---

## 6. Script Templates

### Quick Demo Script Template
```
HOOK (3 seconds)
[Visual: Pain point]
Text: "Frustrated with JIRA?"

SOLUTION (10 seconds)
[Visual: Type natural language]
"Just ask what you need"
[Visual: Results appear]

PROOF (10 seconds)
[Visual: Multiple examples rapid-fire]
"Create issues. Track sprints. Search anything."

CTA (7 seconds)
[Visual: GitHub page]
"Get started in 5 minutes"
[Visual: Star button highlighted]
```

### Tutorial Script Template
```
INTRO (30 seconds)
- Greeting
- What we'll cover
- Prerequisites

PROBLEM (1 minute)
- Show the pain point
- Why it matters

SOLUTION (3-5 minutes)
- Step-by-step demo
- Explain as you go
- Highlight key points

SUMMARY (30 seconds)
- Recap key points
- Next steps
- CTA (subscribe, star, etc.)
```

---

## Recommendation

**Immediate priorities:**
1. **Option 7A (Quick Demo)** - Terminal GIF for README
   - Tool: VHS or asciinema
   - Duration: 15-30 seconds
   - Budget: Free

2. **Getting Started video** - YouTube upload
   - Tool: OBS + DaVinci Resolve
   - Duration: 5 minutes
   - Budget: Free

**Phase 2:**
3. **Option 7B (Feature Tour)** - Marketing video
   - Tool: ScreenFlow + stock music
   - Duration: 2-3 minutes
   - Budget: $100-300

**Long-term:**
4. **Tutorial Series** - YouTube playlist
5. **Use Case Scenarios** - Role-specific content

---

## File Naming Convention

```
jira-assistant-demo-30s.gif          # Quick demo
jira-assistant-getting-started.mp4   # Tutorial
jira-assistant-sprint-planning.mp4   # Use case
jira-assistant-vs-jql.mp4           # Comparison
```
