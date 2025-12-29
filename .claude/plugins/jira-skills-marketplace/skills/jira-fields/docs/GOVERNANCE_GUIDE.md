# Field Governance Guide

Strategic guidance for managing custom fields at scale.

---

## Field Request Process

### Step 1: Request Submission

Requestor provides:

| Item | Description |
|------|-------------|
| Field name | Clear, reusable name |
| Purpose | Why is this field needed? |
| Projects | Which projects need it? |
| Issue types | Stories, Bugs, Tasks, etc.? |
| Required? | Is it mandatory? |
| Expected values | For select lists |
| Reporting needs | How will data be used? |

### Step 2: Admin Review Checklist

Before creating any field:

- [ ] Can an existing field be reused?
- [ ] Is this truly needed for work or reporting?
- [ ] Will this data be maintained over time?
- [ ] Does the name follow naming standards?
- [ ] What is the performance impact?
- [ ] Is the field type appropriate?

### Step 3: Implementation

If approved:

1. Create field with standard name
2. Set appropriate context (project-specific preferred)
3. Add to required screens
4. Document in field registry
5. Communicate to team

---

## Field Audit Schedule

### Monthly

- [ ] Review fields created this month
- [ ] Check for duplicate field names
- [ ] Verify field descriptions are complete

### Quarterly

- [ ] Audit field usage statistics
- [ ] Identify fields with < 5% usage
- [ ] Review global context fields
- [ ] Check for orphaned fields (no screen)
- [ ] Merge similar fields where possible

### Annually

- [ ] Full field inventory
- [ ] Archive/delete unused fields
- [ ] Review naming consistency
- [ ] Update field documentation
- [ ] Performance optimization review

---

## Field Cleanup Strategy

### Phase 1: Identify Candidates

Fields to review:

```
Criteria:
- Zero usage in last 180 days
- Usage in < 10 issues
- No screen associations
- Global context but < 20% project usage
```

### Phase 2: Stakeholder Review

For each candidate field:

1. Notify field creator
2. Check with project admins
3. Verify no active workflows reference it
4. Document decision

### Phase 3: Removal Process

```
1. Remove from screens first
2. Remove from contexts
3. Wait 30 days (grace period)
4. Delete field (data is lost!)
5. Document in change log
```

**Warning:** Field deletion is permanent. Export field data before deleting.

---

## Field Registry Template

Maintain a registry of all custom fields:

| Field Name | Field ID | Type | Context | Owner | Created | Last Review |
|------------|----------|------|---------|-------|---------|-------------|
| Story Points | customfield_10016 | Number | All Scrum | Agile Team | 2023-01 | 2025-12 |
| Epic Link | customfield_10014 | Epic Link | All Projects | Platform | 2023-01 | 2025-12 |
| Customer Impact | customfield_10050 | Select | SUPPORT | Support Mgr | 2024-06 | 2025-12 |

**Registry includes:**
- Field purpose and usage guidelines
- Projects and issue types using it
- Responsible owner/team
- Creation and last review dates
- Related workflow rules or automation

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Field proliferation | New fields instead of reusing | Reuse with contexts |
| Naming inconsistency | "StoryPoints", "Story Points" | Enforce standards |
| Global everything | All fields global context | Use project-specific |
| Required overload | Too many required fields | Require only essentials |
| Free text abuse | Text for enumerable data | Use select lists |
| Forgotten fields | Unused fields cluttering | Regular audits |
| Missing descriptions | No guidance on usage | Mandate descriptions |
| Single-use fields | Project-specific names | Design for reuse |

---

## Performance Guidelines

### Field Limits

```
Total custom fields:    < 500 (good), < 1000 (acceptable)
Global context fields:  < 50
Fields per screen:      < 30
Select list options:    < 200
```

### JIRA Cloud Limits (February 2026)

- Maximum 700 fields per field configuration
- Maximum 150 work types per scheme

### Red Flags

**Warning signs requiring immediate action:**

- Over 1000 total custom fields
- Over 100 fields with global context
- JIRA slow when viewing issue create screen
- Search queries timing out
- Board load times > 5 seconds

---

## Context Management

### Context Strategies

**Global Context:**
- Use for: Truly universal fields (Priority, Labels)
- Warning: Impacts performance at scale

**Project-Specific Context:**
- Use for: Fields only relevant to certain projects
- Benefit: Reduces clutter, improves performance

**Multi-Context Approach:**
- Use for: Same field name, different options per project
- Example: "Environment" with different options for different teams

### Context Decision Tree

```
Is the field used by ALL projects?
  |
  +-- Yes --> Global context
  |
  +-- No --> Project-specific context
       |
       +-- Same options everywhere? --> Single context
       |
       +-- Different options? --> Multiple contexts
```

---

## Naming Standards

### Rules

| Do | Don't |
|----|-------|
| Use title case: "Story Points" | Lowercase: "story points" |
| Be concise: "Sprint" | Verbose: "Sprint Assignment Field" |
| Avoid abbreviations: "Priority" | "Pri" |
| Use singular: "Epic Link" | "Epic Links" |
| Be descriptive: "Customer Impact" | Just "Impact" |

### Prohibited Patterns

- Including "custom" in name: "Custom Priority"
- Special characters: "Priority (P1-P5)"
- Duplicating built-in names: "Status"
- Jargon/acronyms: "MTTR Field"
- Excessively long: "Customer Reported Bug Severity Level"

---

## Quick Governance Checklist

### Before Creating a Field

1. Search existing fields
2. Check if reusable with contexts
3. Document purpose
4. Choose appropriate type
5. Plan for scale

### After Creating a Field

1. Set clear description
2. Add to appropriate screens
3. Configure validation
4. Document in registry
5. Communicate to users

### Quarterly Maintenance

1. Review usage statistics
2. Identify unused fields
3. Merge duplicates
4. Update documentation
5. Optimize contexts

---

## Cross-References

- [Quick Start Guide](QUICK_START.md) - Get started fast
- [Field Types Reference](FIELD_TYPES_REFERENCE.md) - All field types
- [Agile Field Guide](AGILE_FIELD_GUIDE.md) - Agile configuration
- [Best Practices](BEST_PRACTICES.md) - Design principles
