# Commit Message Formats

**Read time:** 3 minutes

## Basic Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

## Always Include JIRA Issue Keys

**Formats that JIRA recognizes:**

```bash
# Direct reference
PROJ-123 Fix authentication bug

# Conventional Commits style
feat(auth): PROJ-123 add OAuth support

# Action prefix
Fixes PROJ-123: Null pointer in login
Closes PROJ-456: Memory leak in cache
Resolves PROJ-789: API timeout

# Brackets
[PROJ-123] Fix login button styling

# Multiple issues
PROJ-123 PROJ-456 Update shared dependencies
```

## Commit Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(auth): PROJ-123 add two-factor auth` |
| `fix` | Bug fix | `fix(api): PROJ-456 handle null response` |
| `docs` | Documentation | `docs: PROJ-789 update API guide` |
| `style` | Code style | `style: PROJ-101 format with prettier` |
| `refactor` | Code refactoring | `refactor(db): PROJ-202 optimize query` |
| `perf` | Performance | `perf(cache): PROJ-303 reduce memory` |
| `test` | Add/update tests | `test(auth): PROJ-404 add OAuth tests` |
| `build` | Build system | `build: PROJ-505 update webpack` |
| `ci` | CI/CD changes | `ci: PROJ-606 add GitHub Actions` |
| `chore` | Maintenance | `chore: PROJ-707 update dependencies` |

## Good Examples

```bash
# Feature with context
feat(payments): PROJ-123 add Stripe integration

Implements Stripe payment processing with webhook support.
Includes error handling and retry logic.

Refs: PROJ-123

# Bug fix with details
fix(login): PROJ-456 prevent session timeout on mobile

Users were getting logged out after 5 minutes on mobile Safari.
Fixed by updating session cookie settings.

Fixes: PROJ-456
```

## Bad Examples

| Bad | Problem | Good |
|-----|---------|------|
| `fixed stuff` | No issue key, vague | `fix(auth): PROJ-123 resolve token expiration` |
| `WIP` | No context | `feat(api): PROJ-456 add user endpoint (WIP)` |
| `Updated files` | No detail | `docs: PROJ-789 update installation guide` |

## Parsing Issue Keys

```bash
# Extract keys from commit message
python parse_commit_issues.py "PROJ-123: Fix login bug"

# Extract from git log
git log --oneline -10 | python parse_commit_issues.py --from-stdin

# Filter by project
python parse_commit_issues.py "PROJ-123 OTHER-456" --project PROJ
```

## Next Steps

- [Smart Commits](smart-commits.md) - Log time, transition issues from commits
- [PR Best Practices](pr-workflows.md) - Pull request patterns
