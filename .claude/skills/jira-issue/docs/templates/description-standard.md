# Standard Description Template

Use this template for most issues when no specialized format is needed.

## Template

```markdown
## Problem/Goal
[What is the issue or what needs to be achieved? Be specific about the current state and desired state.]

## Context
[Why is this important? What's the business value or impact? Who is affected?]

## Acceptance Criteria
- [ ] Criterion 1: Specific, measurable outcome
- [ ] Criterion 2: Specific, measurable outcome
- [ ] Criterion 3: Specific, measurable outcome

## Technical Notes (optional)
[Implementation hints, constraints, dependencies, or architectural considerations]

## Additional Information (optional)
[Screenshots, logs, error messages, links to related documentation]
```

## Example

```markdown
## Problem/Goal
Users cannot export their monthly reports as PDF files. The export button is visible but produces no output when clicked.

## Context
This is a frequently used feature by enterprise customers. Currently blocked users must manually screenshot or use third-party tools, causing workflow delays.

## Acceptance Criteria
- [ ] PDF export button generates valid PDF document
- [ ] PDF includes all visible report data with correct formatting
- [ ] Export works for reports up to 1000 rows
- [ ] Loading indicator displays during generation

## Technical Notes
Consider using existing PDF generation library (jsPDF) already included in dependencies. May need async generation for large reports.

## Additional Information
Related to feature request PROJ-456. User feedback in support ticket #12345.
```

## When to Use

- General tasks and features
- Issues that don't fit specialized templates
- Quick documentation of work items
- Internal technical tasks

## Key Sections Explained

| Section | Purpose | Required |
|---------|---------|----------|
| Problem/Goal | Clear statement of what needs to change | Yes |
| Context | Business justification and impact | Yes |
| Acceptance Criteria | How we know it's done | Yes |
| Technical Notes | Implementation guidance | Optional |
| Additional Information | Supporting materials | Optional |
