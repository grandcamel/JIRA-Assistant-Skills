# Trust Signals Section

> Production-ready markdown sections to embed in the project README.
> Implements Options 6B (Minimal Badges), 6D (Test Table), and 6I (Security).

---

## Section 1: Badges (Option 6B)

Place this immediately after the project title/logo in README.md:

```markdown
<p align="center">
  <img src="https://img.shields.io/badge/tests-422%2B%20passing-brightgreen?logo=pytest" alt="Tests">
  <img src="https://img.shields.io/badge/python-3.8+-3776AB?logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
</p>
```

**Rendered Preview:**

<p align="center">
  <img src="https://img.shields.io/badge/tests-422%2B%20passing-brightgreen?logo=pytest" alt="Tests">
  <img src="https://img.shields.io/badge/python-3.8+-3776AB?logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
</p>

---

## Section 2: Test Coverage Table (Option 6D)

Place in a "Quality Assurance" or "Testing" section:

```markdown
## Test Coverage

| Category | Tests | Description |
|----------|------:|-------------|
| Core Integration | 157 | Issue lifecycle, collaboration, agile workflows |
| JSM Integration | 94 | Service desks, SLAs, approvals, knowledge base |
| New Skills Integration | 87 | Bulk ops, dev workflows, fields, cache |
| Unit Tests | 84 | Isolated function validation |
| **Total** | **422** | **All passing** |

> Tests run against live JIRA Cloud instances to ensure real-world reliability.
```

**Rendered Preview:**

## Test Coverage

| Category | Tests | Description |
|----------|------:|-------------|
| Core Integration | 157 | Issue lifecycle, collaboration, agile workflows |
| JSM Integration | 94 | Service desks, SLAs, approvals, knowledge base |
| New Skills Integration | 87 | Bulk ops, dev workflows, fields, cache |
| Unit Tests | 84 | Isolated function validation |
| **Total** | **422** | **All passing** |

> Tests run against live JIRA Cloud instances to ensure real-world reliability.

---

## Section 3: Security (Option 6I)

Place in a dedicated "Security" section:

```markdown
## Security

<p>
  <img src="https://img.shields.io/badge/HTTPS-required-blue" alt="HTTPS Required">
  <img src="https://img.shields.io/badge/credentials-.gitignored-important" alt="Credentials Gitignored">
</p>

- **No hardcoded secrets** - API tokens stored in environment variables or gitignored files
- **HTTPS-only connections** - All JIRA API requests enforced over secure transport
- **Input validation** - All user data validated before API calls
- **Credential isolation** - `settings.local.json` gitignored by default
- **No credential logging** - Sensitive data excluded from logs and error output
```

**Rendered Preview:**

## Security

<p>
  <img src="https://img.shields.io/badge/HTTPS-required-blue" alt="HTTPS Required">
  <img src="https://img.shields.io/badge/credentials-.gitignored-important" alt="Credentials Gitignored">
</p>

- **No hardcoded secrets** - API tokens stored in environment variables or gitignored files
- **HTTPS-only connections** - All JIRA API requests enforced over secure transport
- **Input validation** - All user data validated before API calls
- **Credential isolation** - `settings.local.json` gitignored by default
- **No credential logging** - Sensitive data excluded from logs and error output

---

## Combined Example

Here is how all three sections look together in a README context:

```markdown
# JIRA Assistant Skills

<p align="center">
  <img src="https://img.shields.io/badge/tests-422%2B%20passing-brightgreen?logo=pytest" alt="Tests">
  <img src="https://img.shields.io/badge/python-3.8+-3776AB?logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
</p>

AI-powered JIRA automation through 14 modular Claude Code skills.

## Test Coverage

| Category | Tests | Description |
|----------|------:|-------------|
| Core Integration | 157 | Issue lifecycle, collaboration, agile workflows |
| JSM Integration | 94 | Service desks, SLAs, approvals, knowledge base |
| New Skills Integration | 87 | Bulk ops, dev workflows, fields, cache |
| Unit Tests | 84 | Isolated function validation |
| **Total** | **422** | **All passing** |

> Tests run against live JIRA Cloud instances to ensure real-world reliability.

## Security

<p>
  <img src="https://img.shields.io/badge/HTTPS-required-blue" alt="HTTPS Required">
  <img src="https://img.shields.io/badge/credentials-.gitignored-important" alt="Credentials Gitignored">
</p>

- **No hardcoded secrets** - API tokens stored in environment variables or gitignored files
- **HTTPS-only connections** - All JIRA API requests enforced over secure transport
- **Input validation** - All user data validated before API calls
- **Credential isolation** - `settings.local.json` gitignored by default
- **No credential logging** - Sensitive data excluded from logs and error output
```

---

## Implementation Notes

### Metrics Source

Test counts derived from project documentation in `CLAUDE.md`:
- Core skills: 157 live integration tests
- JSM skill: 94 live integration tests
- New skills: 87 live + 84 unit tests

### Maintenance

Update badge test counts when significant test additions occur. The `422+` format allows for minor additions without requiring immediate updates.

### GitHub Stars Badge (Optional)

When the repository is public on GitHub, add this to the badge section:

```markdown
<img src="https://img.shields.io/github/stars/YOUR_ORG/jira-assistant-skills?style=social" alt="GitHub Stars">
```

### Alternative: Grouped Badge Layout

For repositories preferring categorized badges:

```markdown
**Quality:** ![Tests](https://img.shields.io/badge/tests-422%2B%20passing-brightgreen) ![Live Tests](https://img.shields.io/badge/live%20integration-338%20passing-blue)

**Stack:** ![Python](https://img.shields.io/badge/python-3.8+-3776AB) ![Claude Code](https://img.shields.io/badge/claude%20code-skills-blueviolet)

**License:** ![MIT](https://img.shields.io/badge/license-MIT-green)
```
