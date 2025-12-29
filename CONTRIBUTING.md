# Contributing to JIRA Assistant Skills

Thank you for your interest in contributing to JIRA Assistant Skills! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [Commit Guidelines](#commit-guidelines)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Adding New Skills](#adding-new-skills)
- [Adding New Scripts](#adding-new-scripts)

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributions from everyone regardless of experience level.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/jira-assistant-skills.git
   cd jira-assistant-skills
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/grandcamel/jira-assistant-skills.git
   ```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- JIRA Cloud instance for testing (free tier works)
- API token from [Atlassian](https://id.atlassian.com/manage-profile/security/api-tokens)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r .claude/skills/shared/scripts/lib/requirements.txt

# Install test dependencies
pip install pytest pytest-cov responses
```

### Configuration

```bash
export JIRA_API_TOKEN="your-token"
export JIRA_EMAIL="you@company.com"
export JIRA_SITE_URL="https://your-site.atlassian.net"
```

Or create `.claude/settings.local.json` (gitignored):
```json
{
  "jira": {
    "profiles": {
      "development": {
        "url": "https://your-site.atlassian.net",
        "email": "you@company.com",
        "default_project": "TEST"
      }
    },
    "default_profile": "development"
  }
}
```

## Project Structure

```
.claude/
├── skills/
│   ├── shared/           # Shared library (all skills depend on this)
│   │   ├── scripts/lib/  # Core modules (jira_client, config_manager, etc.)
│   │   └── tests/        # Shared library tests
│   ├── jira-issue/       # Issue CRUD skill
│   ├── jira-lifecycle/   # Workflow transitions
│   ├── jira-search/      # JQL and filters
│   └── ...               # Other skills
├── plugins/              # Claude Code plugins
└── settings.json         # Default configuration
```

## Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. Make your changes following project conventions

3. Run tests to ensure nothing is broken:
   ```bash
   pytest .claude/skills/*/tests/ -v
   ```

4. Commit using conventional commits (see below)

5. Push and create a pull request

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/). All commit messages must follow this format:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature or functionality |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `style` | Code style (formatting, no logic changes) |
| `refactor` | Code changes that neither fix bugs nor add features |
| `perf` | Performance improvements |
| `test` | Adding or updating tests |
| `build` | Build system or dependencies |
| `ci` | CI configuration |
| `chore` | Other changes |

### Scopes

Use the skill name as scope: `jira-issue`, `jira-lifecycle`, `jira-search`, `jira-collaborate`, `jira-agile`, `jira-relationships`, `jira-time`, `jira-jsm`, `jira-bulk`, `jira-dev`, `jira-fields`, `jira-ops`, `shared`, `config`, `docs`

### Examples

```bash
# New feature
feat(jira-issue): add support for creating subtasks

# Bug fix
fix(shared): correct retry backoff calculation

# Breaking change
feat(config)!: migrate to YAML configuration

BREAKING CHANGE: settings.json is now settings.yaml
```

## Testing

### Running Tests

```bash
# Run all unit tests
pytest .claude/skills/*/tests/ -v

# Run specific skill tests
pytest .claude/skills/jira-issue/tests/ -v

# Run with coverage
pytest .claude/skills/*/tests/ --cov=.claude/skills -v

# Run live integration tests (requires JIRA credentials)
pytest .claude/skills/shared/tests/live_integration/ --profile development -v
```

### Test Requirements

- All new scripts must have corresponding unit tests
- Tests should mock external API calls using `responses` library
- Aim for >80% coverage on new code
- Live integration tests are optional but appreciated

### TDD Best Practices

1. Write failing tests first
2. Implement feature to pass tests
3. Commit after all tests pass
4. Include test counts in commit messages:
   ```
   feat(jira-search): implement jql_validate.py (7/7 tests passing)
   ```

## Pull Request Process

1. **Update documentation**: If adding features, update relevant SKILL.md files
2. **Add tests**: Include unit tests for new functionality
3. **Pass CI**: Ensure all tests pass
4. **Clear description**: Explain what changes and why
5. **Link issues**: Reference any related issues

### PR Template

```markdown
## Summary
Brief description of changes

## Changes
- Change 1
- Change 2

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing performed
- [ ] All tests passing

## Related Issues
Fixes #123
```

## Adding New Skills

1. Create skill directory structure:
   ```
   .claude/skills/new-skill/
   ├── SKILL.md              # Skill description for Claude
   ├── scripts/              # Python scripts
   └── tests/                # Unit tests
   ```

2. Create `SKILL.md` with required sections:
   - YAML frontmatter with `name`, `description`, `when_to_use`
   - "What this skill does" section
   - "Available scripts" section
   - "Examples" section

3. Scripts must:
   - Use shared library imports
   - Support `--profile` argument
   - Include argparse with help text
   - Handle errors with `print_error()`

4. Update `jira-assistant/SKILL.md` routing table

## Adding New Scripts

When adding scripts to existing skills:

1. **Location**: Place in skill's `scripts/` directory
2. **Imports**: Use standard path injection:
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))
   ```
3. **CLI**: Use argparse with descriptive help
4. **Errors**: Catch `JiraError`, call `print_error()`, `sys.exit(1)`
5. **Profile**: Add `--profile` argument
6. **Executable**: `chmod +x script.py` with shebang
7. **Documentation**: Update skill's SKILL.md

### Script Template

```python
#!/usr/bin/env python3
"""Brief description of what this script does."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))

from config_manager import get_jira_client
from error_handler import print_error, JiraError
from validators import validate_issue_key


def main():
    parser = argparse.ArgumentParser(
        description='What this script does',
        epilog='Example: %(prog)s PROJ-123'
    )
    parser.add_argument('issue_key', help='The issue key')
    parser.add_argument('--profile', help='JIRA profile to use')
    args = parser.parse_args()

    try:
        validate_issue_key(args.issue_key)
        client = get_jira_client(profile=args.profile)
        # Your implementation here
        print(f"Success: {args.issue_key}")
    except JiraError as e:
        print_error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
```

## Questions?

- Open a [GitHub Discussion](https://github.com/grandcamel/jira-assistant-skills/discussions)
- File an [Issue](https://github.com/grandcamel/jira-assistant-skills/issues)

Thank you for contributing!
