# Scenario: Handing Off to a Teammate

**Use this guide when:** You are transferring issue ownership to another person.

## The Situation

You need to transfer an issue to someone else (vacation, role change, expertise needed). You want to ensure smooth transition with no lost context.

## Quick Template

```bash
python add_comment.py PROJ-123 --format markdown --body "@new-assignee Taking over from @previous-assignee

**Current status:** [Where things stand]
**Completed:** [What is done]
**Remaining:** [What is left]
**Blockers:** [Any issues]
**Key context:** [Important comments or decisions to review]

@previous-assignee Please confirm handoff is complete."
```

## Example

```bash
python add_comment.py PROJ-123 --format markdown --body "@alice Taking over from @bob who is on leave.

**Current status:** API integration 60% complete
**Completed:**
- Authentication flow working
- GET endpoints implemented and tested

**Remaining:**
- POST/PUT/DELETE endpoints
- Error handling
- Integration tests

**Blockers:** None currently
**Key context:** See comment from Dec 20 about rate limiting strategy

@bob Please confirm I have the full context."
```

## Related Scripts

- `add_comment.py` - Post the handoff message
- `get_comments.py` - Review existing comments for context
- `get_activity.py` - See full history of changes
- `manage_watchers.py` - Add new assignee if not already watching

## Pro Tips

- List completed vs remaining work explicitly
- Point to key previous comments
- Ask for confirmation to ensure nothing is missed
- The outgoing person should acknowledge the handoff

---

[Back to GETTING_STARTED.md](../GETTING_STARTED.md)
