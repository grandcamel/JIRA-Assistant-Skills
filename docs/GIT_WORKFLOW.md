# Git Workflow

## Branch Strategy

**CRITICAL: Never push directly to `origin/main`.** Local `main` is read-only.

| Branch | Purpose | Push to origin? |
|--------|---------|-----------------|
| `main` | Read-only mirror of GitHub | **NO** - only pull |
| `dev` | Default local development | Yes, for backup |
| `feature/*`, `fix/*`, `docs/*` | PR branches | Yes, for PRs |

## Default Development Flow

1. **Start work on a feature branch or `dev`:**
   ```bash
   git checkout dev
   # or
   git checkout -b feature/my-feature
   ```

2. **Make commits locally** - commit freely to your working branch

3. **When ready to merge to main, create a PR:**
   - Ask user for branch name
   - Create and push the PR branch
   - Create PR via `gh pr create`

## Creating Pull Requests

**Only create PRs when explicitly requested.** Do NOT proactively create PRs.

1. **Ask for branch name** if not specified
2. **Create PR branch:**
   ```bash
   git checkout -b <pr-branch-name>
   git add -A
   git commit -m "<conventional commit message>"
   ```
3. **Push and create PR:**
   ```bash
   git push -u origin <pr-branch-name>
   gh pr create --title "<title>" --body "<description>" --base main --head <pr-branch-name>
   ```

## Keeping Local Main Updated

```bash
# Update local main from GitHub
git checkout main
git pull --rebase origin main

# Rebase working branch
git checkout dev
git rebase main
```

## What NOT to Do

```bash
# NEVER do this
git checkout main && git commit -m "some change"
git push origin main
```

## Quick Reference

| Action | Command |
|--------|---------|
| Start new work | `git checkout dev` or `git checkout -b feature/name` |
| Update from GitHub | `git checkout main && git pull --rebase origin main` |
| Create PR branch | `git checkout -b <branch-name>` |
| Push PR branch | `git push -u origin <branch-name>` |
| After PR merged | `git checkout main && git pull --rebase origin main` |
| Clean up PR branch | `git branch -d <branch-name>` |

## Conventional Commits

Format: `<type>[optional scope]: <description>`

### Types

| Type | Purpose |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no logic change |
| `refactor` | Code change, not fix or feature |
| `perf` | Performance improvement |
| `test` | Adding/updating tests |
| `build` | Build system or dependencies |
| `ci` | CI configuration |
| `chore` | Other changes |

### Scopes

Skills: `jira-issue`, `jira-lifecycle`, `jira-search`, `jira-collaborate`, `jira-agile`, `jira-relationships`, `jira-time`, `jira-jsm`, `jira-bulk`, `jira-dev`, `jira-fields`, `jira-ops`, `jira-admin`, `jira-assistant`

Other: `shared`, `config`, `docs`

### Examples

```bash
feat(jira-issue): add support for creating subtasks
fix(shared): correct retry backoff calculation
docs: add troubleshooting guide

# Breaking change
feat(config)!: migrate to YAML configuration format

BREAKING CHANGE: settings.json is now settings.yaml
```

### Guidelines

- Body explains what and why, not how
- Reference JIRA tickets in footers: `Refs: PROJ-123`
- Wrap body at 72 characters
- Multiple scopes: `feat(jira-issue,shared): add retry logic`
