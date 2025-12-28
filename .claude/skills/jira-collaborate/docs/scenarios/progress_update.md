# Scenario: Providing a Progress Update

**Use this guide when:** Work is underway and you want to share status with the team.

## The Situation

You have made progress on an issue and want to keep stakeholders informed without cluttering the comment history with unnecessary updates.

## Quick Template

```bash
python add_comment.py PROJ-123 --format markdown --body "## Update: [Brief title]

**Status:** On track | At risk | Blocked
**Progress:** [What is completed]
**Next steps:** [What comes next]"
```

## Example

```bash
python add_comment.py PROJ-123 --format markdown --body "## Update: API Integration

**Status:** On track
**Progress:** Completed authentication module, GET endpoints working
**Next steps:** Implementing POST/PUT endpoints tomorrow"
```

**Output in JIRA:**

> ## Update: API Integration
>
> **Status:** On track
> **Progress:** Completed authentication module, GET endpoints working
> **Next steps:** Implementing POST/PUT endpoints tomorrow

## Related Scripts

- `add_comment.py` - Post your progress update
- `upload_attachment.py` - Attach evidence of progress (screenshots, logs)
- `get_activity.py` - Review what has changed on the issue

## Pro Tips

- Update at meaningful milestones, not every minor change
- Front-load the status (On track/At risk/Blocked) for quick scanning
- Link to PRs or Confluence docs rather than pasting full content

---

[Back to GETTING_STARTED.md](../GETTING_STARTED.md)
