# Visual Assets Options

## Overview
Visual assets include logos, banners, GIFs, and images that create brand identity and demonstrate functionality.

---

## 1. Logo Options

### Option 1A: Abstract Geometric
**Concept:** Interconnected nodes representing skills/connections

```
    ◆───◆
   /│   │\
  ◆─┼───┼─◆
   \│   │/
    ◆───◆
```

- Modern, tech-forward
- Works at small sizes
- No direct JIRA/Atlassian imagery (avoids trademark issues)

### Option 1B: Chat Bubble + Ticket
**Concept:** Speech bubble morphing into a ticket/issue shape

```
  ┌─────────┐
  │ ? → ✓   │
  └────┬────┘
       ▼
```

- Clearly communicates "conversation to action"
- Intuitive meaning
- Friendly, approachable

### Option 1C: Hexagonal Skill Grid
**Concept:** Honeycomb pattern with "JA" or icon center

```
   ⬡ ⬡
  ⬡ JA ⬡
   ⬡ ⬡
```

- Represents modular skills
- Scalable (add more hexagons for complexity)
- Modern, premium feel

### Option 1D: Terminal Prompt
**Concept:** Stylized command prompt with JIRA colors

```
  > jira_
```

- Developer-friendly
- Instantly recognizable context
- Minimal, distinctive

### Option 1E: Bridge/Connector
**Concept:** Arc connecting "Natural Language" to "JIRA"

```
  NL ︵ JIRA
     ╲_/
```

- Communicates translation/bridging
- Abstract but meaningful
- Works in monochrome

---

## 2. Banner Options

### Option 2A: Gradient Tech Banner
**Style:** Dark background, gradient accents, code snippets

```
┌─────────────────────────────────────────────────────────────────────┐
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│  ░                                                               ░  │
│  ░   [LOGO]  JIRA ASSISTANT SKILLS                              ░  │
│  ░           Talk to JIRA like you talk to a teammate           ░  │
│  ░                                                               ░  │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
└─────────────────────────────────────────────────────────────────────┘
```

**Colors:** Deep blue (#1a1a2e) → Purple (#4a00e0) gradient
**Dimensions:** 1280x320px (GitHub standard)

### Option 2B: Split Comparison Banner
**Style:** Left side chaos, right side clarity

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Complex JQL mess]      │        [Clean conversation]             │
│  project = PROJ AND      │        "Show my blockers"               │
│  status IN (Open...      │        ───────────────────              │
│  ████████████████        │             ✓ Done                      │
│         😤               │              😊                         │
└─────────────────────────────────────────────────────────────────────┘
```

**Style:** Before/After visual transformation

### Option 2C: Animated Banner (GIF)
**Style:** Terminal typing animation

```
Frame 1: > _
Frame 2: > W_
Frame 3: > Wh_
Frame 4: > What_
...
Frame N: > What's blocking the release?
Frame N+1: [Response appears]
```

**Format:** GIF, ~3 seconds loop
**Size:** Keep under 1MB for fast loading

### Option 2D: Skill Icon Strip
**Style:** Row of skill icons with labels

```
┌─────────────────────────────────────────────────────────────────────┐
│                    JIRA ASSISTANT SKILLS                            │
│                                                                     │
│   📝 Issue  🔄 Lifecycle  🔍 Search  💬 Collaborate  🏃 Agile      │
│   🔗 Links  ⏱️ Time  🎫 JSM  📦 Bulk  👨‍💻 Dev  ⚙️ Fields  🔧 Ops   │
│                                                                     │
│              14 skills • 100+ scripts • 0 JQL required              │
└─────────────────────────────────────────────────────────────────────┘
```

### Option 2E: Minimalist Text Banner
**Style:** Typography-focused, no imagery

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                     JIRA ASSISTANT SKILLS                           │
│                                                                     │
│           "Show me what's blocking the release"                     │
│                          ↓                                          │
│              Found 3 blockers across 47 issues                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Demo GIF Options

### Option 3A: Full Terminal Recording
**Content:** Complete workflow from question to answer
**Duration:** 30-45 seconds
**Tool:** asciinema → gif conversion

```
Sequence:
1. Show prompt
2. Type question naturally
3. Show "thinking" indicator
4. Display formatted response
5. Show follow-up action
```

### Option 3B: Split Screen Demo
**Content:** Left: Terminal | Right: JIRA updating
**Duration:** 20-30 seconds
**Tool:** Screen recording + compositing

```
┌──────────────────┬──────────────────┐
│    Terminal      │   JIRA Web UI    │
│                  │                  │
│  > Create bug... │   [Issue created]│
│                  │   PROJ-456       │
│  ✓ Created       │   [Fields fill]  │
└──────────────────┴──────────────────┘
```

### Option 3C: Conversation Cascade
**Content:** Multiple questions showing skill variety
**Duration:** 45-60 seconds
**Style:** Fast cuts between different capabilities

```
Scene 1: "Create a bug" → Issue created
Scene 2: "Start sprint" → Sprint activated
Scene 3: "What's blocked?" → Analysis shown
Scene 4: "Log 2 hours" → Time logged
```

### Option 3D: Before/After Animation
**Content:** Same task, two ways
**Duration:** 20 seconds
**Style:** Side-by-side comparison

```
Left panel: Manual JIRA (slow, many clicks)
Right panel: Claude conversation (fast, natural)
Timer overlay showing time difference
```

### Option 3E: Typewriter Effect (Lightweight)
**Content:** Just the conversation text, no actual terminal
**Duration:** 15 seconds
**Style:** Animated text on clean background
**Size:** <500KB

---

## 4. Infographic Options

### Option 4A: Skill Wheel
**Concept:** Circular diagram with jira-assistant at center

```
              jira-search
                  │
    jira-agile ───┼─── jira-issue
                  │
         [jira-assistant]
                  │
    jira-jsm ─────┼───── jira-dev
                  │
              jira-bulk
```

### Option 4B: Layered Architecture
**Concept:** Horizontal layers showing flow

```
┌─────────────────────────────────────────┐
│           Natural Language              │  You
├─────────────────────────────────────────┤
│           Claude Code                   │  AI
├─────────────────────────────────────────┤
│    14 Specialized JIRA Skills           │  Skills
├─────────────────────────────────────────┤
│           JIRA REST API                 │  API
├─────────────────────────────────────────┤
│           JIRA Cloud                    │  Data
└─────────────────────────────────────────┘
```

### Option 4C: Use Case Matrix
**Concept:** Grid showing role × capability

```
                    Sprint   Incident   Search   Time
                    Planning Response   Query    Track
Developer             ✓         ✓         ✓        ✓
Team Lead             ✓         ✓         ✓        ✓
Product Manager       ✓         ○         ✓        ○
IT/Ops                ○         ✓         ✓        ○

✓ = Primary use  ○ = Secondary use
```

### Option 4D: Timeline Flow
**Concept:** Day-in-the-life showing skill usage

```
9:00 AM  "What's on my plate today?"     → jira-search
9:30 AM  "Create spike for perf issue"   → jira-issue
2:00 PM  "Start progress on PROJ-123"    → jira-lifecycle
4:00 PM  "Log 3 hours on PROJ-123"       → jira-time
5:00 PM  "What did I complete today?"    → jira-search
```

---

## 5. Screenshot Options

### Option 5A: Clean Terminal Output
**Content:** Formatted response with colors
**Focus:** Show professional, readable output

### Option 5B: IDE Integration
**Content:** Claude Code in VS Code/terminal
**Focus:** Show real development environment

### Option 5C: JIRA Result
**Content:** JIRA UI showing created/modified item
**Focus:** Prove it actually works

### Option 5D: Conversation Thread
**Content:** Multi-turn conversation
**Focus:** Show contextual understanding

---

## Production Specifications

| Asset | Dimensions | Format | Max Size | Tool Recommendation |
|-------|------------|--------|----------|---------------------|
| Logo | 512x512 | SVG + PNG | 50KB | Figma, Illustrator |
| Banner | 1280x320 | PNG | 200KB | Figma, Canva |
| Demo GIF | 800x500 | GIF | 5MB | VHS, asciinema |
| Infographic | 1200x800 | PNG/SVG | 300KB | Figma, Mermaid |
| Screenshot | 1200x750 | PNG | 200KB | CleanShot, native |

---

## Recommendation

**Immediate priorities:**
1. **Logo:** Option 1D (Terminal Prompt) - simple, developer-friendly
2. **Banner:** Option 2A (Gradient Tech) - professional, modern
3. **Demo GIF:** Option 3A (Full Terminal) - shows real value
4. **Infographic:** Option 4B (Layered Architecture) - explains system

**Phase 2:**
- Before/After animation (Option 3D)
- Skill Wheel infographic (Option 4A)
- IDE integration screenshots (Option 5B)
