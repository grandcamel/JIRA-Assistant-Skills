# Checkpoint and Resume Guide

How to use checkpoints for reliable large-scale operations.

---

## When to Enable Checkpoints

Enable checkpoints when:
- Processing **500+ issues**
- On an **unreliable network** connection
- Running **critical operations** that must complete
- Operation will take **>5 minutes**

---

## How Checkpoints Work

1. **Enable:** Add `--enable-checkpoint` to your command
2. **Execute:** Progress is saved automatically after each batch
3. **Interrupt:** Safe to stop with Ctrl+C at any time
4. **Resume:** Continue from where you left off

```
Operation Start
    |
    v
[Batch 1: 100 issues] --> Save checkpoint (100/500)
    |
    v
[Batch 2: 100 issues] --> Save checkpoint (200/500)
    |
    v
[Batch 3: 100 issues] --> Save checkpoint (300/500)
    |
    v  <-- Network failure or Ctrl+C
[Interrupted at 300/500]
    |
    v
[Resume] --> Load checkpoint, continue from issue 301
```

---

## Usage

### Enable Checkpointing

```bash
python bulk_transition.py \
  --jql "project=PROJ" \
  --to "Done" \
  --enable-checkpoint
```

### List Pending Checkpoints

```bash
python bulk_transition.py --list-checkpoints
```

Output:
```
Pending checkpoints:
  transition-20251226-143022 (Progress: 300/500 issues, 60% complete)
  transition-20251225-091500 (Progress: 150/1000 issues, 15% complete)
```

### Resume an Interrupted Operation

```bash
python bulk_transition.py --resume transition-20251226-143022 --to "Done"
```

---

## Storage Details

**Location:** `~/.jira-skills/checkpoints/`

**File format:** JSON with:
- Operation ID (timestamp-based identifier)
- Target status/assignee/priority
- Progress percentage and counts
- List of processed issue keys
- Start and last update timestamps

**Size:** Approximately 50KB per operation (varies with issue count)

---

## Cleanup

Checkpoints are automatically cleaned up after successful completion.

To manually clean up old checkpoints:

```bash
# View checkpoint files
ls ~/.jira-skills/checkpoints/

# Remove specific checkpoint
rm ~/.jira-skills/checkpoints/transition-20251225-091500.json

# Remove all checkpoints (caution!)
rm ~/.jira-skills/checkpoints/*.json
```

---

## Combining with Batch Size

For optimal reliability on very large operations:

```bash
python bulk_transition.py \
  --jql "project=PROJ" \
  --to "Done" \
  --batch-size 200 \
  --enable-checkpoint \
  --delay-between-ops 0.3
```

| Total Issues | Recommended Setup |
|--------------|-------------------|
| 500-1,000 | `--batch-size 200 --enable-checkpoint` |
| 1,000-5,000 | `--batch-size 200 --enable-checkpoint --delay-between-ops 0.3` |
| 5,000+ | `--batch-size 500 --enable-checkpoint --delay-between-ops 0.5` |

---

## Troubleshooting

**"Checkpoint not found"**
- Check the operation ID spelling
- Run `--list-checkpoints` to see available checkpoints

**"Cannot resume - operation completed"**
- The checkpoint was auto-cleaned after success
- No action needed

**"Checkpoint file corrupted"**
- Delete the checkpoint file manually
- Re-run the full operation

---

## Related Documentation

- [Quick Start](QUICK_START.md) - Get started in 5 minutes
- [Error Recovery](ERROR_RECOVERY.md) - Handle failures
- [Best Practices](BEST_PRACTICES.md) - Full guidance
