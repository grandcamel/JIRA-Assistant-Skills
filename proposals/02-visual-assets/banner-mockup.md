# Banner 2A: Gradient Tech - Design Specification

## Concept
A professional, developer-focused banner with a dark tech aesthetic featuring gradient accents, the terminal prompt logo, and a live terminal preview.

## Dimensions
- **Size:** 1280 x 320 pixels (GitHub standard banner size)
- **Format:** SVG (scalable) with PNG fallback

## Color Palette

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| Deep Navy | `#1a1a2e` | Primary background |
| Dark Blue | `#16213e` | Background gradient end |
| Atlassian Blue | `#0052CC` | Accent, prompt color |
| Purple | `#4a00e0` | Gradient accent |
| Cyan | `#00C7E6` | Cursor glow, highlights |
| Light Gray | `#e2e8f0` | Primary text |
| Muted Gray | `#94a3b8` | Secondary text |
| Slate | `#64748b` | Tertiary text |

## Layout Zones

```
+------------------------------------------------------------------+
|  [Code snippets faded]  |  LOGO + CONTENT  |  [Terminal preview] |
|  Left decorative zone   |  Central focus   |  Right interactive  |
|  ~180px                 |  ~500px          |  ~450px             |
+------------------------------------------------------------------+
```

### Left Zone (Decorative)
- Faded JQL snippets at 15% opacity
- Creates depth and context
- Hints at complexity being abstracted away

### Center Zone (Primary)
- Logo: Terminal prompt icon in circular frame
- Title: "JIRA ASSISTANT SKILLS" in bold sans-serif
- Tagline: "Talk to JIRA like you talk to a teammate"
- Stats bar: "14 skills | 100+ scripts | 0 JQL required"

### Right Zone (Demo)
- Mini terminal window with realistic frame
- Shows actual conversation example
- Demonstrates value proposition visually

## Typography

| Element | Font | Size | Weight | Color |
|---------|------|------|--------|-------|
| Title | Inter / Segoe UI | 48px | 700 | White |
| Tagline | Inter / Segoe UI | 22px | 400 | Light Gray |
| Stats | SF Mono + Inter | 14px | 600/400 | Cyan + Gray |
| Terminal | SF Mono | 13px | 400 | Mixed |

## Visual Effects

1. **Top/Bottom Accent Lines**
   - 3px gradient lines (Blue -> Purple -> Cyan)
   - 80% opacity for subtle framing

2. **Dot Pattern Texture**
   - Subtle dot grid at 3% opacity
   - Adds depth without distraction

3. **Gradient Orbs**
   - Large, soft circles at 5% opacity
   - Create ambient lighting effect

4. **Terminal Window**
   - macOS-style window controls
   - Dark theme matching overall design
   - Realistic code syntax highlighting

## Implementation Notes

### SVG Version (Included)
The `banner-gradient-tech.svg` file is production-ready with:
- All gradients defined
- Responsive scaling
- Embedded fonts with fallbacks
- Optimized file size

### PNG Export
For PNG export:
1. Open SVG in Figma/Illustrator
2. Ensure fonts are installed or converted to outlines
3. Export at 2x for retina displays (2560x640)
4. Compress with TinyPNG or similar

### Animated Version (Optional)
For an animated GIF version:
1. Add cursor blink animation
2. Add typing animation in terminal
3. Export as APNG or GIF
4. Keep under 1MB for web performance

## Accessibility

- **Contrast Ratio:** Title on background exceeds 7:1 (WCAG AAA)
- **Alt Text:** "JIRA Assistant Skills banner - Natural language interface for JIRA with 14 skills and 100+ scripts"

## Usage Guidelines

### Do
- Use on dark-themed pages
- Maintain aspect ratio when scaling
- Include with README.md hero section

### Don't
- Crop the terminal preview
- Add additional text overlays
- Use on light backgrounds without adaptation
