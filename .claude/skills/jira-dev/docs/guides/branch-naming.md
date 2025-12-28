# Branch Naming Conventions

**Read time:** 3 minutes

## Standard Format

```
<type>/<issue-key>-<description>
```

**Examples:**
```bash
feature/PROJ-123-user-authentication
bugfix/PROJ-456-memory-leak
hotfix/PROJ-789-payment-api-timeout
task/PROJ-101-database-migration
```

## Branch Type Prefixes

| Branch Type | When to Use | JIRA Issue Type |
|-------------|-------------|-----------------|
| `feature/` | New functionality | Story, Feature, Improvement |
| `bugfix/` | Bug fixes (non-critical) | Bug, Defect |
| `hotfix/` | Critical production bugs | Bug (High/Critical priority) |
| `task/` | Technical work | Task, Sub-task |
| `epic/` | Large feature branch | Epic |
| `spike/` | Research, proof of concept | Spike, Research |
| `chore/` | Maintenance, refactoring | Chore, Maintenance |
| `docs/` | Documentation changes | Documentation |
| `release/` | Release preparation | N/A (version-based) |

## Naming Rules

**Do:**
- Use lowercase with hyphens (kebab-case)
- Include the JIRA issue key in UPPERCASE
- Keep description short (3-5 words max)
- Use imperative form: `add-feature` not `added-feature`

**Don't:**
- Use underscores or camelCase
- Include spaces or special characters
- Exceed 80 characters total
- Omit the issue key

## Examples

| Bad | Good | Why |
|-----|------|-----|
| `my-branch` | `feature/PROJ-123-user-login` | Missing issue key and type |
| `Feature_PROJ_123` | `feature/PROJ-123-add-oauth` | Underscores, no description |
| `proj-123` | `bugfix/PROJ-123-null-pointer` | Missing type and description |

## Using create_branch_name.py

```bash
# Auto-generate from JIRA issue
python create_branch_name.py PROJ-123
# Output: feature/proj-123-fix-login-button

# Auto-detect prefix from issue type
python create_branch_name.py PROJ-123 --auto-prefix

# Custom prefix
python create_branch_name.py PROJ-123 --prefix hotfix

# Generate and checkout in one command
$(python create_branch_name.py PROJ-123 --output git)
```

## Git Alias (Optional)

```bash
git config alias.jira-branch '!f() { $(python /path/to/create_branch_name.py "$1" --output git); }; f'

# Usage
git jira-branch PROJ-123
```

## Next Steps

- [Commit Message Formats](commit-messages.md) - Standard commit patterns
- [Smart Commits](smart-commits.md) - JIRA actions from commits
