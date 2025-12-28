# Interactive Demo Options

## Overview
Interactive demos let users experience JIRA Assistant Skills without installation. These range from simple embedded terminals to full sandbox environments.

---

## 1. Embedded Terminal Demos

### Option 8A: asciinema Embedded Player
**Concept:** Recorded terminal session with playback controls

```html
<!-- Embed in README or docs -->
<a href="https://asciinema.org/a/YOUR_RECORDING_ID">
  <img src="https://asciinema.org/a/YOUR_RECORDING_ID.svg" />
</a>
```

**Features:**
- Play/pause controls
- Speed adjustment
- Copy-paste from recording
- No server required

**Pros:**
- Free, easy to create
- Works on GitHub README
- Lightweight

**Cons:**
- Not truly interactive
- Pre-recorded only
- Limited customization

**Implementation:**
1. Install asciinema: `brew install asciinema`
2. Record: `asciinema rec demo.cast`
3. Upload to asciinema.org
4. Embed SVG in README

---

### Option 8B: Termynal (Fake Terminal Animation)
**Concept:** CSS/JS animated terminal that types commands

```html
<div id="termynal" data-termynal>
  <span data-ty="input">claude "Create a bug for login failing"</span>
  <span data-ty="progress"></span>
  <span data-ty>✅ Created PROJ-456: Login failing</span>
  <span data-ty>   Type: Bug | Priority: Medium</span>
  <span data-ty>   Status: Open | Assignee: Unassigned</span>
</div>
```

**Features:**
- Typing animation
- Customizable speed
- No recording needed

**Pros:**
- Lightweight (< 10KB)
- Works anywhere (GitHub Pages)
- Easy to update

**Cons:**
- Fake, not real output
- Limited interactivity
- Scripted only

**Implementation:**
- Use [Termynal](https://github.com/ines/termynal) library
- Host on GitHub Pages

---

### Option 8C: VHS GIF with Annotations
**Concept:** Scripted terminal recordings with custom styling

```tape
# demo.tape
Output demo.gif
Set FontSize 20
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"
Set Padding 20
Set Margin 10
Set BorderRadius 10
Set WindowBar Colorful

Type "# 🚀 JIRA Assistant Skills Demo"
Enter
Sleep 1s

Type "claude 'What bugs are blocking the release?'"
Enter
Sleep 2s

# Simulated output
Type "Found 3 blockers:"
Enter
Type "  • PROJ-123: API rate limit (blocking 12 issues)"
Enter
Type "  • PROJ-456: SSL certificate expired"
Enter
Type "  • PROJ-789: Database migration pending"
Enter
```

**Pros:**
- Beautiful, customizable
- Reproducible (scripted)
- Works as GIF anywhere

**Cons:**
- Still not interactive
- Requires VHS tool setup

---

## 2. Live Sandbox Environments

### Option 8D: GitHub Codespaces
**Concept:** One-click cloud development environment

```json
// .devcontainer/devcontainer.json
{
  "name": "JIRA Assistant Skills Demo",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "postCreateCommand": "pip install -r requirements.txt",
  "customizations": {
    "vscode": {
      "extensions": ["anthropic.claude-code"]
    }
  }
}
```

**Features:**
- Full VS Code in browser
- Pre-configured environment
- 60 hours/month free

**Pros:**
- Real environment
- No local setup
- Quick to launch

**Cons:**
- Requires GitHub account
- Limited free hours
- No real JIRA connection (need mock)

**Implementation:**
1. Add `.devcontainer/devcontainer.json`
2. Add "Open in Codespaces" badge to README
3. Include demo script with mock data

---

### Option 8E: Gitpod Workspace
**Concept:** Similar to Codespaces, alternative provider

```yaml
# .gitpod.yml
image: gitpod/workspace-python

tasks:
  - name: Setup
    init: pip install -r requirements.txt
    command: echo "Ready! Try: python demo.py"

vscode:
  extensions:
    - anthropic.claude-code
```

**Pros:**
- 50 hours/month free
- Works with any Git provider
- Pre-configured

**Cons:**
- Another account to create
- Similar limitations to Codespaces

---

### Option 8F: StackBlitz / CodeSandbox
**Concept:** In-browser code playground

**Note:** These are primarily for JavaScript/web projects. Less suitable for Python CLI tools.

**Alternative approach:**
- Create a web-based simulator that mimics CLI behavior
- Host as static site on GitHub Pages

---

## 3. Mock Demo Environments

### Option 8G: Demo Mode with Mock Data
**Concept:** Built-in demo mode that uses fake JIRA data

```python
# demo_mode.py
DEMO_ISSUES = [
    {"key": "DEMO-1", "summary": "Login button not working", "type": "Bug"},
    {"key": "DEMO-2", "summary": "Add dark mode", "type": "Story"},
    {"key": "DEMO-3", "summary": "Improve search speed", "type": "Task"},
]

# Usage: python script.py --demo-mode
```

**Pros:**
- No JIRA credentials needed
- Safe to experiment
- Consistent demo experience

**Cons:**
- Not real data
- May confuse users
- Maintenance overhead

**Implementation:**
1. Add `--demo-mode` flag to key scripts
2. Create mock data fixtures
3. Intercept JIRA client calls in demo mode

---

### Option 8H: Interactive Tutorial Mode
**Concept:** Guided walkthrough with prompts

```
$ python demo.py --interactive

╔══════════════════════════════════════════════════════════════╗
║              JIRA Assistant Skills Demo                       ║
╠══════════════════════════════════════════════════════════════╣
║  Welcome! This demo will walk you through key features.      ║
║                                                               ║
║  [1] Create an issue                                          ║
║  [2] Search for issues                                        ║
║  [3] Transition an issue                                      ║
║  [4] Log time                                                 ║
║  [5] Exit                                                     ║
╚══════════════════════════════════════════════════════════════╝

Choose an option (1-5):
```

**Pros:**
- Guided experience
- Low learning curve
- Showcases features

**Cons:**
- Development effort
- May feel artificial

---

## 4. Web-Based Demos

### Option 8I: GitHub Pages Demo Site
**Concept:** Static website with interactive elements

**Structure:**
```
docs/
├── index.html        # Landing page
├── demo/
│   ├── terminal.html # Fake terminal demo
│   └── commands.json # Demo script data
├── try/
│   └── index.html    # "Try it" interactive page
└── assets/
    └── termynal.js   # Terminal animation
```

**Features:**
- Animated terminal demos
- Command reference
- Interactive command builder
- Link to actual repo

**Pros:**
- Free hosting (GitHub Pages)
- No backend needed
- SEO benefits

**Cons:**
- Not real execution
- Development time

---

### Option 8J: Command Playground
**Concept:** Web form that shows what command would run

```html
<div class="playground">
  <h3>Build Your Command</h3>

  <label>Action:</label>
  <select id="action">
    <option>Create issue</option>
    <option>Search issues</option>
    <option>Transition issue</option>
  </select>

  <label>Issue Type:</label>
  <select id="type">
    <option>Bug</option>
    <option>Story</option>
    <option>Task</option>
  </select>

  <label>Summary:</label>
  <input type="text" id="summary" placeholder="Login button broken">

  <div class="output">
    <code>claude "Create a Bug: Login button broken"</code>
  </div>
</div>
```

**Pros:**
- Interactive without backend
- Teaches command structure
- Easy to implement

**Cons:**
- Doesn't execute anything
- May confuse users

---

## 5. Video Game-Style Tutorials

### Option 8K: Step-by-Step Quest
**Concept:** Gamified onboarding experience

```
╔════════════════════════════════════════════════════════════╗
║  JIRA ASSISTANT SKILLS - Training Quest                     ║
╠════════════════════════════════════════════════════════════╣
║                                                              ║
║  Quest 1: Your First Issue                                   ║
║  ────────────────────────────────────                        ║
║  Your team lead just asked you to create a bug report.      ║
║                                                              ║
║  🎯 Goal: Create a bug called "Homepage loads slowly"        ║
║                                                              ║
║  💡 Hint: Try saying "Create a bug: Homepage loads slowly"   ║
║                                                              ║
║  Type your command:                                          ║
║  > _                                                         ║
║                                                              ║
║  [Press Enter to continue]                                   ║
╚════════════════════════════════════════════════════════════╝
```

**Pros:**
- Engaging, fun
- Teaches by doing
- Progress tracking

**Cons:**
- Significant development
- May seem gimmicky to some

---

## 6. Implementation Priority

### Tier 1: Quick Wins (1-2 days)
| Option | Effort | Impact |
|--------|--------|--------|
| 8A: asciinema embed | 1 hour | Medium |
| 8B: Termynal animation | 2 hours | Medium |
| 8C: VHS GIF | 2 hours | High |

### Tier 2: Medium Effort (1 week)
| Option | Effort | Impact |
|--------|--------|--------|
| 8D: Codespaces config | 4 hours | High |
| 8I: GitHub Pages site | 3 days | High |
| 8J: Command Playground | 2 days | Medium |

### Tier 3: Full Development (2+ weeks)
| Option | Effort | Impact |
|--------|--------|--------|
| 8G: Demo mode | 1 week | High |
| 8H: Interactive tutorial | 2 weeks | High |
| 8K: Quest system | 3 weeks | High |

---

## 7. README Integration

### Option 8L: Minimal Demo Section
```markdown
## Try It

<a href="https://asciinema.org/a/XXXXX">
  <img src="https://asciinema.org/a/XXXXX.svg" width="600" />
</a>

[▶️ Watch the full demo](https://youtube.com/watch?v=XXXXX) | [🚀 Open in Codespaces](https://codespaces.new/grandcamel/jira-assistant-skills)
```

### Option 8M: Interactive Demo Section
```markdown
## Try It Now

<div align="center">

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/grandcamel/jira-assistant-skills)

</div>

**No JIRA account?** Try our [interactive demo](https://grandcamel.github.io/jira-assistant-skills/demo) with sample data.

**Quick preview:**

<p align="center">
  <img src="assets/demo.gif" alt="Demo" width="600">
</p>
```

---

## Recommendation

**Immediate (This Week):**
1. **Option 8C (VHS GIF)** - Create polished terminal demo GIF
2. **Option 8D (Codespaces)** - Add devcontainer.json for one-click setup

**Short Term (This Month):**
3. **Option 8I (GitHub Pages)** - Create demo site with Termynal animations
4. **Option 8A (asciinema)** - Record real terminal sessions

**Long Term (Future):**
5. **Option 8G (Demo Mode)** - Build mock data layer for offline demos
6. **Option 8H (Interactive Tutorial)** - Create guided onboarding

---

## Technical Requirements

### For VHS (Recommended for GIFs)
```bash
# Install
brew install vhs

# Create tape file
cat > demo.tape << 'EOF'
Output demo.gif
Set FontSize 18
Set Width 1000
Set Height 500
Set Theme "Dracula"

Type "claude 'Show my sprint work'"
Enter
Sleep 3s
EOF

# Generate GIF
vhs demo.tape
```

### For Codespaces
```json
// .devcontainer/devcontainer.json
{
  "name": "JIRA Assistant Demo",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "postCreateCommand": "pip install -r .claude/skills/shared/scripts/lib/requirements.txt",
  "customizations": {
    "vscode": {
      "settings": {
        "terminal.integrated.defaultProfile.linux": "bash"
      }
    }
  }
}
```

### For GitHub Pages Demo Site
```yaml
# .github/workflows/pages.yml
name: Deploy Demo Site
on:
  push:
    branches: [main]
    paths: [docs/**]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```
