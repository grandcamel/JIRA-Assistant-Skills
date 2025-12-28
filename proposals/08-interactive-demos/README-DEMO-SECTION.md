# Demo Section for README.md

Add the following section to the main README.md file after the project description.

---

## Try It Now

<div align="center">

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/grandcamel/jira-assistant-skills)

</div>

Launch a fully-configured development environment in seconds. No local setup required.

### Quick Preview

<p align="center">
  <img src="assets/demo.gif" alt="JIRA Assistant Skills Demo" width="700">
</p>

### What You Can Do

| Skill | Example Command |
|-------|-----------------|
| **Create Issues** | `python .claude/skills/jira-issue/scripts/create_issue.py PROJ "Bug title" --type Bug` |
| **Search with JQL** | `python .claude/skills/jira-search/scripts/jql_search.py "assignee = currentUser()"` |
| **Transition Issues** | `python .claude/skills/jira-lifecycle/scripts/transition_issue.py PROJ-123 "Done"` |
| **Log Time** | `python .claude/skills/jira-time/scripts/log_time.py PROJ-123 2h --comment "Fix applied"` |
| **Manage Sprints** | `python .claude/skills/jira-agile/scripts/move_to_sprint.py PROJ-123 --sprint "Sprint 5"` |
| **Bulk Operations** | `python .claude/skills/jira-bulk/scripts/bulk_transition.py "query" "Done" --dry-run` |

### Setup in Codespaces

1. Click "Open in GitHub Codespaces" above
2. Wait for the environment to build (~2 minutes)
3. Configure your JIRA credentials as Codespaces secrets:

   | Secret | Value |
   |--------|-------|
   | `JIRA_SITE_URL` | `https://your-company.atlassian.net` |
   | `JIRA_EMAIL` | Your Atlassian account email |
   | `JIRA_API_TOKEN` | [Generate here](https://id.atlassian.com/manage-profile/security/api-tokens) |

4. Restart the Codespace to apply secrets
5. Start using the skills!

### Local Installation

```bash
# Clone the repository
git clone https://github.com/grandcamel/jira-assistant-skills.git
cd jira-assistant-skills

# Install dependencies
pip install -r .claude/skills/shared/scripts/lib/requirements.txt

# Configure credentials
export JIRA_SITE_URL="https://your-company.atlassian.net"
export JIRA_EMAIL="you@company.com"
export JIRA_API_TOKEN="your-api-token"

# Test connection
python .claude/skills/jira-issue/scripts/get_issue.py YOUR-KEY
```

---

## Integration Notes

### Badge Placement
The Codespaces badge should be prominently placed near the top of the README, ideally in a centered div after the project title/description.

### Demo GIF
1. Generate the GIF using VHS: `cd proposals/08-interactive-demos && vhs demo.tape`
2. Move to assets folder: `mv demo.gif ../../assets/`
3. The README references `assets/demo.gif`

### Alternative Badge Styles

```markdown
<!-- Minimal -->
[![Open in Codespaces](https://img.shields.io/badge/Open%20in-Codespaces-blue?logo=github)](https://codespaces.new/grandcamel/jira-assistant-skills)

<!-- With container info -->
[![Dev Container](https://img.shields.io/badge/Dev%20Container-Python%203.11-blue?logo=visualstudiocode)](https://codespaces.new/grandcamel/jira-assistant-skills)
```

### Required Secrets Documentation

Add to your repository's SECURITY.md or CONTRIBUTING.md:

```markdown
## Codespaces Secrets

To use JIRA Assistant Skills in Codespaces, configure these repository-scoped secrets:

1. Go to [GitHub Codespaces Settings](https://github.com/settings/codespaces)
2. Under "Codespaces secrets", click "New secret"
3. Add each secret below, scoped to `grandcamel/jira-assistant-skills`:

| Secret Name | Description | Where to Get |
|-------------|-------------|--------------|
| `JIRA_SITE_URL` | Your JIRA Cloud instance URL | Your JIRA URL (e.g., https://company.atlassian.net) |
| `JIRA_EMAIL` | Atlassian account email | The email you use to log into JIRA |
| `JIRA_API_TOKEN` | API authentication token | [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens) |
```
