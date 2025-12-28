# Hero Section Design Options

## Overview
The hero section is the first 10 seconds of attention. It must communicate value instantly and compel scrolling.

---

## Option A: Minimal Elegant

**Philosophy:** Apple-style simplicity. One image, one line, maximum impact.

```markdown
<p align="center">
  <img src="assets/logo-light.svg" alt="JIRA Assistant" width="120">
</p>

<h1 align="center">Talk to JIRA</h1>

<p align="center">
  <em>14 Claude Code skills that turn natural language into JIRA actions.</em>
</p>

<p align="center">
  <img src="assets/hero-conversation.gif" alt="Demo" width="600">
</p>

<p align="center">
  <a href="#quick-start"><strong>Get Started →</strong></a>
</p>
```

**Pros:** Clean, fast-loading, timeless
**Cons:** May not convey feature depth
**Best for:** Developer audience who appreciates minimalism

---

## Option B: Badge-Heavy Technical

**Philosophy:** Instant credibility through metrics and status indicators.

```markdown
<p align="center">
  <img src="assets/banner-technical.png" alt="JIRA Assistant Skills" width="800">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-3776AB?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/tests-560%2B%20passing-brightgreen?logo=pytest">
  <img src="https://img.shields.io/badge/skills-14-FF6B6B">
  <img src="https://img.shields.io/badge/scripts-100%2B-4ECDC4">
  <img src="https://img.shields.io/badge/coverage-live%20tested-0052CC?logo=atlassian">
  <img src="https://img.shields.io/github/stars/grandcamel/jira-assistant-skills?style=social">
</p>

<p align="center">
  <strong>Natural language JIRA automation for Claude Code</strong><br>
  <sub>From sprint planning to incident response—14 skills, 100+ scripts, zero JQL memorization.</sub>
</p>

<p align="center">
  <a href="#quick-start">🚀 Quick Start</a> •
  <a href="#demo">🎬 Demo</a> •
  <a href="#skills">📚 Skills</a> •
  <a href="#architecture">🏗️ Architecture</a>
</p>
```

**Pros:** Immediate credibility, SEO-friendly, scannable
**Cons:** Can feel cluttered, badges may become stale
**Best for:** Open source community, GitHub power users

---

## Option C: Problem-Solution Hook

**Philosophy:** Lead with the pain, reveal the solution.

```markdown
<h1 align="center">😤 → 😊</h1>

<table align="center">
<tr>
<td align="center" width="45%">

**The Old Way**
```
SELECT * FROM jira WHERE
  project = 'PROJ' AND
  sprint IN openSprints() AND
  status != 'Done' AND
  assignee = currentUser()
ORDER BY priority DESC
```
*Copy. Paste. Debug. Repeat.*

</td>
<td align="center" width="10%">→</td>
<td align="center" width="45%">

**The New Way**
```
"Show me my sprint work
 sorted by priority"
```
*Just ask.*

</td>
</tr>
</table>

<h2 align="center">JIRA Assistant Skills</h2>
<p align="center"><em>14 Claude Code skills that understand what you mean.</em></p>
```

**Pros:** Emotional resonance, immediate relatability
**Cons:** Requires more vertical space, may seem gimmicky
**Best for:** Frustrated JIRA users, non-technical stakeholders

---

## Option D: Conversation-First

**Philosophy:** Show the product being used. Let the demo sell itself.

```markdown
<p align="center">
  <img src="assets/logo-horizontal.svg" width="400">
</p>

<div align="center">

```
┌─────────────────────────────────────────────────────────────┐
│ You: "What's blocking the Q4 release?"                      │
├─────────────────────────────────────────────────────────────┤
│ Claude: Analyzing 147 issues across 3 projects...           │
│                                                             │
│ Found 4 blockers:                                           │
│ • PLATFORM-234: API rate limiting (blocked 12 issues)       │
│ • MOBILE-567: iOS signing certificate expired               │
│ • WEB-890: Pending security review                          │
│ • INFRA-123: Database migration not scheduled               │
│                                                             │
│ Recommended actions:                                        │
│ 1. Escalate PLATFORM-234 to @api-team (highest impact)      │
│ 2. MOBILE-567 can be resolved by @devops today              │
│ 3. WEB-890 needs @security-lead approval                    │
└─────────────────────────────────────────────────────────────┘
```

</div>

<p align="center">
  <strong>14 skills. 100+ scripts. Zero JQL required.</strong>
</p>
```

**Pros:** Shows actual value, self-explanatory
**Cons:** Lots of text, may not render well on mobile
**Best for:** Technical evaluators who want to see capabilities

---

## Option E: Video-Centric

**Philosophy:** A 30-second video is worth 10,000 words.

```markdown
<p align="center">
  <a href="https://youtube.com/watch?v=DEMO_ID">
    <img src="assets/video-thumbnail.png" alt="Watch Demo" width="700">
  </a>
</p>

<p align="center">
  <a href="https://youtube.com/watch?v=DEMO_ID">▶️ <strong>Watch the 60-second demo</strong></a>
</p>

<h1 align="center">JIRA Assistant Skills</h1>
<p align="center">
  Talk to JIRA like you talk to a teammate.<br>
  <sub>Natural language automation for Claude Code.</sub>
</p>
```

**Pros:** Highest engagement, shows real usage
**Cons:** Requires video production, YouTube dependency
**Best for:** Broad audiences, marketing-focused launch

---

## Option F: Stats-Driven Impact

**Philosophy:** Numbers speak louder than words.

```markdown
<h1 align="center">JIRA Assistant Skills</h1>

<table align="center">
<tr>
<td align="center">
<h2>10x</h2>
<sub>More context-efficient<br>than MCP servers</sub>
</td>
<td align="center">
<h2>14</h2>
<sub>Specialized skills<br>one conversation</sub>
</td>
<td align="center">
<h2>45s</h2>
<sub>Sprint planning<br>that took 2 hours</sub>
</td>
<td align="center">
<h2>0</h2>
<sub>JQL syntax<br>to memorize</sub>
</td>
</tr>
</table>

<p align="center">
  <em>Natural language JIRA automation for Claude Code</em>
</p>

<p align="center">
  <img src="assets/hero-demo.gif" width="600">
</p>
```

**Pros:** Scannable, impressive, memorable
**Cons:** Stats need to be defensible, can seem marketing-heavy
**Best for:** Decision-makers, executives evaluating tools

---

## Recommendation Matrix

| Option | Developer Appeal | PM/Lead Appeal | Visual Impact | Implementation Effort |
|--------|-----------------|----------------|---------------|----------------------|
| A: Minimal | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Low |
| B: Badge-Heavy | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Low |
| C: Problem-Solution | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Medium |
| D: Conversation | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Low |
| E: Video-Centric | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | High |
| F: Stats-Driven | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Medium |

---

## Suggested Approach

**Combine elements for maximum impact:**

1. Start with **Option F's stats** (immediate value)
2. Add **Option B's badges** (credibility)
3. Include **Option D's conversation** or **Option E's video** (demonstration)
4. End with **Option A's clean CTA** (clear next step)

This creates a funnel: Hook → Credibility → Proof → Action
