# Attachment Strategy Deep Dive

[Back to Index](../INDEX.md) | [Back to Quick Reference](../QUICK_REFERENCE.md)

---

Advanced guidance on managing attachments effectively in JIRA.

## When to Attach vs Link

| Scenario | Action | Reasoning |
|----------|--------|-----------|
| Screenshots/error logs | Attach | Specific to this issue |
| Design documents | Link to Confluence | Needs versioning |
| Large log files (>2MB) | Link to file storage | Size limits |
| Code snippets | Paste in comment | Small, contextual |
| PR/commits | Link to Git | Native integration |
| Architecture diagrams | Link to Confluence | Shared across issues |
| Test evidence | Attach | Proof of completion |
| Temporary debug info | Attach | Will not be revised |

**Best practice:** Link instead of upload when possible. JIRA should be the source of truth for work items, not a file storage system.

## File Naming Conventions

**Format:** `[ProjectKey]_[Type]_[Description]_[Version]_[Date]`

Examples:
- `PROJ-123_Screenshot_LoginError_v1_2025-12-26.png`
- `PROJ-456_Logs_ProductionError_2025-12-26.txt`
- `PROJ-789_Diagram_Architecture_v2.0_2025-12.pdf`

**Naming principles:**
- **Descriptive:** Immediately clear what file contains
- **Unique:** Will not conflict with other attachments
- **Versioned:** Include version if multiple iterations expected
- **Dated:** Use YYYY-MM-DD format for chronological sorting
- **No spaces:** Use underscores or hyphens

## Size Guidelines

| File Type | Size Limit | Best Practice |
|-----------|------------|---------------|
| Screenshots | < 1MB | Compress or crop to relevant area |
| Documents | < 2MB | Link to Confluence/Google Docs |
| Logs | < 5MB | Upload only relevant excerpts |
| Videos | < 10MB | Use Loom/YouTube and link |
| Archives | Avoid | Extract and attach only needed files |

**JIRA Cloud default:** 10MB per attachment

## Organizing Multiple Attachments

When issue has many attachments:

1. **Use clear naming:**
   ```
   01_Original_Bug_Report.pdf
   02_Screenshot_Error_State.png
   03_Screenshot_Expected_State.png
   04_Logs_Before_Fix.txt
   05_Logs_After_Fix.txt
   ```

2. **Add comment index:**
   ```markdown
   ## Attachment Index

   **Bug Evidence:**
   - 01_Original_Bug_Report.pdf - Initial customer report
   - 02_Screenshot_Error_State.png - Error as seen by user

   **Solution Verification:**
   - 05_Logs_After_Fix.txt - Logs confirming fix
   ```

3. **Delete obsolete attachments** after finalized versions exist.

## Screenshot Best Practices

**Effective screenshots:**
- Crop to relevant area only
- Highlight/annotate important parts
- Include timestamp if showing transient issue
- Show enough context (browser address bar, app state)

**In comment, explain what screenshot shows:**

```markdown
See attached screenshot showing the login timeout error.

**Steps to reproduce:**
1. Navigate to /login
2. Enter valid credentials
3. Wait 30+ seconds
4. Error appears (highlighted in screenshot)

Attachment: PROJ-123_Screenshot_LoginError_2025-12-26.png
```

## Log File Best Practices

Before attaching full logs:
1. Identify relevant time window
2. Extract only pertinent entries
3. Redact sensitive data (tokens, passwords, PII)
4. Add context comment

**Log excerpt template:**

```markdown
## Error Log Excerpt

**Timestamp:** 2025-12-26 14:23:15 UTC
**Component:** Authentication Service
**Severity:** ERROR

See attached log file (lines 1523-1687 covering the error window).

Key error: `NullPointerException in SessionManager.validateToken()`
```

## Attachment Security

**Never attach:**
- API keys or tokens
- Passwords or credentials
- Customer PII (unless required and encrypted)
- Proprietary source code (link to Git instead)

**If sensitive data needed:**
- Use internal comments with visibility restrictions
- Encrypt files before attaching
- Use temporary secure sharing (expire after resolution)

```bash
# Upload with restricted visibility comment
python upload_attachment.py PROJ-123 --file secure_data.txt
python add_comment.py PROJ-123 --body "Secure data attached" --visibility-role Administrators
```

---

[Back to Index](../INDEX.md) | [Back to Quick Reference](../QUICK_REFERENCE.md)
