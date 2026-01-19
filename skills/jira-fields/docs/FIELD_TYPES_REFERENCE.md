# JIRA Field Types Reference

Complete reference for JIRA custom field types, their use cases, and selection guidance.

---

## Quick Selection Guide

| Need | Use This Type |
|------|---------------|
| Short text (255 chars) | `text` |
| Long text (unlimited) | `textarea` |
| Numbers/calculations | `number` |
| Date only | `date` |
| Date and time | `datetime` |
| Single choice | `select` or `radio` |
| Multiple choices | `multiselect` or `checkbox` |
| User reference | `user` |
| Web link | `url` |
| Free-form tags | `labels` |

---

## Standard Field Types

### Text Field (`text`)

**Storage:** String (255 characters max)
**Searchable:** Yes

**Use when:**
- Free-form input is required
- Values are unique per issue
- No data validation needed

**Examples:**
- Product name
- External ticket number
- Customer reference ID

**Create command:**
```bash
python create_field.py --name "External ID" --type text
```

---

### Text Area (`textarea`)

**Storage:** Text (unlimited)
**Searchable:** Yes

**Use when:**
- Multi-line content needed
- Detailed descriptions required
- No character limit constraint

**Examples:**
- Technical notes
- Requirements
- Release notes

**Create command:**
```bash
python create_field.py --name "Technical Notes" --type textarea
```

---

### Number Field (`number`)

**Storage:** Float
**Searchable:** Yes

**Use when:**
- Performing calculations
- Need range queries
- Sorting numerically matters

**Examples:**
- Story points (1, 2, 3, 5, 8, 13)
- Budget amount
- Effort estimate in hours

**Create command:**
```bash
python create_field.py --name "Effort Hours" --type number
```

---

### Date Picker (`date`)

**Storage:** Date
**Searchable:** Yes

**Use when:**
- Tracking deadlines
- Date-only is sufficient
- Need time-based queries

**Examples:**
- Target date
- Review deadline
- Release date

**Create command:**
```bash
python create_field.py --name "Target Date" --type date
```

---

### Date Time Picker (`datetime`)

**Storage:** DateTime
**Searchable:** Yes

**Use when:**
- Specific time matters
- Scheduling with time zones
- Audit timestamps needed

**Examples:**
- Scheduled deployment
- Meeting time
- Incident start time

**Create command:**
```bash
python create_field.py --name "Deployment Time" --type datetime
```

---

### Select List (`select`)

**Storage:** String
**Searchable:** Yes

**Use when:**
- Values are from a known set
- Need consistency across issues
- Want to prevent typos

**Examples:**
- Severity (Critical, High, Medium, Low)
- Environment (Production, Staging, Development)
- Platform (iOS, Android, Web)

**Create command:**
```bash
python create_field.py --name "Severity" --type select
```

**Note:** Configure options in JIRA admin after creation.

---

### Multi-Select (`multiselect`)

**Storage:** Array
**Searchable:** Yes

**Use when:**
- Multiple values allowed
- Options are predefined
- Reporting by category needed

**Examples:**
- Affected components
- Target platforms
- Required skills

**Create command:**
```bash
python create_field.py --name "Target Platforms" --type multiselect
```

---

### Checkboxes (`checkbox`)

**Storage:** Array
**Searchable:** Yes

**Use when:**
- Multiple selections displayed inline
- Options are few (2-6)
- Toggle-style selection preferred

**Examples:**
- Features included
- Compliance flags
- Test types required

**Create command:**
```bash
python create_field.py --name "Compliance" --type checkbox
```

---

### Radio Buttons (`radio`)

**Storage:** String
**Searchable:** Yes

**Use when:**
- Single selection displayed inline
- Options are few (2-4)
- Clear visual distinction needed

**Examples:**
- Approval status (Approved, Rejected, Pending)
- Yes/No choice
- T-shirt size (S, M, L, XL)

**Create command:**
```bash
python create_field.py --name "Approval" --type radio
```

---

### URL Field (`url`)

**Storage:** String
**Searchable:** Yes

**Use when:**
- Storing web links
- Links should be clickable
- External references needed

**Examples:**
- Documentation link
- Design file URL
- External ticket reference

**Create command:**
```bash
python create_field.py --name "Documentation" --type url
```

---

### User Picker (`user`)

**Storage:** User object
**Searchable:** Yes

**Use when:**
- Assigning responsibility
- Tracking ownership
- User-based filtering needed

**Examples:**
- Approver
- Technical reviewer
- Product owner

**Create command:**
```bash
python create_field.py --name "Approver" --type user
```

---

### Labels (`labels`)

**Storage:** String array
**Searchable:** Yes

**Use when:**
- Free-form tagging needed
- Values evolve over time
- Autocomplete from existing values

**Examples:**
- Technology tags (react, typescript)
- Category labels (backend, api)
- Feature tags

**Create command:**
```bash
python create_field.py --name "Tech Stack" --type labels
```

---

## Agile-Specific Fields

For Agile fields (Sprint, Story Points, Epic Link), see:
- [Agile Field IDs Reference](../assets/agile-field-ids.md)
- [Agile Field Guide](AGILE_FIELD_GUIDE.md)

---

## Field Type Decision Tree

```
Is the value text?
  |
  +-- Yes, short (< 255 chars)? --> text
  |
  +-- Yes, longer? --> textarea
  |
  +-- No, is it a number? --> number
  |
  +-- No, is it a date?
       |
       +-- Date only? --> date
       +-- Date + time? --> datetime
  |
  +-- No, is it a choice from options?
       |
       +-- Single choice?
       |    +-- Few options (2-4)? --> radio
       |    +-- Many options? --> select
       |
       +-- Multiple choices?
            +-- Few options (2-6)? --> checkbox
            +-- Many options? --> multiselect
  |
  +-- No, is it a user? --> user
  |
  +-- No, is it a URL? --> url
  |
  +-- No, is it free-form tags? --> labels
```

---

## Technical Reference

For Atlassian plugin identifiers used in API calls, see:
[Field Types Reference JSON](../assets/field-types-reference.json)

---

## Cross-References

- [Quick Start Guide](QUICK_START.md) - Get started fast
- [Best Practices](BEST_PRACTICES.md) - Design principles
- [Governance Guide](GOVERNANCE_GUIDE.md) - Field management
