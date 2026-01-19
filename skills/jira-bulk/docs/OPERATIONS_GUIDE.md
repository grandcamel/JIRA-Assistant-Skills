# Which Bulk Operation Should I Use?

Quick guide to choosing the right script for your task.

---

## Operation Selection

### I need to move issues to a new status

**Use:** `bulk_transition.py`

```bash
python bulk_transition.py --jql "project=PROJ AND status='In Progress'" --to "Done"
```

**Best for:**
- Sprint cleanup (moving done items to "Done")
- Release management (transitioning to "Released")
- Mass status updates after verification

**Key features:**
- Handles workflow constraints automatically
- Sets resolution when transitioning to resolved states
- Adds optional comments during transition

---

### I need to reassign work to a team member

**Use:** `bulk_assign.py`

```bash
python bulk_assign.py --jql "assignee=john.doe" --assignee jane.doe
```

**Best for:**
- Team member transitions (leaving/joining)
- Load balancing work distribution
- Reassigning after team reorganization

**Key features:**
- Accepts email, account ID, or 'self' keyword
- Supports unassign with `--unassign` flag
- Fast execution for assignment updates

---

### I need to set priority on multiple issues

**Use:** `bulk_set_priority.py`

```bash
python bulk_set_priority.py --jql "type=Bug AND labels=urgent" --priority Highest
```

**Best for:**
- Priority escalation (marking critical bugs)
- Priority standardization across projects
- Triage batch updates

**Key features:**
- Standard priority levels (Highest, High, Medium, Low, Lowest)
- Custom priority names supported
- Simple, fast execution

---

### I need to duplicate issues for another team

**Use:** `bulk_clone.py`

```bash
python bulk_clone.py --jql "sprint='Sprint 42'" --target-project NEWPROJ --include-subtasks
```

**Best for:**
- Sprint template cloning
- Project migration
- Creating parallel work items for multiple teams

**Key features:**
- Include subtasks with `--include-subtasks`
- Include issue links with `--include-links`
- Clone to different project with `--target-project`
- Add prefix to summaries with `--prefix`

---

## Decision Matrix

| I need to... | Script | Risk Level | Reversible? |
|--------------|--------|------------|-------------|
| Change status | `bulk_transition.py` | Low-Medium | Yes (reverse transition) |
| Reassign issues | `bulk_assign.py` | Low | Yes (reassign back) |
| Change priority | `bulk_set_priority.py` | Low | Yes (set original priority) |
| Clone issues | `bulk_clone.py` | Medium | Partial (delete clones) |

---

## I need something else

**Combining operations:**

Run scripts sequentially for complex workflows:

```bash
# First transition, then reassign
python bulk_transition.py --jql "project=PROJ" --to "In Review" && \
python bulk_assign.py --jql "project=PROJ AND status='In Review'" --assignee reviewer
```

**Custom bulk operations:**

For unsupported operations, use the `jira-search` skill to find issues, then process individually or request an enhancement.

---

## Related Documentation

- [Quick Start](QUICK_START.md) - Get started in 5 minutes
- [Best Practices](BEST_PRACTICES.md) - Full guidance for complex operations
