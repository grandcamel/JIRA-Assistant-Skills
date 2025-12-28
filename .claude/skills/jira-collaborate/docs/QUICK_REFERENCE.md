# Quick Reference

Fast lookup for common collaboration tasks.

---

## Essential Scripts

| Task | Command |
|------|---------|
| Add comment | `python add_comment.py PROJ-123 --body "text"` |
| Markdown comment | `python add_comment.py PROJ-123 --body "**bold**" --format markdown` |
| Internal comment | `python add_comment.py PROJ-123 --body "text" --visibility-role Administrators` |
| Upload file | `python upload_attachment.py PROJ-123 --file myfile.pdf` |
| List attachments | `python download_attachment.py PROJ-123 --list` |
| Download file | `python download_attachment.py PROJ-123 --name "file.png"` |
| Add watcher | `python manage_watchers.py PROJ-123 --add user@company.com` |
| Notify watchers | `python send_notification.py PROJ-123 --watchers --subject "Update" --body "text"` |
| View history | `python get_activity.py PROJ-123 --format table` |

---

## JQL for Collaboration

```jql
# Issues I am watching
watcher = currentUser() AND status NOT IN (Done, Closed)

# Issues where I have commented
issueFunction in commented("by currentUser()")

# Watched issues updated recently
updated >= -1d AND watcher = currentUser()

# Issues needing my attention
(assignee = currentUser() OR watcher = currentUser()) AND status = "Awaiting Input"

# Blocked issues I am watching
watcher = currentUser() AND (status = Blocked OR "Flagged" = Impediment)
```

---

## Keyboard Shortcuts (JIRA UI)

| Key | Action |
|-----|--------|
| `m` | Comment on issue |
| `a` | Assign to me |
| `e` | Edit issue |
| `.` | Open operations menu |
| `w` | Watch/unwatch issue |

---

## When to Use What

| Need | Tool |
|------|------|
| Issue-specific update | JIRA comment |
| Immediate attention | @mention in JIRA |
| Ongoing visibility | Add as watcher |
| Real-time discussion | Slack, then summarize in JIRA |
| Document collaboration | Confluence, link from JIRA |
| Code review | GitHub/Bitbucket, link from JIRA |
| Mass notification | `send_notification.py` |
| Share files | Upload (< 5MB) or link to storage |
| Track who did what | `get_activity.py` |

---

## Checklists

### Before Sending Notification

- [ ] Used `--dry-run` to preview recipients
- [ ] Subject is clear and actionable
- [ ] Body explains what is needed
- [ ] Only necessary recipients included

### Before Uploading Attachment

- [ ] Descriptive filename with date
- [ ] File size under 5MB
- [ ] Sensitive data redacted
- [ ] Will add explanatory comment

### Before Adding Comment

- [ ] Clear and concise (2-5 sentences)
- [ ] Provides context (why, not just what)
- [ ] @mentions only people who need to act
- [ ] Links to external resources included

---

## Common Options (All Scripts)

| Option | Description |
|--------|-------------|
| `--profile <name>` | JIRA profile to use |
| `--help`, `-h` | Show detailed help |

For script-specific options: `python <script>.py --help`

---

[Back to GETTING_STARTED.md](GETTING_STARTED.md) | [Templates](TEMPLATES.md)
