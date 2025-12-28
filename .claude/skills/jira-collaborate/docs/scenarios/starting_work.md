# Scenario: Starting Work on an Issue

**Use this guide when:** You are picking up an issue and want to signal to the team that work has begun.

## The Situation

You have been assigned an issue or are claiming one from the backlog. You want to let the team know you are starting, set expectations, and prevent duplicate work.

## Quick Template

```bash
python add_comment.py PROJ-123 --format markdown --body "## Starting Work

**Focus:** [specific aspect you will tackle first]
**ETA:** [expected completion timeframe]
**Dependencies:** [any blockers or prerequisites]"
```

## Example

```bash
python add_comment.py PROJ-123 --format markdown --body "## Starting Work

**Focus:** Implementing the authentication flow first
**ETA:** 2 days for initial implementation
**Dependencies:** Waiting on API keys from vendor (expected today)"
```

**Output in JIRA:**

> ## Starting Work
>
> **Focus:** Implementing the authentication flow first
> **ETA:** 2 days for initial implementation
> **Dependencies:** Waiting on API keys from vendor (expected today)

## Related Scripts

- `add_comment.py` - Post your start notification
- `manage_watchers.py` - Add stakeholders who should track progress

## Pro Tips

- Include ETA to set expectations
- Mention any known dependencies upfront
- Keep the comment brief but informative

---

[Back to GETTING_STARTED.md](../GETTING_STARTED.md)
