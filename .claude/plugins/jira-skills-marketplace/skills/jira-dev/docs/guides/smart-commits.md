# Smart Commits Guide

**Read time:** 5 minutes

Smart Commits allow you to perform JIRA actions directly from commit messages.

## Syntax

```
<text> <ISSUE-KEY> <text> #<command> <arguments>
```

## Available Commands

### #comment - Add Comments

```bash
git commit -m "PROJ-123 #comment Fixed the login bug"

git commit -m "PROJ-456 #comment This requires review"
```

### #time - Log Work

```bash
git commit -m "PROJ-123 #time 2h Fixed authentication"

git commit -m "PROJ-456 #time 1d 4h Implemented payment processing"
```

**Time formats:**
| Format | Meaning |
|--------|---------|
| `30m` | 30 minutes |
| `2h` | 2 hours |
| `1d` | 1 day (8 hours) |
| `1w` | 1 week (5 days) |
| `2h 30m` | 2 hours 30 minutes |

### #transition - Change Status

```bash
git commit -m "PROJ-123 #in-progress Starting work"

git commit -m "PROJ-456 #done Fixed and tested"
```

**Common transitions:**
| Command | Status |
|---------|--------|
| `#start` | Start Progress |
| `#stop` | Stop Progress |
| `#in-review` | In Review |
| `#done` | Done |
| `#close` | Closed |

## Combining Commands

```bash
# Comment + time
git commit -m "PROJ-123 #comment Fixed auth bug #time 2h"

# Transition + comment
git commit -m "PROJ-456 #done #comment All tests passing"

# All three
git commit -m "PROJ-789 #in-review #time 3h #comment Ready for review"
```

## Requirements

1. **Email must match:** Git email must exactly match JIRA user email
   ```bash
   git config user.email "your.email@company.com"
   ```

2. **Integration required:** JIRA must have Git integration installed

3. **Permissions:** User must have permission to comment, log work, and transition

4. **Issue key format:** Must use UPPERCASE: `PROJ-123` not `proj-123`

## Workflow Examples

**Starting work:**
```bash
git commit -m "PROJ-123 #start #comment Beginning implementation"
```

**During development:**
```bash
git commit -m "PROJ-123 #time 1h #comment Added validation logic"
```

**Code review:**
```bash
git commit -m "PROJ-123 #in-review #comment PR created"
```

**Completing work:**
```bash
git commit -m "PROJ-123 #done #time 1h #comment All tests passing"
```

## Common Mistakes

| Wrong | Correct | Issue |
|-------|---------|-------|
| `proj-123 #done` | `PROJ-123 #done` | Lowercase key |
| `PROJ-123#done` | `PROJ-123 #done` | Missing space |
| `PROJ-123 #finish` | `PROJ-123 #done` | Invalid transition |

## Troubleshooting

**Smart commits not working?**
1. Check Git email matches JIRA user exactly
2. Verify issue key is UPPERCASE
3. Ensure space before `#command`
4. Check user has required permissions

## Next Steps

- [PR Best Practices](pr-workflows.md) - Pull request patterns
- [Development Panel](development-panel.md) - View Git activity in JIRA
