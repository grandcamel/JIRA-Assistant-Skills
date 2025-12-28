# Scenario: Sharing Test Evidence

**Use this guide when:** You need to share screenshots, logs, or test results with the team.

## The Situation

You have evidence to share: a bug screenshot, error logs, test results, or other artifacts. You want to attach them in a way that is organized and useful.

## Quick Template

```bash
# Upload the file
python upload_attachment.py PROJ-123 --file PROJ-123_Screenshot_ErrorState_2025-12-28.png

# Add explanatory comment
python add_comment.py PROJ-123 --format markdown --body "## Test Evidence

**Attached:** PROJ-123_Screenshot_ErrorState_2025-12-28.png

**Description:** [What the attachment shows]
**Steps to reproduce:** [If applicable]
**Expected vs Actual:** [If bug evidence]"
```

## Example

```bash
# Upload screenshot
python upload_attachment.py PROJ-123 --file PROJ-123_Screenshot_LoginError_2025-12-28.png

# Add context
python add_comment.py PROJ-123 --format markdown --body "## Bug Evidence

**Attached:** PROJ-123_Screenshot_LoginError_2025-12-28.png

**Description:** Login timeout error after 30 seconds of inactivity

**Steps to reproduce:**
1. Navigate to /login
2. Enter valid credentials
3. Wait 30+ seconds before clicking Submit
4. Error appears (highlighted in screenshot)

**Expected:** Session should persist for at least 2 hours
**Actual:** Session expires after 30 seconds of idle time"
```

## File Naming Convention

Use descriptive names: `[ProjectKey]_[Type]_[Description]_[Date].ext`

- `PROJ-123_Screenshot_ErrorState_2025-12-28.png`
- `PROJ-123_Logs_ProductionError_2025-12-28.txt`
- `PROJ-123_TestResults_UserFlow_2025-12-28.pdf`

## Related Scripts

- `upload_attachment.py` - Upload files to the issue
- `download_attachment.py --list` - List existing attachments
- `add_comment.py` - Add explanatory comment with context

## Pro Tips

- Always explain what the attachment shows
- Use descriptive filenames (not screenshot.png)
- Crop screenshots to relevant area
- Redact sensitive data from logs
- Keep files under 5MB (compress if needed)

---

[Back to GETTING_STARTED.md](../GETTING_STARTED.md)
