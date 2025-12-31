# Live Integration Tests

End-to-end integration tests that run against a real JIRA Cloud instance.

## Overview

These tests create a temporary project, run the full test suite, and clean up all resources including the project itself.

## Prerequisites

1. **JIRA Cloud Instance**: A JIRA Cloud instance with admin access
2. **API Token**: Valid API token with admin permissions
3. **Profile Configuration**: JIRA profile configured in settings

### Required Permissions

The API user needs:
- **JIRA Administrator** - Create/delete projects
- **Browse Projects** - View project data
- **Create Issues** - Issue creation
- **Edit Issues** - Issue updates
- **Delete Issues** - Issue cleanup
- **Manage Sprints** - Sprint lifecycle
- **Schedule Issues** - Sprint assignment

## Usage

### Run All Tests

```bash
# Using development profile
pytest plugins/jira-assistant-skills/skills/shared/tests/live_integration/ --profile development -v

# Using specific profile
pytest plugins/jira-assistant-skills/skills/shared/tests/live_integration/ --profile staging -v

# Keep project after tests (for debugging)
pytest plugins/jira-assistant-skills/skills/shared/tests/live_integration/ --profile development --keep-project -v

# Use existing project (no cleanup)
pytest plugins/jira-assistant-skills/skills/shared/tests/live_integration/ --profile development --project-key EXISTING -v
```

### Run Specific Test Modules

```bash
# Issue lifecycle tests only
pytest plugins/jira-assistant-skills/skills/shared/tests/live_integration/test_issue_lifecycle.py --profile development -v

# Agile workflow tests only
pytest plugins/jira-assistant-skills/skills/shared/tests/live_integration/test_agile_workflow.py --profile development -v

# Relationship tests only
pytest plugins/jira-assistant-skills/skills/shared/tests/live_integration/test_relationships.py --profile development -v

# Collaboration tests only
pytest plugins/jira-assistant-skills/skills/shared/tests/live_integration/test_collaboration.py --profile development -v

# Project lifecycle tests only
pytest plugins/jira-assistant-skills/skills/shared/tests/live_integration/test_project_lifecycle.py --profile development -v

# Time tracking tests only
pytest plugins/jira-assistant-skills/skills/shared/tests/live_integration/test_time_tracking.py --profile development -v
```

### Cleanup Utility

For cleaning up orphaned test projects:

```bash
# List all test projects (INT prefix)
python plugins/jira-assistant-skills/skills/shared/tests/live_integration/cleanup.py --list --profile development

# Delete specific project
python plugins/jira-assistant-skills/skills/shared/tests/live_integration/cleanup.py INT123ABC --profile development

# Delete all projects with prefix (with confirmation)
python plugins/jira-assistant-skills/skills/shared/tests/live_integration/cleanup.py --prefix INT --profile development

# Dry run (show what would be deleted)
python plugins/jira-assistant-skills/skills/shared/tests/live_integration/cleanup.py --prefix INT --dry-run --profile development
```

## Test Structure

```
live_integration/
├── conftest.py                 # Fixtures for project setup/teardown
├── test_issue_lifecycle.py     # Issue CRUD tests
├── test_agile_workflow.py      # Sprint/board/epic tests
├── test_relationships.py       # Issue link tests
├── test_collaboration.py       # Comments, attachments, watchers
├── test_project_lifecycle.py   # Project creation/deletion tests
├── test_time_tracking.py       # Worklogs, estimates, time tracking
├── cleanup.py                  # Standalone cleanup utility
└── README.md                   # This file
```

## Fixtures

### Session-Scoped

- `jira_client` - JIRA client instance
- `test_project` - Temporary project (auto-created, auto-cleaned)

### Function-Scoped

- `test_issue` - Temporary test issue
- `test_epic` - Temporary test epic
- `test_sprint` - Temporary test sprint

## Test Project Naming

Test projects are created with keys like `INTA1B2C3`:
- `INT` prefix (Integration Test)
- 6 random hex characters

This allows easy identification and cleanup of orphaned projects.

## Cleanup Behavior

1. **Normal completion**: Project and all resources are deleted
2. **Test failure**: Cleanup still runs (via fixture teardown)
3. **Interrupted**: Use cleanup.py to remove orphaned projects
4. **--keep-project**: Skips cleanup for debugging

## Environment Variables

| Variable | Description |
|----------|-------------|
| `JIRA_PROFILE` | Default profile (fallback for --profile) |
| `JIRA_API_TOKEN` | API token (if not in config) |
| `JIRA_EMAIL` | User email (if not in config) |
| `JIRA_SITE_URL` | JIRA URL (if not in config) |

## Notes

- Tests may take several minutes due to API rate limits
- Project deletion goes to trash (60-day retention)
- Some tests require specific issue types (Epic, Story, Bug, Task, Subtask)
- Sprint deletion only works for "future" state sprints
