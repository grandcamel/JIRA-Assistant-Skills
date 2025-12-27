#!/bin/bash
#
# setup_assets.sh - Create asset directory structure for JIRA Assistant Skills README enhancement
#
# This script creates the directory structure and placeholder files needed for
# the README enhancement project. Run from the repository root.
#
# Usage:
#   chmod +x proposals/10-implementation/setup_assets.sh
#   ./proposals/10-implementation/setup_assets.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_step() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[-]${NC} $1"
}

# Banner
echo ""
echo "=============================================="
echo "  JIRA Assistant Skills - Asset Setup Script"
echo "=============================================="
echo ""

# Check if we're in the repository root
if [ ! -f "CLAUDE.md" ]; then
    print_error "This script must be run from the repository root."
    print_error "Please cd to the project root and try again."
    exit 1
fi

# Create main assets directory
print_step "Creating assets directory structure..."

mkdir -p assets/screenshots
mkdir -p assets/users
mkdir -p assets/icons

print_success "Created assets/ directory structure"

# Create .devcontainer directory
print_step "Creating .devcontainer directory..."

mkdir -p .devcontainer

print_success "Created .devcontainer/ directory"

# Create docs directory for GitHub Pages (optional)
print_step "Creating docs directory for GitHub Pages..."

mkdir -p docs/demo
mkdir -p docs/assets

print_success "Created docs/ directory structure"

# Create placeholder files with specifications
print_step "Creating placeholder files with specifications..."

# Logo placeholder
cat > assets/LOGO_SPEC.md << 'EOF'
# Logo Specifications

## Primary Logo (logo.svg, logo.png)
- **Concept**: Terminal prompt style (`> jira_`)
- **Dimensions**: 512x512 pixels
- **Format**: SVG (primary), PNG (fallback)
- **Max Size**: 50KB
- **Requirements**:
  - Must work on light backgrounds
  - Must work on dark backgrounds
  - Monochrome base with optional accent color
  - Scalable from 32px to 512px

## Horizontal Logo (logo-horizontal.svg, logo-horizontal.png)
- **Dimensions**: 400x100 pixels
- **Format**: SVG (primary), PNG (fallback)
- **Max Size**: 30KB
- **Use Case**: README header, documentation

## Favicon (favicon.ico)
- **Dimensions**: 32x32 pixels (with 16x16 variant)
- **Format**: ICO
- **Max Size**: 10KB
- **Use Case**: Browser tab, bookmarks

## Color Palette (Suggested)
- Primary Blue: #0052CC (JIRA Blue)
- Accent Purple: #4A00E0
- Dark Background: #1A1A2E
- Light Text: #FFFFFF
- Dark Text: #172B4D

## Design Tools
- Figma (recommended)
- Adobe Illustrator
- Inkscape (free alternative)
EOF

print_success "Created assets/LOGO_SPEC.md"

# Banner placeholder
cat > assets/BANNER_SPEC.md << 'EOF'
# Banner Specifications

## Technical Banner (banner.png)
- **Dimensions**: 1280x320 pixels (GitHub standard)
- **Format**: PNG
- **Max Size**: 200KB
- **Style**: Gradient tech banner with code snippets

## Design Elements
- **Background**: Deep blue (#1a1a2e) to Purple (#4a00e0) gradient
- **Logo**: Include horizontal logo on left
- **Text**: "JIRA ASSISTANT SKILLS" primary headline
- **Tagline**: "Talk to JIRA like you talk to a teammate"
- **Optional**: Subtle code/terminal elements

## Layout Guide
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

## Design Tools
- Figma (recommended)
- Canva (quick alternative)
- Adobe Photoshop
EOF

print_success "Created assets/BANNER_SPEC.md"

# Demo GIF placeholder
cat > assets/DEMO_SPEC.md << 'EOF'
# Demo GIF Specifications

## Primary Demo (demo.gif)
- **Dimensions**: 800x500 pixels
- **Format**: GIF
- **Max Size**: 5MB
- **Duration**: 15-30 seconds
- **Frame Rate**: 10-15 fps (for file size)

## Content Sequence
1. Show terminal prompt
2. Type natural language query
3. Show "thinking" indicator
4. Display formatted response
5. Optional: Show follow-up action

## Recording Tools

### VHS (Recommended)
```bash
# Install
brew install vhs

# Create tape file and generate GIF
vhs demo.tape
```

### asciinema + agg
```bash
# Install
brew install asciinema agg

# Record
asciinema rec demo.cast

# Convert to GIF
agg demo.cast demo.gif --theme dracula
```

## Sample VHS Tape File (demo.tape)
```tape
Output demo.gif
Set FontSize 18
Set Width 800
Set Height 500
Set Theme "Dracula"
Set Padding 20
Set WindowBar Colorful

Type "# JIRA Assistant Skills Demo"
Enter
Sleep 1s

Type "claude 'What's blocking the Q4 release?'"
Enter
Sleep 3s

# Simulated output would be typed here
```

## Quality Checklist
- [ ] Text is readable at 800px width
- [ ] Colors work on light/dark GitHub themes
- [ ] Loop is smooth (no jarring restart)
- [ ] File size under 5MB
EOF

print_success "Created assets/DEMO_SPEC.md"

# Screenshots placeholder
cat > assets/screenshots/README.md << 'EOF'
# Screenshots Directory

Store screenshots here for documentation and marketing.

## Recommended Screenshots

| Name | Description | Dimensions |
|------|-------------|------------|
| terminal-output.png | Formatted CLI output | 1200x750 |
| ide-integration.png | VS Code with Claude Code | 1200x750 |
| jira-result.png | JIRA issue created by skill | 1200x750 |
| conversation.png | Multi-turn conversation | 1200x750 |

## Screenshot Guidelines
- Use consistent terminal theme (Dracula recommended)
- Blur or redact any sensitive information
- Include relevant context in frame
- Optimize PNG files for web
EOF

print_success "Created assets/screenshots/README.md"

# Users placeholder (for future logos)
cat > assets/users/README.md << 'EOF'
# User Logos Directory

When organizations adopt JIRA Assistant Skills and agree to be featured,
add their logos here.

## Requirements
- Explicit permission from organization
- Logo height: 40px standard
- Transparent background preferred
- Link to organization website

## Adding a User
1. Obtain written permission
2. Add logo file (PNG or SVG)
3. Update README "Used By" section
EOF

print_success "Created assets/users/README.md"

# Icons placeholder
cat > assets/icons/README.md << 'EOF'
# Icons Directory

Skill-specific icons and UI elements.

## Icon Categories
- Skill icons (14 skills)
- Action icons (create, search, update, etc.)
- Status icons (success, error, warning)
EOF

print_success "Created assets/icons/README.md"

# Create devcontainer.json
cat > .devcontainer/devcontainer.json << 'EOF'
{
  "name": "JIRA Assistant Skills Demo",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "postCreateCommand": "pip install -r .claude/skills/shared/scripts/lib/requirements.txt",
  "customizations": {
    "vscode": {
      "settings": {
        "terminal.integrated.defaultProfile.linux": "bash",
        "python.defaultInterpreterPath": "/usr/local/bin/python"
      },
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance"
      ]
    }
  },
  "features": {
    "ghcr.io/devcontainers/features/git:1": {}
  },
  "remoteEnv": {
    "JIRA_DEMO_MODE": "true"
  }
}
EOF

print_success "Created .devcontainer/devcontainer.json"

# Create sample VHS tape file
cat > demo.tape << 'EOF'
# JIRA Assistant Skills Demo
# Generate with: vhs demo.tape
# Install VHS: brew install vhs

Output assets/demo.gif

Set FontSize 18
Set Width 800
Set Height 500
Set Theme "Dracula"
Set Padding 20
Set Margin 10
Set BorderRadius 10
Set WindowBar Colorful
Set TypingSpeed 50ms

# Introduction
Type "# JIRA Assistant Skills Demo"
Enter
Sleep 500ms
Enter

# Example 1: Natural language search
Type "# Ask a question in plain English:"
Enter
Sleep 500ms

Type "claude 'Show my high priority bugs in the current sprint'"
Enter
Sleep 2s

# Simulated response
Type "Found 3 high priority bugs:"
Enter
Type "  PROJ-123: Login fails on Safari [Critical]"
Enter
Type "  PROJ-456: Payment timeout at checkout [High]"
Enter
Type "  PROJ-789: Search results incomplete [High]"
Enter
Enter
Sleep 1s

# Example 2: Create issue
Type "# Create issues naturally:"
Enter
Sleep 500ms

Type "claude 'Create a bug: API returns 500 on /users endpoint'"
Enter
Sleep 2s

Type "Created PROJ-890: API returns 500 on /users endpoint"
Enter
Type "  Type: Bug | Priority: Medium | Status: Open"
Enter
Enter
Sleep 1s

# Closing
Type "# 14 skills. 100+ scripts. Zero JQL required."
Enter
Sleep 2s
EOF

print_success "Created demo.tape"

# Create GitHub Pages placeholder files
cat > docs/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JIRA Assistant Skills - Documentation</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
            color: #333;
        }
        h1 {
            color: #0052CC;
        }
        a {
            color: #0052CC;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 8px;
        }
        .badge-blue { background: #0052CC; color: white; }
        .badge-green { background: #36B37E; color: white; }
    </style>
</head>
<body>
    <h1>JIRA Assistant Skills</h1>
    <p>
        <span class="badge badge-blue">14 Skills</span>
        <span class="badge badge-green">100+ Scripts</span>
    </p>
    <p>Natural language JIRA automation for Claude Code.</p>

    <h2>Quick Links</h2>
    <ul>
        <li><a href="https://github.com/grandcamel/jira-assistant-skills">GitHub Repository</a></li>
        <li><a href="demo/">Interactive Demo</a></li>
        <li><a href="https://github.com/grandcamel/jira-assistant-skills#quick-start">Quick Start Guide</a></li>
    </ul>

    <h2>Getting Started</h2>
    <p>Add the skills to your Claude Code project and start asking questions in plain English.</p>

    <pre><code>claude "Show me my open bugs"
claude "Create a story: Implement dark mode"
claude "What's blocking the release?"</code></pre>
</body>
</html>
EOF

print_success "Created docs/index.html"

cat > docs/demo/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JIRA Assistant Skills - Demo</title>
    <link rel="stylesheet" href="https://unpkg.com/termynal@0.0.1/termynal.css">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
            background: #1a1a2e;
            color: #fff;
        }
        h1 {
            text-align: center;
            color: #fff;
        }
        .termynal {
            max-width: 800px;
            margin: 2rem auto;
        }
        .back-link {
            display: block;
            text-align: center;
            margin-top: 2rem;
            color: #4ECDC4;
        }
    </style>
</head>
<body>
    <h1>JIRA Assistant Skills Demo</h1>

    <div id="termynal" data-termynal data-ty-typeDelay="40" data-ty-lineDelay="700">
        <span data-ty="input">claude "What's blocking the Q4 release?"</span>
        <span data-ty="progress"></span>
        <span data-ty>Analyzing 147 issues across 3 projects...</span>
        <span data-ty>&nbsp;</span>
        <span data-ty>Found 4 blockers:</span>
        <span data-ty>  - PLATFORM-234: API rate limiting (blocking 12 issues)</span>
        <span data-ty>  - MOBILE-567: iOS signing certificate expired</span>
        <span data-ty>  - WEB-890: Pending security review</span>
        <span data-ty>  - INFRA-123: Database migration not scheduled</span>
        <span data-ty>&nbsp;</span>
        <span data-ty="input">claude "Create bug: Login fails on Safari with error 500"</span>
        <span data-ty="progress"></span>
        <span data-ty>Created PROJ-456: Login fails on Safari with error 500</span>
        <span data-ty>  Type: Bug | Priority: Medium | Status: Open</span>
    </div>

    <a href="../" class="back-link">Back to Documentation</a>

    <script src="https://unpkg.com/termynal@0.0.1/termynal.js"></script>
</body>
</html>
EOF

print_success "Created docs/demo/index.html"

# Create .gitkeep files for empty directories
touch assets/screenshots/.gitkeep
touch assets/users/.gitkeep
touch assets/icons/.gitkeep
touch docs/assets/.gitkeep

print_success "Created .gitkeep files"

# Summary
echo ""
echo "=============================================="
echo "  Setup Complete!"
echo "=============================================="
echo ""
print_success "Directory structure created:"
echo ""
echo "  assets/"
echo "  ├── LOGO_SPEC.md"
echo "  ├── BANNER_SPEC.md"
echo "  ├── DEMO_SPEC.md"
echo "  ├── screenshots/"
echo "  ├── users/"
echo "  └── icons/"
echo ""
echo "  .devcontainer/"
echo "  └── devcontainer.json"
echo ""
echo "  docs/"
echo "  ├── index.html"
echo "  ├── demo/"
echo "  │   └── index.html"
echo "  └── assets/"
echo ""
echo "  demo.tape"
echo ""
print_step "Next steps:"
echo "  1. Create logo using assets/LOGO_SPEC.md as guide"
echo "  2. Create banner using assets/BANNER_SPEC.md as guide"
echo "  3. Run 'vhs demo.tape' to generate demo GIF"
echo "  4. Update README.md with new assets"
echo ""
print_warning "Note: VHS requires installation: brew install vhs"
echo ""
