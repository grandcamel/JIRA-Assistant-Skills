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
- [Extending JIRA Capability](#extending-jira-capability)
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

### Live-Test Configuration

Live Jira tests run only through the host-approved `jira-dev-host --suite`
wrapper, against the sandbox project key the live suite requires (`SBX`).
The default SBX profile reads credentials and `JIRA_DEFAULT_PROJECT=SBX` only
from the wrapper environment; do not put live-test credentials in settings
files or export them into worker sessions. The profile refuses missing
credentials or a non-SBX project, never creates a project, and verifies issue
cleanup at session teardown. See [Testing](docs/TESTING.md#live-integration-testing)
for the operator command and required cleanup output.

## Project Structure

```
skills/
├── jira/                 # The one skill: the Entry-Point Hint
│   ├── SKILL.md
│   └── tests/            # Routing check + sandbox validation
└── shared/               # Shared engineering test infrastructure
    └── tests/            # SBX live-profile + live_integration suite

tests/
├── e2e/                  # Help-only sufficiency arm
├── fixtures/confluence-stub/  # Non-shipped fixture for the routing check
└── floor_eval/           # Knowledge Floor eval

.claude/
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
   pytest skills/jira/tests/ -v
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

Use `jira` for the skill itself, or the area touched: `shared`, `e2e`,
`config`, `docs`.

### Examples

```bash
# New feature
feat(jira): document a new jira-as topic in the Entry-Point Hint

# Bug fix
fix(shared): correct retry backoff calculation

# Breaking change
feat(config)!: migrate to YAML configuration

BREAKING CHANGE: settings.json is now settings.yaml
```

## Testing

See [Before each plugin release](docs/TESTING.md#before-each-plugin-release) for the host-run Knowledge Floor check and model-policy trigger.

### Running Tests

```bash
# Run the offline suite, exactly as CI does
python -m pytest -q --deselect skills/jira/tests/test_routing.py \
  --deselect skills/jira/tests/test_sandbox_validation.py \
  --deselect tests/e2e/test_plugin_e2e.py

# Run the jira skill's tests only
pytest skills/jira/tests/ -v

# Live integration: host-approved operator only (absolute paths required)
lane=/absolute/path/to/JIRA-Assistant-Skills
# Run from your grand-camel-platform checkout's scripts/jira-dev-host
scripts/jira-dev-host "$lane" --suite \
  "$lane/.venv/bin/python" -m pytest \
  "$lane/skills/shared/tests/live_integration" -q -p no:cacheprovider
```

### Test Requirements

- All new scripts must have corresponding unit tests
- Tests should mock external API calls using `responses` library
- Aim for >80% coverage on new code
- Live integration tests require the dev wrapper and SBX; acceptance includes verified teardown

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

## Extending JIRA Capability

There is one skill (`skills/jira/SKILL.md`) and it does not grow per
feature. New JIRA capability belongs in the `jira-as` CLI itself,
in the separate [jira-as](https://github.com/grandcamel/jira-as)
repository -- not in a new skill directory or an expanded `SKILL.md` here.
`jira-as help`, `jira-as api search`, and `jira-as api describe` already
make new commands discoverable, so `skills/jira/SKILL.md` only needs to
change if the Entry-Point Hint's own four moves stop being true (see
`CLAUDE.md`'s "Extending JIRA Capability" section for the full rationale).

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
