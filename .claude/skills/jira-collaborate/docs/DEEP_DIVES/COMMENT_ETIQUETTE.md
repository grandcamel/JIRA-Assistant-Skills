# Comment Etiquette Deep Dive

[Back to Index](../INDEX.md) | [Back to Quick Reference](../QUICK_REFERENCE.md)

---

Advanced guidance on writing effective, professional comments in JIRA.

## Comment Structure for Progress Updates

Use this template for status updates:

```markdown
## Update: [Brief title]

**Status:** On track / Blocked / At risk
**Progress:** Completed X, working on Y
**Next steps:** Will do Z
**Blockers:** [if any]
```

## When to Comment

| Situation | Comment? | Reason |
|-----------|----------|--------|
| Starting work | Yes | Prevents duplicate work, sets expectations |
| Progress milestone | Yes | Keeps stakeholders informed |
| Blocked/waiting | Yes | Signals need for help |
| Solution found | Yes | Documents resolution |
| Before closing | Yes | Confirms completion criteria |
| Routine updates | No | Creates noise |
| Trivial edits | No | Visible in activity history |

## Comment Length Guidelines

**Do:**
- Keep comments concise (2-5 sentences ideal)
- Use bullet points for multiple items
- Break long updates into sections with headings
- Front-load the most important information

**Do Not:**
- Write essay-length comments (use Confluence and link)
- Include full error logs (attach as file instead)
- Paste entire code blocks (link to PR/commit)
- Repeat information already in description

## Professional Tone

**Do:**
- Be constructive: "Consider using X instead of Y because..."
- Be specific: "The login timeout occurs when session exceeds 30 minutes"
- Be respectful: "Thanks for the review! I will update the error handling"
- Be collaborative: "Would love input from @jane on the database schema"

**Do Not:**
- Be vague: "This does not work"
- Be demanding: "Fix this now!"
- Be dismissive: "That is a terrible approach"
- Be passive-aggressive: "Well, if you had read my comment..."

## Team Conventions

Establish team agreements for consistency:

| Convention | Purpose | Example |
|------------|---------|---------|
| Comment labels | Categorize type | "QUESTION:", "BLOCKER:", "FYI:" |
| Prefix tags | Signal urgency | "[URGENT]", "[NEEDS REVIEW]" |
| Status markers | Quick scanning | "DONE", "BLOCKED", "IN PROGRESS" |
| Ownership markers | Assign action | "ACTION @username:", "DECISION NEEDED:" |

## Question and Answer Protocol

**Asking good questions:**

```markdown
QUESTION: [Clear, specific question]

**Context:** [Why you are asking]
**Tried already:** [What you have attempted]
**Impact:** [Why it matters]
```

**Answering questions:**
- Answer directly at the top
- Provide reasoning below
- Include references or links
- Suggest alternatives if applicable

## Internal vs Public Comments

**Use internal comments for:**
- Sensitive information (customer details, pricing)
- Team-only discussions (architectural decisions)
- Administrative notes (billing, contracts)
- Debugging details with security implications

```bash
# Public comment
python add_comment.py PROJ-123 --body "Fix deployed to production"

# Internal comment (Administrators only)
python add_comment.py PROJ-123 --body "Customer credentials reset" --visibility-role Administrators

# Group-restricted comment
python add_comment.py PROJ-123 --body "Pricing approved: $15k" --visibility-group finance-team
```

## Editing Comments

**When to edit:**
- Fixing typos or formatting
- Adding clarifying information
- Updating status within same day

**When to add new comment instead:**
- Significant new information
- Changed circumstances
- Response to questions
- After 24 hours have passed

**Best practice:** If editing changes meaning, add note:

```markdown
[EDITED: 2025-12-26] Added error details below

[Original comment text]

**Update:** Error is actually caused by timeout, not permissions.
```

---

[Back to Index](../INDEX.md) | [Back to Quick Reference](../QUICK_REFERENCE.md)
