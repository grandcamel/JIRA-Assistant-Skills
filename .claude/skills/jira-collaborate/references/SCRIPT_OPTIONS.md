# Script Options Reference

Detailed options for all jira-collaborate scripts.

---

## Universal Options

All scripts support these options:

| Option | Description |
|--------|-------------|
| `--profile <name>` | JIRA profile to use (default: from config) |
| `--help`, `-h` | Show help message and exit |

---

## Comment Scripts

### add_comment.py

| Option | Description |
|--------|-------------|
| `ISSUE_KEY` | Issue to add comment to (required) |
| `--body <text>` | Comment body text (required) |
| `--format text\|markdown\|adf` | Input format (default: text) |
| `--visibility-role <role>` | Restrict to role (e.g., Administrators) |
| `--visibility-group <group>` | Restrict to group |

### update_comment.py

| Option | Description |
|--------|-------------|
| `ISSUE_KEY` | Issue containing the comment (required) |
| `--comment-id <id>` | Comment ID to update (required) |
| `--body <text>` | New comment body (required) |
| `--format text\|markdown\|adf` | Input format (default: text) |

### delete_comment.py

| Option | Description |
|--------|-------------|
| `ISSUE_KEY` | Issue containing the comment (required) |
| `--comment-id <id>` | Comment ID to delete (required) |
| `--dry-run` | Preview without deleting |
| `--force` | Skip confirmation prompt |

### get_comments.py

| Option | Description |
|--------|-------------|
| `ISSUE_KEY` | Issue to get comments from (required) |
| `--format text\|table\|json` | Output format (default: text) |
| `--limit <n>` | Maximum comments to return |

---

## Attachment Scripts

### upload_attachment.py

| Option | Description |
|--------|-------------|
| `ISSUE_KEY` | Issue to attach file to (required) |
| `--file <path>` | File path to upload (required) |

### download_attachment.py

| Option | Description |
|--------|-------------|
| `ISSUE_KEY` | Issue to download from (required) |
| `--list` | List all attachments |
| `--id <id>` | Download specific attachment by ID |
| `--name <filename>` | Download specific attachment by name |
| `--all` | Download all attachments |
| `--output-dir <path>` | Directory to save files |
| `--output text\|json` | Output format for --list |

---

## Notification Scripts

### send_notification.py

| Option | Description |
|--------|-------------|
| `ISSUE_KEY` | Issue to notify about (required) |
| `--subject <text>` | Notification subject |
| `--body <text>` | Notification body |
| `--dry-run` | Preview recipients without sending |
| `--watchers` | Notify all watchers |
| `--assignee` | Notify assignee |
| `--reporter` | Notify reporter |
| `--users <ids>` | Notify specific users (account IDs) |
| `--groups <names>` | Notify specific groups |

---

## Activity Scripts

### get_activity.py

| Option | Description |
|--------|-------------|
| `ISSUE_KEY` | Issue to get activity for (required) |
| `--format text\|table\|json\|csv` | Output format (default: text) |
| `--filter <type>` | Filter by change type (status, assignee, priority) |

---

## Watcher Scripts

### manage_watchers.py

| Option | Description |
|--------|-------------|
| `ISSUE_KEY` | Issue to manage watchers for (required) |
| `--add <email>` | Add user as watcher |
| `--remove <email>` | Remove user as watcher |
| `--list` | List current watchers |

---

## Custom Field Scripts

### update_custom_fields.py

| Option | Description |
|--------|-------------|
| `ISSUE_KEY` | Issue to update (required) |
| `--field <id>` | Custom field ID (required) |
| `--value <value>` | Value to set (required) |

---

## Option Matrix

| Script | --format | --dry-run | --visibility | --filter |
|--------|----------|-----------|--------------|----------|
| add_comment.py | input | - | role/group | - |
| update_comment.py | input | - | - | - |
| delete_comment.py | - | yes | - | - |
| get_comments.py | output | - | - | - |
| send_notification.py | - | yes | - | - |
| get_activity.py | output | - | - | yes |
| download_attachment.py | output | - | - | - |

---

For detailed help on any script: `python <script>.py --help`
