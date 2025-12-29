# JIRA Custom Field Best Practices

Core design principles and configuration guidelines for custom fields.

---

## Table of Contents

1. [Field Design Principles](#field-design-principles)
2. [Naming Conventions](#naming-conventions)
3. [Context Management](#context-management)
4. [Screen Configuration](#screen-configuration)
5. [Validation Guidelines](#validation-guidelines)
6. [Quick Reference](#quick-reference)

**For detailed guides, see:**
- [Quick Start Guide](QUICK_START.md) - Get started in 5 minutes
- [Field Types Reference](FIELD_TYPES_REFERENCE.md) - Complete type reference
- [Agile Field Guide](AGILE_FIELD_GUIDE.md) - Agile configuration
- [Governance Guide](GOVERNANCE_GUIDE.md) - Field management at scale

---

## Field Design Principles

### The Four Questions

Before creating any custom field, ask:

1. **Is it necessary?** - Will this data be used for work or reporting?
2. **Does it already exist?** - Can an existing field be reused?
3. **Is it specific or reusable?** - Should it apply to one project or many?
4. **Will it scale?** - What happens when you have 10,000 issues?

### Design Guidelines

**Do:**
- Design fields for reuse across projects
- Use descriptive field descriptions
- Choose the most restrictive field type that works
- Plan for data validation upfront
- Consider reporting needs when designing

**Don't:**
- Create project-specific fields if avoidable
- Use free-text when a select list would work
- Create fields for data that won't be maintained
- Duplicate built-in field functionality
- Create fields for temporary needs

### Type Selection Quick Guide

| Need This | Use This Type |
|-----------|---------------|
| Free-form input, unique per issue | Text Field |
| Known set of values, prevent typos | Select List |
| Calculations, range queries | Number |
| Deadlines, time-based queries | Date/DateTime |

See [Field Types Reference](FIELD_TYPES_REFERENCE.md) for complete guidance.

---

## Naming Conventions

### Naming Rules

**Format:** Use clear, generic names that describe the field's purpose, not its use case.

| Bad (Too Specific) | Good (Reusable) | Why Better |
|-------------------|----------------|------------|
| Marketing Campaign ID | Campaign ID | Usable by all departments |
| Bug Severity | Severity | Works for bugs and incidents |
| Dev Team Estimate | Effort Estimate | Any team can use |
| Release 2.0 Flag | Release Flag | Works for all releases |

### Standards

**Do:**
- Use title case: "Story Points" not "story points"
- Be concise: "Sprint" not "Sprint Assignment Field"
- Avoid abbreviations: "Priority" not "Pri"
- Use singular form: "Epic Link" not "Epic Links"
- Be descriptive: "Customer Impact" not "Impact"

**Don't:**
- Include "custom" in the name
- Use special characters
- Duplicate built-in field names
- Use jargon or acronyms
- Make names excessively long

### Field Descriptions

Every custom field should have a clear description:

```
Field: Effort Estimate
Description: Estimated effort in story points (Fibonacci: 1, 2, 3, 5, 8, 13).
Used for sprint planning and velocity tracking. Required for Story and Task types.
Projects: PROJ, TEAM, MOBILE
```

**Include:**
- Purpose of the field
- Valid values or format
- Which projects/issue types use it
- Whether it's required or optional

---

## Context Management

### Understanding Field Contexts

A **field context** defines:
- Which projects the field applies to
- Which issue types can use the field
- Default values for the field
- Available options (for select lists)

### Context Strategies

| Strategy | When to Use | Impact |
|----------|-------------|--------|
| Global | Field is truly universal | Performance concern at scale |
| Project-specific | Field only for certain projects | Better performance, less clutter |
| Multi-context | Same field, different options per project | Reuse name, customize values |

### Best Practices

**Do:**
- Limit global contexts to truly universal fields
- Use project-specific contexts when possible
- Document which context applies to which project
- Review contexts quarterly
- Set meaningful default values

**Don't:**
- Create global contexts by default
- Have overlapping contexts for the same field
- Create contexts for single-use fields
- Use contexts to hide poor field design

---

## Screen Configuration

### Screen Types

| Screen Type | Purpose | Fields to Include |
|-------------|---------|-------------------|
| **Create** | Issue creation | Minimal - only required fields |
| **Edit** | Issue modification | Create fields + status/resolution |
| **View** | Issue display | All fields including system fields |

### Create Screen - Minimal Fields

Essential fields only:
- Summary
- Issue Type
- Priority
- Description
- Assignee

Add sparingly:
- Story Points (for Stories)
- Labels
- Components

### Edit Screen - Extended Fields

Create screen fields, plus:
- Status
- Resolution
- Time Tracking
- Custom fields relevant to workflow

### Field Ordering

Logical flow for screens:

1. **Core fields:** Summary, Type, Priority
2. **Context fields:** Description, Acceptance Criteria
3. **Planning fields:** Story Points, Sprint, Epic Link
4. **Assignment fields:** Assignee, Reporter
5. **Organizational fields:** Labels, Components
6. **Tracking fields:** Due Date, Fix Version
7. **Custom fields:** Grouped by category

---

## Validation Guidelines

### Built-in Validation Options

| Field Type | Validation Options |
|------------|-------------------|
| Number | min/max values |
| Text | character limit, regex pattern |
| Date | date range constraints |
| Select | required selection |

### Best Practices

**Do:**
- Validate at creation time when possible
- Use select lists instead of free text
- Provide clear error messages
- Test validation rules thoroughly
- Document validation requirements

**Don't:**
- Make too many fields required
- Use complex regex that users don't understand
- Validate fields that change frequently
- Block legitimate use cases
- Forget to communicate validation rules

---

## Quick Reference

### Essential Scripts

```bash
# List all custom fields
python list_fields.py

# List Agile fields with IDs
python list_fields.py --agile

# Check project field availability
python check_project_fields.py PROJ --check-agile

# Configure Agile fields (company-managed)
python configure_agile_fields.py PROJ --dry-run
python configure_agile_fields.py PROJ

# Create new custom field (requires admin)
python create_field.py --name "Field Name" --type number
```

### Common Agile Field IDs

See [Agile Field IDs Reference](../assets/agile-field-ids.md) for complete and current list.

Always verify with: `python list_fields.py --agile`

### Common JQL for Field Management

```sql
-- Find issues missing required field
"Story Points" IS EMPTY AND type = Story

-- Find issues with specific field value
"Customer Impact" = High

-- Check field population rate
"Custom Field Name" IS NOT EMPTY

-- Issues with field changes
"Customer Impact" CHANGED DURING (startOfMonth(), now())
```

---

## Additional Resources

### Official Documentation

- [Jira custom fields: The complete guide 2025](https://blog.isostech.com/jira-custom-fields-the-complete-guide-2025)
- [Optimize your custom fields - Atlassian](https://confluence.atlassian.com/display/ENTERPRISE/Optimize+your+custom+fields)
- [Managing custom fields effectively - Atlassian](https://confluence.atlassian.com/display/ENTERPRISE/Managing+custom+fields+in+Jira+effectively)
- [Jira custom fields governance - Atlassian Success Central](https://success.atlassian.com/solution-resources/agile-and-devops-ado/agile-at-scale-practices/jira-custom-fields-governance)

### Related Guides

- [Quick Start Guide](QUICK_START.md) - Get started in 5 minutes
- [Field Types Reference](FIELD_TYPES_REFERENCE.md) - All field types
- [Agile Field Guide](AGILE_FIELD_GUIDE.md) - Agile configuration
- [Governance Guide](GOVERNANCE_GUIDE.md) - Field management at scale
- [Agile Field IDs](../assets/agile-field-ids.md) - Field ID lookup

---

*Last updated: December 2025*
