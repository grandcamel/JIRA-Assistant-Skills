# Time Format Quick Reference

Quick lookup table for JIRA time format syntax.

---

## Time Format Syntax

| Format | Meaning | Seconds | Example Use |
|--------|---------|---------|-------------|
| `15m` | 15 minutes | 900 | Quick fix |
| `30m` | 30 minutes | 1,800 | Code review |
| `1h` | 1 hour | 3,600 | Small task |
| `2h` | 2 hours | 7,200 | Bug fix |
| `4h` | 4 hours | 14,400 | Half day |
| `1d` | 1 day | 28,800 | Full day (8h) |
| `2d` | 2 days | 57,600 | Standard story |
| `1w` | 1 week | 144,000 | 5 days (40h) |

## Combined Formats

| Format | Total Time | Seconds |
|--------|------------|---------|
| `1h 30m` | 1.5 hours | 5,400 |
| `2h 15m` | 2.25 hours | 8,100 |
| `1d 4h` | 12 hours | 43,200 |
| `2d 4h 30m` | 20.5 hours | 73,800 |
| `1w 2d` | 7 days | 201,600 |
| `1w 3d 2h 30m` | 65 hours | 234,000 |

## Common Task Estimates

| Task Type | Typical Format | Hours |
|-----------|----------------|-------|
| Trivial fix | `15m` to `30m` | 0.25-0.5 |
| Quick fix | `1h` | 1 |
| Small bug | `2h` to `4h` | 2-4 |
| Code review | `30m` to `1h` | 0.5-1 |
| Daily standup | `15m` | 0.25 |
| Sprint planning | `2h` to `4h` | 2-4 |
| Standard story | `1d` to `2d` | 8-16 |
| Complex feature | `3d` to `1w` | 24-40 |

## Invalid Formats (Don't Use)

| Incorrect | Correct | Problem |
|-----------|---------|---------|
| `2 hours` | `2h` | Spaces not allowed |
| `1.5h` | `1h 30m` | Decimals not supported |
| `90 minutes` | `1h 30m` | Must use abbreviations |
| `0.5d` | `4h` | No decimal days |
| `120min` | `2h` | Use "m" not "min" |

## Default Unit Configuration

**JIRA defaults (configurable by admin):**
- 1 minute = 60 seconds
- 1 hour = 60 minutes
- **1 day = 8 hours**
- **1 week = 5 days (40 hours)**

**Note:** Check your organization's configuration in:
`JIRA Settings > System > Time Tracking`

---

**Back to:** [SKILL.md](../../SKILL.md) | [Best Practices](../BEST_PRACTICES.md)
