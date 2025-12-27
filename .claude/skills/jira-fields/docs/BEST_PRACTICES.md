# JIRA Custom Field Management Best Practices

Comprehensive guide to managing custom fields, screens, field contexts, and Agile field configuration in JIRA.

---

## Table of Contents

1. [Field Type Reference](#field-type-reference)
2. [Field Design Principles](#field-design-principles)
3. [Naming Conventions](#naming-conventions)
4. [Field Context Management](#field-context-management)
5. [Screen Configuration](#screen-configuration)
6. [Agile Field Configuration](#agile-field-configuration)
7. [Field Validation and Constraints](#field-validation-and-constraints)
8. [Performance Optimization](#performance-optimization)
9. [Field Governance and Cleanup](#field-governance-and-cleanup)
10. [Common Pitfalls](#common-pitfalls)
11. [Quick Reference Card](#quick-reference-card)

---

## Field Type Reference

### Standard Field Types

| Field Type | Use Case | Storage | Searchable | Example |
|------------|----------|---------|------------|---------|
| **Text Field** | Short single-line text | String (255 chars) | Yes | Product name, ticket number |
| **Text Area** | Multi-line text | Text | Yes | Description, notes |
| **Number** | Numeric values | Float | Yes | Story points, budget |
| **Date Picker** | Date only | Date | Yes | Target date, deadline |
| **Date Time** | Date and time | DateTime | Yes | Scheduled deployment |
| **Select List** | Single choice | String | Yes | Priority, severity |
| **Multi-Select** | Multiple choices | Array | Yes | Affected components |
| **Checkbox** | Multiple options | Array | Yes | Features included |
| **Radio Buttons** | Single choice (displayed as radio) | String | Yes | Approval status |
| **URL** | Web links | String | Yes | Documentation link |
| **User Picker** | Single user | User object | Yes | Approver, reviewer |
| **Multi-User Picker** | Multiple users | User array | Yes | Reviewers, stakeholders |
| **Labels** | Free-form tags | String array | Yes | Tags, categories |

### Agile-Specific Field Types

| Field Type | JIRA Name | Use Case | Typical Field ID |
|------------|-----------|----------|------------------|
| **Sprint** | Sprint | Track sprint assignment | customfield_10020 |
| **Story Points** | Story Point Estimate | Effort estimation | customfield_10016 |
| **Epic Link** | Epic Link | Link story to epic | customfield_10014 |
| **Epic Name** | Epic Name | Name of the epic | customfield_10011 |
| **Epic Color** | Epic Color | Visual epic identifier | customfield_10012 |
| **Rank** | Rank | Backlog ordering | customfield_10019 |

**Important:** Field IDs vary by JIRA instance. Always use `list_fields.py --agile` to find correct IDs.

### Advanced Field Types

| Field Type | Use Case | Requires Plugin | Notes |
|------------|----------|-----------------|-------|
| **Cascading Select** | Hierarchical choices | No | Good for category/subcategory |
| **Version Picker** | Release versions | No | Built-in for fix/affect versions |
| **Component Picker** | Project components | No | Built-in field |
| **Project Picker** | Link to other projects | No | Cross-project references |
| **Read Only Text** | Calculated/auto-filled | No | Cannot be edited by users |

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

### Field Type Selection

**Choose Text Field when:**
- Free-form input is required
- Values are unique per issue
- No need for data validation
- Examples: External ticket ID, customer reference

**Choose Select List when:**
- Values are from a known set
- Need consistency across issues
- Want to prevent typos
- Examples: Severity, environment, platform

**Choose Number when:**
- Performing calculations
- Need range queries
- Sorting numerically matters
- Examples: Story points, cost, count

**Choose Date when:**
- Tracking deadlines or milestones
- Need time-based queries
- Want calendar integration
- Examples: Target date, review deadline

---

## Naming Conventions

### Field Naming Standards

**Format:** Use clear, generic names that describe the field's purpose, not its use case.

| Bad (Too Specific) | Good (Reusable) | Why Better |
|-------------------|----------------|------------|
| Marketing Campaign ID | Campaign ID | Usable by all departments |
| Bug Severity | Severity | Works for bugs and incidents |
| Dev Team Estimate | Effort Estimate | Any team can use |
| Release 2.0 Flag | Release Flag | Works for all releases |

### Naming Rules

**Do:**
- Use title case: "Story Points" not "story points"
- Be concise: "Sprint" not "Sprint Assignment Field"
- Avoid abbreviations: "Priority" not "Pri"
- Use singular form: "Epic Link" not "Epic Links"
- Be descriptive: "Customer Impact" not "Impact"

**Don't:**
- Include "custom" in the name: "Custom Priority" ❌
- Use special characters: "Priority (P1-P5)" ❌
- Duplicate built-in field names: "Status" ❌
- Use jargon or acronyms: "MTTR Field" ❌
- Make names too long: "Customer Reported Bug Severity Level" ❌

### Field Description Best Practices

Every custom field should have a clear description:

```markdown
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
- Examples of proper usage

---

## Field Context Management

### Understanding Field Contexts

A **field context** defines:
- Which projects the field applies to
- Which issue types can use the field
- Default values for the field
- Available options (for select lists)

### Context Strategies

**Global Context:**
```
Applies to: All projects
Issue Types: All types
Use when: Field is universal (e.g., Priority, Labels)
Warning: Impacts performance at scale
```

**Project-Specific Context:**
```
Applies to: Selected projects (PROJ, TEAM)
Issue Types: Selected types (Story, Bug)
Use when: Field is only relevant to certain projects
Benefit: Reduces clutter, improves performance
```

**Multi-Context Approach:**
```
Context 1: Engineering projects (different options)
Context 2: Marketing projects (different options)
Use when: Same field name, different option values
Benefit: Reuse field name with project-specific values
```

### Context Configuration Best Practices

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
- Forget to update contexts when adding projects
- Use contexts to hide poor field design

### Setting Default Values

**Good defaults:**
- Most common value: Priority = "Medium"
- Neutral value: Severity = "Not Set"
- Empty for required fields: Forces user choice
- Current sprint: Sprint = currentSprint()

**Bad defaults:**
- Critical or urgent priorities
- Specific user assignments
- Far future dates
- Values that rarely apply

---

## Screen Configuration

### Screen Hierarchy

JIRA uses a three-level screen system:

```
Project
  └─ Issue Type Screen Scheme
       └─ Screen Scheme (Create, Edit, View)
            └─ Screen (actual fields)
```

### Screen Types

| Screen Type | Purpose | When Shown |
|-------------|---------|------------|
| **Create** | Fields when creating issues | Create Issue dialog |
| **Edit** | Fields when editing issues | Edit Issue screen |
| **View** | Fields when viewing issues | Issue detail view |

**Best Practice:** Use different screens for different operations to avoid clutter.

### Screen Design Guidelines

**Create Screen - Minimal Fields:**
```
Required for creation:
✓ Summary
✓ Issue Type
✓ Priority
✓ Description
✓ Assignee

Optional but useful:
✓ Labels
✓ Components
✓ Fix Version
```

**Edit Screen - More Fields:**
```
All Create fields, plus:
✓ Status
✓ Resolution
✓ Time Tracking
✓ Custom fields
✓ Attachments
```

**View Screen - Complete Context:**
```
All fields including:
✓ Reporter, Created Date
✓ Updated Date, Resolved Date
✓ Watchers
✓ Linked Issues
✓ Work Log
```

### Field Ordering on Screens

**Logical Flow:**
1. **Core fields first:** Summary, Type, Priority
2. **Context fields:** Description, Acceptance Criteria
3. **Planning fields:** Story Points, Sprint, Epic Link
4. **Assignment fields:** Assignee, Reporter
5. **Organizational fields:** Labels, Components
6. **Tracking fields:** Due Date, Fix Version
7. **Custom fields:** Grouped by category

### Tab Organization for Complex Projects

For projects with many fields, use field tabs:

```
Tab 1: Details
- Summary, Type, Priority, Status
- Description, Acceptance Criteria

Tab 2: Planning
- Story Points, Sprint, Epic Link
- Fix Version, Components

Tab 3: Tracking
- Time Tracking, Due Date
- Custom effort fields

Tab 4: Technical
- Environment, Browser
- Technical details, logs
```

---

## Agile Field Configuration

### Essential Agile Fields

**Must-Have for Scrum:**
1. **Sprint** - Track which sprint contains the work
2. **Story Points** - Estimate effort for planning
3. **Epic Link** - Group related stories

**Nice-to-Have:**
4. **Rank** - Manual ordering in backlog
5. **Epic Name** - Visible epic identifier
6. **Epic Color** - Visual distinction

### Finding Agile Field IDs

Field IDs vary by instance. Use the jira-fields scripts:

```bash
# List all Agile fields
python list_fields.py --agile

# Check specific project
python check_project_fields.py PROJ --check-agile

# Output:
# ✓ sprint: Sprint (customfield_10020)
# ✓ story_points: Story Points (customfield_10016)
# ✓ epic_link: Epic Link (customfield_10014)
```

### Common Agile Field IDs by Instance Type

**JIRA Cloud (typical):**
```
Sprint:        customfield_10020
Story Points:  customfield_10016 or customfield_10040
Epic Link:     customfield_10014
Epic Name:     customfield_10011
Epic Color:    customfield_10012
Rank:          customfield_10019
```

**JIRA Server/Data Center:**
```
May vary significantly - always verify with list_fields.py
```

### Configuring Story Points

**Step 1: Verify Field Exists**
```bash
python list_fields.py --filter "story"
```

**Step 2: Check Project Access**
```bash
python check_project_fields.py PROJ --type Story
```

**Step 3: Add to Screens (if missing)**
```bash
# For company-managed projects
python configure_agile_fields.py PROJ --dry-run
python configure_agile_fields.py PROJ
```

**Step 4: Configure in Board Settings**
1. Go to Board > Configure
2. Estimation > Story Point Estimate
3. Select the correct custom field
4. Save

### Configuring Epic Link

**For Company-Managed Projects:**
1. Field should exist: `customfield_10014`
2. Add to Story/Task create screens
3. Add to Story/Task edit screens
4. Set field context to include project

**For Team-Managed Projects:**
1. Project Settings > Features
2. Enable "Epics" feature
3. Epic Link automatically available
4. Configure in issue types settings

### Sprint Field Configuration

**Automatic in Scrum Projects:**
- Sprint field created automatically
- Managed by board configuration
- Available on backlog and board
- Cannot be edited directly in issues

**Manual for Kanban-to-Scrum Migration:**
```bash
# Verify Sprint field exists
python list_fields.py --filter "sprint"

# Add to project screens
python configure_agile_fields.py PROJ
```

### Board Field Configuration

When setting up Agile boards, map these fields:

**In Board Settings > Estimation:**
```
Estimation Statistic: Story Points
  └─ Field: Story Point Estimate (customfield_10016)

Time Tracking: Original Time Estimate
  └─ Field: Original Estimate (built-in)
```

**In Board Settings > Card Layout:**
```
Fields to display on cards:
✓ Assignee
✓ Priority
✓ Story Points (as badge)
✓ Due Date
✓ Labels
```

---

## Field Validation and Constraints

### Built-in Validation

**Number Fields:**
- Set min/max values in field configuration
- Use field validator for range checking
- Example: Story Points between 1-13

**Text Fields:**
- Character limits (255 for text, unlimited for textarea)
- Regular expression validation
- Example: Email format, issue key pattern

**Date Fields:**
- Date range validation
- Must be after/before another field
- Example: End date after start date

### Custom Validators

**Required Field Validators:**
```
Applies to: Specific transitions or screens
Use case: Ensure field populated before moving forward
Example: "Assignee required when moving to In Progress"
```

**Field Format Validators:**
```
Applies to: Text fields
Use case: Enforce specific patterns
Example: "External ID must match EXT-[0-9]+"
```

**Conditional Required Fields:**
```
Applies to: Transitions with conditions
Use case: Field required only in certain scenarios
Example: "Root Cause required when resolving as Fixed"
```

### Validation Best Practices

**Do:**
- Validate at creation time when possible
- Use select lists instead of free text
- Provide clear error messages
- Test validation rules thoroughly
- Document validation requirements

**Don't:**
- Make too many fields required
- Use complex regex that users don't understand
- Validate fields that may change frequently
- Implement validation that blocks legitimate use cases
- Forget to communicate validation rules to users

---

## Performance Optimization

### Performance Impact of Custom Fields

**High Impact:**
- Global context fields (applied to all projects)
- Text area fields with rich text enabled
- Cascading select fields
- Fields with complex validation
- Fields used in hundreds of workflows

**Medium Impact:**
- Project-specific context fields
- Select lists with many options (100+)
- Multi-select and checkbox fields
- Date/time fields with automation

**Low Impact:**
- Simple text fields with project context
- Number fields
- User picker fields
- Labels (built-in field)

### Performance Best Practices

**Field Limits:**
```
Total custom fields:      < 500 (good), < 1000 (acceptable)
Global context fields:    < 50
Fields per screen:        < 30
Select list options:      < 200
```

**Starting February 2026:**
JIRA Cloud will enforce:
- Maximum 700 fields per field configuration
- Maximum 150 work types per scheme

### Optimization Strategies

**1. Reduce Global Contexts**
```bash
# Before: Global context for "Marketing Campaign"
Context: All Projects

# After: Project-specific context
Context: MKT, SALES, PROD only
```

**2. Merge Similar Fields**
```bash
# Before: 3 fields
- Engineering Priority
- Marketing Priority
- Support Priority

# After: 1 field with context-specific options
- Priority (with different option sets per project)
```

**3. Archive Unused Fields**
```bash
# Check field usage
# If last update > 180 days and < 100 issues:
# Remove from screens
# Remove from contexts
# Consider deleting
```

**4. Limit Screen Fields**
```bash
# Review each screen
python check_project_fields.py PROJ --type Story

# Remove fields not used in last 90 days
# Move rarely-used fields to tabs
# Keep create screen minimal
```

### Indexing Considerations

**Searchable Fields:**
- Impact index size and search performance
- Only make fields searchable if used in JQL
- Review searchable status quarterly

**Non-Searchable Fields:**
- Good for display-only information
- Better performance
- Examples: Internal notes, formatting fields

---

## Field Governance and Cleanup

### Field Request Process

**Step 1: Request Submission**
```
Requestor fills out:
- Field name and purpose
- Projects that need it
- Issue types that need it
- Required or optional?
- Expected values (if select list)
- Reporting needs
```

**Step 2: Admin Review**
```
Admin checks:
□ Can existing field be reused?
□ Is this truly needed?
□ Will this be maintained?
□ Does it align with naming standards?
□ What's the performance impact?
```

**Step 3: Implementation**
```
If approved:
1. Create field with standard name
2. Set appropriate context
3. Add to required screens
4. Document in field registry
5. Communicate to team
```

### Field Audit Checklist

**Monthly:**
- Review fields created this month
- Check for duplicate field names
- Verify field descriptions are complete

**Quarterly:**
- Audit field usage statistics
- Identify fields with < 5% usage
- Review global context fields
- Check for orphaned fields (no screen)

**Annually:**
- Full field inventory
- Merge similar fields where possible
- Archive/delete unused fields
- Review naming consistency
- Update field documentation

### Field Cleanup Strategy

**Phase 1: Identify Candidates**
```sql
Fields with:
- Zero usage in last 180 days
- Usage in < 10 issues
- No screen associations
- Global context but project-specific use
```

**Phase 2: Stakeholder Review**
```
For each field:
1. Notify field creator
2. Check with project admins
3. Verify no active workflows reference it
4. Document decision
```

**Phase 3: Removal**
```
Process:
1. Remove from screens first
2. Remove from contexts
3. Wait 30 days
4. Delete field (data is lost!)
5. Document in change log
```

### Field Documentation

**Maintain a Field Registry:**
```markdown
| Field Name | Field ID | Type | Context | Owner | Created | Last Review |
|------------|----------|------|---------|-------|---------|-------------|
| Story Points | customfield_10016 | Number | All Scrum | Agile Team | 2023-01 | 2025-12 |
| Epic Link | customfield_10014 | Epic Link | All Projects | Platform | 2023-01 | 2025-12 |
| Customer Impact | customfield_10050 | Select | SUPPORT | Support Mgr | 2024-06 | 2025-12 |
```

**Include in Registry:**
- Field purpose and usage guidelines
- Projects and issue types using it
- Responsible owner/team
- Creation and last review dates
- Related workflow rules or automation

---

## Common Pitfalls

### Anti-Patterns to Avoid

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Field Proliferation** | Creating new fields instead of reusing | Reuse existing fields with contexts |
| **Naming Inconsistency** | "StoryPoints", "Story Points", "story_points" | Enforce naming standards |
| **Global Everything** | All fields have global context | Use project-specific contexts |
| **Required Field Overload** | Too many required fields on create | Require only essential fields |
| **Free Text Abuse** | Text fields for enumerable data | Use select lists for known values |
| **Forgotten Fields** | Unused fields cluttering instance | Regular audits and cleanup |
| **Missing Descriptions** | No guidance on field usage | Mandate field descriptions |
| **Single-Use Fields** | Project-specific field names | Design for reusability |
| **No Validation** | Accepting any input | Use validators and field types |
| **Screen Clutter** | 50+ fields on create screen | Minimize, use tabs, split screens |

### Red Flags

**In Field Configuration:**
- Field has been created but never used
- Field name conflicts with built-in field
- Global context with < 20% project usage
- Select list with 1-2 options (use checkbox)
- Multiple fields with similar names

**In Screen Configuration:**
- Same screen for create, edit, and view
- More than 40 fields on a single screen
- Required fields users always skip
- Fields appearing on wrong issue types
- Duplicate fields on same screen

**In Performance:**
- JIRA slow when viewing issue create screen
- Search queries timing out
- Board load times > 5 seconds
- Over 1000 total custom fields
- Over 100 fields with global context

### Troubleshooting Common Issues

**Issue: Field not showing on create screen**

Solutions:
1. Check field context includes the project
2. Verify field is on the create screen
3. Check issue type screen scheme mapping
4. For team-managed projects, check project settings
5. Verify user has permission to see field

**Issue: Field values not saving**

Solutions:
1. Check field validation rules
2. Verify field is not read-only
3. Check workflow validators on transition
4. Verify user has edit permission
5. Check for conflicting automation rules

**Issue: Agile fields not working on board**

Solutions:
1. Verify correct field ID in board settings
2. Check field context includes project
3. Verify field is searchable
4. Check that board includes correct project
5. Use `list_fields.py --agile` to verify field

**Issue: Performance degradation after adding fields**

Solutions:
1. Change global contexts to project-specific
2. Remove unused fields from screens
3. Disable searchable on display-only fields
4. Archive unused fields
5. Review and optimize field validators

---

## Quick Reference Card

### Field Type Cheat Sheet

```
Short text      → Text Field (255 chars)
Long text       → Text Area (unlimited)
Numbers         → Number Field
Dates           → Date Picker or Date Time
Single choice   → Select List or Radio
Multiple choice → Multi-Select or Checkbox
User reference  → User Picker
URL             → URL Field
Free tags       → Labels
```

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

```
Always verify with: python list_fields.py --agile

Typical IDs (may vary):
- Sprint:        customfield_10020
- Story Points:  customfield_10016
- Epic Link:     customfield_10014
- Epic Name:     customfield_10011
- Rank:          customfield_10019
```

### Field Context Decision Tree

```
Is the field used by ALL projects?
  ├─ Yes → Global context
  └─ No → Project-specific context
      ├─ Same options everywhere?
      │   ├─ Yes → Single project context
      │   └─ No → Multiple contexts with different options
      └─ Different issue types?
          └─ Configure issue type in context
```

### Screen Configuration Checklist

```
□ Create Screen: Minimal fields only
  ✓ Summary, Type, Priority, Description
  ✓ Story Points (for Stories)
  ✓ Assignee, Labels

□ Edit Screen: More fields
  ✓ All create fields
  ✓ Status, Resolution
  ✓ Time tracking
  ✓ Custom fields

□ View Screen: All fields
  ✓ All edit fields
  ✓ System fields (created, updated)
  ✓ Watchers, links
```

### Governance Quick Guide

```
Before creating a field:
1. Search existing fields
2. Check if reusable with contexts
3. Document purpose
4. Choose appropriate type
5. Plan for scale

After creating a field:
1. Set clear description
2. Add to appropriate screens
3. Configure validation
4. Document in registry
5. Communicate to users

Quarterly maintenance:
1. Review usage statistics
2. Identify unused fields
3. Merge duplicates
4. Update documentation
5. Optimize contexts
```

### Common JQL for Field Management

```sql
-- Find issues missing required field
"Story Points" IS EMPTY AND type = Story

-- Find issues with specific custom field value
"Customer Impact" = High

-- Issues updated via specific field
"Customer Impact" CHANGED DURING (startOfMonth(), now())

-- Check field population rate
"Custom Field Name" IS NOT EMPTY

-- Find all epics without stories
type = Epic AND issueFunction in linkedIssuesOf("type = Story") = 0
```

---

## Additional Resources

### Official Documentation

For more information, refer to these authoritative sources:

- [Jira custom fields: The complete guide 2025](https://blog.isostech.com/jira-custom-fields-the-complete-guide-2025)
- [The Ultimate Guide to Jira Custom Fields - Seibert Products](https://seibert.group/products/blog/jira-custom-fields-guide/)
- [Optimize your custom fields - Atlassian](https://confluence.atlassian.com/display/ENTERPRISE/Optimize+your+custom+fields)
- [Managing custom fields in Jira effectively - Atlassian](https://confluence.atlassian.com/display/ENTERPRISE/Managing+custom+fields+in+Jira+effectively)
- [Jira custom fields governance - Atlassian Success Central](https://success.atlassian.com/solution-resources/agile-and-devops-ado/agile-at-scale-practices/jira-custom-fields-governance)
- [Adding custom fields - Atlassian Documentation](https://confluence.atlassian.com/adminjiraserver/adding-custom-fields-1047552713.html)
- [Project screens, schemes and fields - Atlassian](https://confluence.atlassian.com/adminjiraserver/project-screens-schemes-and-fields-938847220.html)
- [Associate fields with screens in Jira Cloud - Atlassian Support](https://support.atlassian.com/jira/kb/associate-fields-with-screens-in-jira-cloud/)
- [Learn to use epics in Jira - Atlassian Agile](https://www.atlassian.com/agile/tutorials/epics)
- [Jira Software custom fields - eazyBI](https://docs.eazybi.com/eazybi/data-import/data-from-jira/jira-software-custom-fields)

### Internal Tools

```bash
# jira-fields skill location
.claude/skills/jira-fields/

# Available scripts
scripts/list_fields.py              # List custom fields
scripts/check_project_fields.py     # Check project field availability
scripts/create_field.py             # Create new custom field
scripts/configure_agile_fields.py   # Configure Agile fields

# Documentation
SKILL.md                            # Skill documentation
docs/BEST_PRACTICES.md             # This document
```

---

*Last updated: December 2025*
*Version: 1.0*
*Maintained by: JIRA Platform Team*
