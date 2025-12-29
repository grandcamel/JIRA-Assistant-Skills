# Quick Start: 5-Minute Patterns

Get up and running with bulk operations in under 5 minutes.

---

## Choose Your Path

### I have 5-10 issues to update

Just run it directly - no special options needed:

```bash
# Transition issues
python bulk_transition.py --issues PROJ-1,PROJ-2,PROJ-3 --to "Done"

# Assign issues
python bulk_assign.py --issues PROJ-1,PROJ-2 --assignee "john.doe"

# Set priority
python bulk_set_priority.py --issues PROJ-1,PROJ-2 --priority High

# Clone issues
python bulk_clone.py --issues PROJ-1,PROJ-2 --include-subtasks
```

---

### I have 50-100 issues to update

Use dry-run first to preview changes:

```bash
# Step 1: Preview what will happen
python bulk_transition.py --jql "project=PROJ AND status='In Progress'" --to "Done" --dry-run

# Step 2: Review output - verify count and sample issues

# Step 3: Execute
python bulk_transition.py --jql "project=PROJ AND status='In Progress'" --to "Done"
```

**Tip:** Operations over 50 issues will prompt for confirmation. Use `--yes` to skip (with caution).

---

### I have 500+ issues to update

Use batching and checkpoints for reliability:

```bash
# Step 1: Preview
python bulk_transition.py --jql "project=PROJ" --to "Done" --dry-run

# Step 2: Execute with safety features
python bulk_transition.py \
  --jql "project=PROJ" \
  --to "Done" \
  --batch-size 200 \
  --enable-checkpoint

# If interrupted, resume:
python bulk_transition.py --list-checkpoints
python bulk_transition.py --resume transition-20251226-143022 --to "Done"
```

---

## Essential Options

| Option | When to Use | Example |
|--------|-------------|---------|
| `--dry-run` | Preview changes (>10 issues) | `--dry-run` |
| `--batch-size N` | Rate limit issues (500+ issues) | `--batch-size 200` |
| `--enable-checkpoint` | Allow resume after interruption | `--enable-checkpoint` |
| `--delay-between-ops N` | Reduce rate limit errors | `--delay-between-ops 0.5` |
| `--max-issues N` | Limit scope for testing | `--max-issues 100` |

---

## Common Scenarios

### Sprint Cleanup

```bash
# Close all done items from current sprint
python bulk_transition.py \
  --jql "sprint in openSprints() AND status='Verified'" \
  --to "Done" \
  --resolution "Done"
```

### Team Member Reassignment

```bash
# Reassign open work from leaving team member
python bulk_assign.py \
  --jql "assignee=john.leaving AND status NOT IN (Done, Closed)" \
  --assignee jane.replacing
```

### Priority Escalation

```bash
# Bump all critical bugs to Highest priority
python bulk_set_priority.py \
  --jql "type=Bug AND labels=critical AND priority != Highest" \
  --priority Highest
```

### Sprint Cloning

```bash
# Clone entire sprint to new project
python bulk_clone.py \
  --jql "sprint='Sprint 42'" \
  --target-project NEWPROJ \
  --include-subtasks \
  --include-links \
  --prefix "[Clone]"
```

---

## Next Steps

- **Which script should I use?** See [Operations Guide](OPERATIONS_GUIDE.md)
- **How do checkpoints work?** See [Checkpoint Guide](CHECKPOINT_GUIDE.md)
- **Something went wrong?** See [Error Recovery](ERROR_RECOVERY.md)
- **Planning a big operation?** See [Best Practices](BEST_PRACTICES.md)
