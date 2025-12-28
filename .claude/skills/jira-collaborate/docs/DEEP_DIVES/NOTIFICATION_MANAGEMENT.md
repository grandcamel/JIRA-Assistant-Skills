# Notification Management Deep Dive

[Back to Index](../INDEX.md) | [Back to Quick Reference](../QUICK_REFERENCE.md)

---

Advanced guidance on managing notifications and preventing overload.

## The Notification Overload Problem

**Common complaint:** "I get too many JIRA emails and ignore them all."

**Root causes:**
- Autowatch enabled globally
- Notification scheme includes all project members
- No distinction between important and routine updates
- Batch notifications not enabled

**Solution:** Targeted, relevant notifications only.

## Notification Event Configuration

| Event | Who Should Get Notified |
|-------|-------------------------|
| Issue Created | Assignee, Reporter, Watchers |
| Issue Updated | Assignee, Watchers |
| Issue Commented | Assignee, Watchers, @mentioned users |
| Issue Assigned | New assignee, Reporter |
| Issue Transitioned | Assignee, Reporter, Watchers |
| Issue Resolved | Reporter, Watchers |
| @Mentioned in comment | Mentioned user only |

**Who to exclude:**
- "All project members" (too broad)
- "All developers" (use specific roles)
- Email groups (unless explicitly needed)

## Using send_notification.py

**When to use manual notifications:**
- Escalations requiring immediate attention
- Important announcements about specific issues
- Soliciting feedback from specific group
- Handoffs or delegation

```bash
# Notify all watchers about critical update
python send_notification.py PROD-123 --watchers \
  --subject "Critical: Production fix deployed" \
  --body "Fix for login timeout deployed. Please monitor."

# Notify specific users
python send_notification.py PROJ-456 --users accountId1 accountId2 \
  --subject "Review needed" \
  --body "Please review architecture changes."

# Notify assignee and reporter
python send_notification.py PROJ-789 --assignee --reporter \
  --subject "Status update required" \
  --body "Issue idle for 5 days. Please provide update."
```

## Dry-Run Best Practice

**Always use --dry-run first for important notifications:**

```bash
# Step 1: Preview recipients
python send_notification.py PROJ-123 --watchers --groups leadership \
  --subject "Important update" --body "Message text" --dry-run

# Step 2: Review output, verify recipients

# Step 3: Send for real (remove --dry-run)
python send_notification.py PROJ-123 --watchers --groups leadership \
  --subject "Important update" --body "Message text"
```

## Notification Batching

**Problem:** Individual emails for every update causes inbox fatigue.

**Solution:** Enable notification batching.

**Recommended settings:**
- Developers: Hourly batches during work hours
- Managers: Daily digest at 9 AM
- On-call/support: Immediate (no batching)

## @Mention vs Watcher

**Key difference:**
- **@Mention:** One-time notification for immediate attention
- **Watcher:** Ongoing notifications for all updates

**Use @mention when:**
- Asking for specific input
- Escalating an issue
- Requesting feedback
- Handoff communication

**Add as watcher instead when:**
- They need ongoing visibility (stakeholder tracking)
- They are part of the broader team context
- They may contribute later
- You are not asking them to act immediately

## Decision Tree

```
Need someone's attention?
|
+-- Immediate action required?
|   +-- YES -> Use @mention in comment
|   +-- NO -> Continue
|
+-- Need ongoing visibility?
|   +-- YES -> Add as watcher
|   +-- NO -> Use @mention in comment
|
+-- Already assigned to issue?
    +-- YES -> Just comment (no mention/watcher needed)
    +-- NO -> @mention for one-time OR watcher for ongoing
```

## Reducing Noise

**Individual user level:**
1. Disable Autowatch: User Profile > Preferences > Autowatch > Disable
2. Configure email preferences: Set batching frequency
3. Unwatch old issues: Remove from issues updated > 90 days ago

**Team/project level:**
1. Review notification scheme: Remove "All users" from events
2. Keep only: Assignee, Reporter, Watchers, @mentioned
3. Create role-specific schemes for different urgency levels

## Best Practices Summary

| Do | Do Not |
|----|--------|
| Use targeted notifications (watchers, assignee) | Notify all project members |
| Enable batching for routine updates | Send individual email for every change |
| Disable Autowatch globally | Auto-subscribe everyone who comments |
| Use @mentions for immediate attention | Overuse @mentions for FYI |
| Test with --dry-run before mass notifications | Spam entire team without preview |
| Review and clean up watchers periodically | Let watcher lists grow indefinitely |

---

[Back to Index](../INDEX.md) | [Back to Quick Reference](../QUICK_REFERENCE.md)
