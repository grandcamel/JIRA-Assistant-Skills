# Team Communication Deep Dive

[Back to Index](../INDEX.md) | [Back to Quick Reference](../QUICK_REFERENCE.md)

---

Advanced guidance on choosing communication channels and protocols.

## Choosing the Right Channel

| Communication Need | Use | Do Not Use |
|--------------------|-----|------------|
| Issue-specific discussion | JIRA comment | Email, Slack |
| Quick question about issue | @mention in JIRA | Separate email |
| Real-time discussion | Slack/Teams, then summarize in JIRA | Long JIRA comment chains |
| Document collaboration | Confluence, link from JIRA | Multiple JIRA attachments |
| Status update on specific issue | JIRA comment | Email to team |
| Team-wide announcement | Slack/Email, reference JIRA issue | JIRA comment |
| Code review | GitHub/Bitbucket PR, link in JIRA | JIRA comments |

**Golden rule:** JIRA is the source of truth for issue status and decisions. Summarize external discussions in JIRA comments.

## Synchronous vs Asynchronous

**Asynchronous (JIRA comments):**
- Creates permanent record
- Allows thoughtful responses
- Accessible to future team members
- Searchable and linkable
- Slower for urgent items

**Synchronous (Slack/Zoom):**
- Fast resolution
- Real-time clarification
- Good for complex discussions
- No permanent record
- Excludes offline team members

**Best practice pattern:**
1. Have synchronous discussion (Slack, Zoom)
2. Summarize in JIRA comment
3. Tag participants for confirmation

**Example:**

```markdown
## Decision: Use PostgreSQL instead of MySQL

**Participants:** @alice, @bob, @charlie (Zoom call 2025-12-26)

**Rationale:**
- Better JSON support for our document storage needs
- Team has more PostgreSQL experience
- Existing infrastructure already on PostgreSQL

**Action items:**
- @alice: Update architecture diagram
- @bob: Revise database schema
- @charlie: Update deployment scripts

**Reference:** Meeting notes: [Confluence link]
```

## Handoff Communication

**Template for transferring ownership:**

```markdown
@new-assignee Taking over from @previous-assignee

**Current status:** [Brief summary]
**Completed:** [What is done]
**Remaining:** [What is left]
**Blockers:** [Any issues]
**Context:** [Key comments/decisions to review]

@previous-assignee Please confirm handoff is complete.
```

## Escalation Communication

**Template for blockers:**

```markdown
[ESCALATION] [Brief blocker description]

**Blocked on:** [Specific dependency]
**Impact:** [What cannot proceed]
**Duration:** [How long blocked]
**Attempted:** [Solutions tried]
**Need:** [Specific help required]

@escalation-person Please advise on path forward.
```

## Remote Team Considerations

**Time zones:**
- Note your timezone: "Submitting this EOD PST"
- Set expectations: "Will review tomorrow morning EST"
- Use absolute times: "By 2025-12-26 15:00 UTC" not "this afternoon"

**Asynchronous default:**
- Do not expect immediate responses
- Provide complete context in comments
- Use @mentions sparingly for urgent items only
- Update issues at end of your work day

**Example remote-friendly comment:**

```markdown
## Update: Authentication module complete (2025-12-26 18:00 PST)

**Status:** Ready for review
**Progress:** All unit tests passing, integration tests written
**Next steps:** Code review needed before tomorrow standup
**Blockers:** None

@reviewer Please review PR #234 when online tomorrow.

I will be offline until tomorrow 9 AM PST.
```

## Linking External Resources

**When to link:**

| Tool | What to Link | Format |
|------|--------------|--------|
| Confluence | Design docs, meeting notes | `Design: [Link]` |
| GitHub | PRs, commits | `PR: [Link]` |
| Figma | Design mockups | `Mockup: [Link]` |
| Splunk/Datadog | Logs, monitoring | `Logs: [Link to query]` |
| Loom | Video walkthroughs | `Video: [Link]` |

**Best practices:**
- Use descriptive link text (not "click here")
- Keep links up to date
- Use permanent links (not temporary share links)
- Link both ways for traceability

---

[Back to Index](../INDEX.md) | [Back to Quick Reference](../QUICK_REFERENCE.md)
