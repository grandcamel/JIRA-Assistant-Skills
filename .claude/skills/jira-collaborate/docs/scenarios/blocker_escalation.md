# Scenario: Escalating a Blocker

**Use this guide when:** You are stuck and need help from someone specific to proceed.

## The Situation

Work has stopped due to a dependency, missing information, or technical issue. You need to communicate the blocker clearly and request help.

## Quick Template

```bash
python add_comment.py PROJ-123 --format markdown --body "[BLOCKER] [Brief description]

**Blocked on:** [Specific dependency or issue]
**Duration:** [How long blocked]
**Impact:** [What cannot proceed]
**Need:** [Specific help required]

@person-who-can-help Please advise."
```

## Example

```bash
python add_comment.py PROJ-123 --format markdown --body "[BLOCKER] Database migration blocked

**Blocked on:** INFRA-456 - DBA approval for schema changes
**Duration:** Blocked for 2 business days
**Impact:** Cannot deploy v2.0 to staging, sprint at risk
**Need:** DBA review and approval by Friday

@dba-manager Can you help prioritize this review?"
```

## Related Scripts

- `add_comment.py` - Post the blocker notification
- `send_notification.py` - Send direct notification to escalation path
- `manage_watchers.py` - Add manager or lead to track resolution

## Notification Example

```bash
# Ensure the right people see it immediately
python send_notification.py PROJ-123 --users accountId123 \
  --subject "Blocker: DBA approval needed" \
  --body "Sprint at risk - need DBA review by Friday"
```

## Pro Tips

- Be specific about what you need (not just "help")
- Include duration to convey urgency
- Mention impact to help others prioritize
- Follow up after 24 hours if no response

---

[Back to GETTING_STARTED.md](../GETTING_STARTED.md)
