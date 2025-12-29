# Getting Started with JIRA Collaboration

Quick guide to start collaborating on JIRA issues in under 5 minutes.

## First 5 Minutes

### 1. Add a Comment

```bash
python add_comment.py PROJ-123 --body "Starting work on this now"
```

### 2. Upload Evidence

```bash
python upload_attachment.py PROJ-123 --file screenshot.png
```

### 3. Notify the Team

```bash
python send_notification.py PROJ-123 --watchers --subject "Update" --body "Issue resolved"
```

## Most Common Commands

| Task | Command |
|------|---------|
| Add comment | `python add_comment.py PROJ-123 --body "text"` |
| Rich text comment | `python add_comment.py PROJ-123 --body "**bold**" --format markdown` |
| Upload file | `python upload_attachment.py PROJ-123 --file myfile.pdf` |
| List attachments | `python download_attachment.py PROJ-123 --list` |
| Add watcher | `python manage_watchers.py PROJ-123 --add user@company.com` |
| View history | `python get_activity.py PROJ-123 --format table` |

## Next Steps

Choose a scenario that matches your current situation:

- [Starting work on an issue](scenarios/starting_work.md)
- [Providing a progress update](scenarios/progress_update.md)
- [Escalating a blocker](scenarios/blocker_escalation.md)
- [Handing off to a teammate](scenarios/handoff.md)
- [Sharing test evidence](scenarios/sharing_evidence.md)

## Quick Tips

1. **Use `--help`** on any script for full options
2. **Use `--dry-run`** before sending notifications
3. **Use `--format markdown`** for formatted comments
4. **Use `--visibility-role`** for internal comments

---

[Back to SKILL.md](../SKILL.md) | [Quick Reference](QUICK_REFERENCE.md)
