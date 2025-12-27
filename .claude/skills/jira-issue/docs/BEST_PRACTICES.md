# JIRA Issue Management Best Practices

Comprehensive guide to creating, managing, and maintaining high-quality JIRA issues for effective project tracking and team collaboration.

---

## Table of Contents

1. [Writing Effective Summaries](#writing-effective-summaries)
2. [Writing Effective Descriptions](#writing-effective-descriptions)
3. [Choosing Issue Types](#choosing-issue-types)
4. [Setting Priorities Effectively](#setting-priorities-effectively)
5. [Using Labels](#using-labels)
6. [Using Components](#using-components)
7. [Custom Fields Best Practices](#custom-fields-best-practices)
8. [Issue Templates and Standardization](#issue-templates-and-standardization)
9. [Field Selection Strategy](#field-selection-strategy)
10. [Issue Lifecycle Management](#issue-lifecycle-management)
11. [Common Pitfalls](#common-pitfalls)
12. [Quick Reference Card](#quick-reference-card)

---

## Writing Effective Summaries

The summary is your headline - it should be crisp, clear, and capture the issue's essence at a glance.

### Core Principles

**Do:**
- Start with an action verb: "Add", "Fix", "Update", "Remove", "Implement", "Optimize"
- Be specific and concrete: "Fix login timeout on mobile Safari" not "Login broken"
- Include context when helpful: "Add dark mode toggle to settings page"
- Write from the user's behavioral perspective: "Grommet doesn't come off when flange is twisted"
- Keep it under 80 characters when possible
- Make it scannable: someone should understand the issue without opening it

**Don't:**
- Use vague terms: "Various fixes", "Updates", "Changes", "Work"
- Include implementation details: "Change CSS from flex to grid"
- Write novels: Summaries should be concise
- Use internal jargon unless universally understood
- Duplicate information that belongs in labels or components

### Summary Examples

| Bad | Good | Why Good is Better |
|-----|------|-------------------|
| Login | Fix session timeout on mobile devices | Specific problem and context |
| API stuff | Add rate limiting to REST endpoints | Clear action and scope |
| Bug | Fix null pointer in user registration | Identifies problem location |
| Performance | Optimize database queries for dashboard | Specific area and goal |
| Update code | Refactor authentication module for OAuth2 | Clear purpose and outcome |
| Feature request | Add CSV export to reports page | Specific feature and location |
| Issue with form | Fix form validation on checkout page | Precise location and issue |
| Need help | Implement password reset via email | Clear deliverable |

### Summary Patterns by Issue Type

**Bugs:**
```
Fix [specific problem] in [component/location]
Resolve [error message] when [action]
Correct [incorrect behavior] in [feature]
```
Examples:
- "Fix 404 error when accessing user profile"
- "Resolve crash when uploading large files"
- "Correct currency formatting in checkout"

**Tasks:**
```
[Verb] [object] for [purpose/context]
Update [component] to [desired state]
Configure [system] with [requirements]
```
Examples:
- "Configure CI pipeline for automated testing"
- "Update API documentation for v2.0 endpoints"
- "Create database indexes for performance"

**Stories:**
```
[User] can [action] [object]
Enable [capability] for [user type]
As [role], I want [feature] so that [value]
```
Examples:
- "Users can filter search results by date range"
- "Enable two-factor authentication for admin users"
- "As a manager, I want team performance reports"

**Epics:**
```
[High-level capability/feature area]
[User benefit] - [brief scope]
```
Examples:
- "User Authentication and Authorization System"
- "Mobile App - iOS Native Client"
- "Reporting Dashboard - Analytics and Insights"

---

## Writing Effective Descriptions

The description provides detailed context, requirements, and acceptance criteria. A well-written description eliminates ambiguity and enables efficient execution.

### Standard Description Template

Use this template for most issues:

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

### Bug Report Template

For bugs, use this specialized structure:

```markdown
## Summary
[Brief description of the bug]

## Environment
- **Browser/Device:** Chrome 120 on Windows 11
- **Version:** 2.3.4
- **User Role:** Standard user

## Steps to Reproduce
1. Navigate to login page
2. Enter valid credentials
3. Click "Login" button
4. Observe error message

## Expected Behavior
User should be logged in and redirected to dashboard

## Actual Behavior
Error message "Invalid credentials" appears even with correct password

## Impact
- **Severity:** High - blocks user login
- **Frequency:** 100% reproducible
- **Users Affected:** All mobile users

## Supporting Evidence
[Screenshots, error logs, network traces, video recordings]

## Workaround (if available)
[Temporary solution or alternative approach]
```

### User Story Template

For user stories, follow the standard format:

```markdown
## User Story
As a [type of user]
I want [goal/desire]
So that [benefit/value]

## Context
[Background information, business justification]

## Acceptance Criteria
- [ ] Given [precondition], when [action], then [expected result]
- [ ] Given [precondition], when [action], then [expected result]
- [ ] Given [precondition], when [action], then [expected result]

## UI/UX Notes
[Mockups, wireframes, design specifications]

## Technical Considerations
[API requirements, data model changes, integrations]

## Definition of Done
- [ ] Code implemented and reviewed
- [ ] Unit tests written and passing
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] Deployed to staging and verified
```

### Task Template

For technical tasks:

```markdown
## Objective
[What needs to be accomplished and why]

## Requirements
- Requirement 1
- Requirement 2
- Requirement 3

## Approach
[Proposed solution or implementation strategy]

## Success Criteria
- [ ] Deliverable 1 completed
- [ ] Deliverable 2 completed
- [ ] Validation performed

## Dependencies
[Other issues, external factors, or prerequisites]

## Resources
[Documentation links, API references, design files]
```

### Description Writing Guidelines

**Be Clear and Concise:**
- Use simple, straightforward language
- Avoid jargon unless necessary and well-defined
- Break complex information into sections
- Use bullet points and numbered lists for readability

**Provide Context:**
- Explain the "why" behind the work
- Include business impact and user value
- Reference related issues or epics
- Link to supporting documentation

**Be Specific:**
- Include exact error messages (in code blocks)
- Attach screenshots, logs, or recordings
- Specify versions, environments, and configurations
- Provide concrete examples

**Prioritize Information:**
- Put the most critical information first
- Use headings to organize sections logically
- Highlight blockers or urgent items
- Keep "nice-to-have" details separate

**Keep it Current:**
- Update descriptions as understanding evolves
- Move resolved questions from comments to description
- Archive outdated information
- Add clarifications when team members ask questions

---

## Choosing Issue Types

Different issue types serve different purposes. Choose the right type to ensure proper workflow, reporting, and team understanding.

### Issue Type Decision Matrix

| Type | Use When | Typical Duration | Estimated? | Parent Type | Example |
|------|----------|-----------------|-----------|-------------|---------|
| **Epic** | Feature spans multiple sprints, needs breakdown | 2-6 sprints | No | None | "User Authentication System" |
| **Story** | User-facing value, fits in one sprint | 1-5 days | Yes (points) | Epic | "Users can reset password via email" |
| **Task** | Technical work, enabler, no direct user value | 0.5-3 days | Yes (points) | Epic/None | "Configure Redis cache for sessions" |
| **Bug** | Something worked before, now broken | 0.5-2 days | Optional | Epic/None | "Login fails with special characters" |
| **Subtask** | Breaking down a story/task into smaller pieces | 2-8 hours | Optional (hours) | Story/Task/Bug | "Write unit tests for password validation" |
| **Improvement** | Enhance existing feature, not broken | 1-3 days | Yes (points) | Epic/None | "Add keyboard shortcuts to editor" |
| **Spike** | Research or investigation, outcome unknown | 0.5-2 days | Yes (time-boxed) | Epic/None | "Evaluate authentication libraries" |

### Epic Guidelines

**When to Create an Epic:**
- Feature requires 2+ sprints to complete
- Work involves multiple teams or components
- Initiative has distinct phases or milestones
- You need to track progress across related stories

**When NOT to Create an Epic:**
- Work fits comfortably in one sprint (use Story instead)
- Too broad or vague (break into smaller epics)
- No related stories (just create a large Story)

**Epic Lifecycle:**
1. **Draft** - Initial idea, rough scope
2. **Refined** - User stories identified, acceptance criteria defined
3. **Ready** - Stories estimated, prioritized, dependencies mapped
4. **In Progress** - Stories being worked in sprints
5. **Done** - All stories complete, value delivered

**Epic Sizing:**
- Target: 2-4 sprints to complete
- Maximum: 6 sprints (consider splitting if larger)
- Minimum: If less than 2 sprints, might just be a Story

### Story vs Task

**Use Story When:**
- Delivering user-facing functionality
- Following "As a [user], I want [feature], so that [benefit]" pattern
- Customer can see/experience the result
- Provides direct business value

**Use Task When:**
- Technical enabler work (infrastructure, tooling)
- Internal improvements (refactoring, optimization)
- No direct user-facing changes
- Supporting work for stories (technical debt, setup)

**Examples:**

| Scenario | Type | Rationale |
|----------|------|-----------|
| Add login button to homepage | Story | User-facing feature |
| Setup OAuth server configuration | Task | Technical enabler |
| Display user profile picture | Story | User can see the result |
| Optimize database query performance | Task | Internal improvement |
| Enable users to export CSV | Story | User-facing capability |
| Migrate database to PostgreSQL | Task | Technical work, no visible change |

### Bug Guidelines

**When to Create a Bug:**
- Feature worked correctly before
- Current behavior deviates from expected behavior
- Regression from previous release
- Production issue affecting users

**When NOT to Create a Bug:**
- Feature never worked (create Story or Task)
- Enhancement request (create Story or Improvement)
- Question or support request (use different channel)

**Bug Severity Levels:**

| Severity | Definition | Response Time | Example |
|----------|-----------|---------------|---------|
| **Critical** | Complete system failure, data loss, security breach | Immediate | "Database corruption on save" |
| **High** | Core feature broken, large user impact, no workaround | Same day | "Cannot complete checkout" |
| **Medium** | Feature broken, moderate impact, workaround exists | 1-3 days | "Filter doesn't work on mobile" |
| **Low** | Minor issue, cosmetic problem, minimal impact | Next sprint | "Button alignment off by 2px" |

---

## Setting Priorities Effectively

Priority indicates the order in which issues should be addressed. Use priorities consistently across your team.

### Priority Definitions

| Priority | When to Use | Response Expectation | Example Scenarios |
|----------|-------------|---------------------|-------------------|
| **Highest** | Emergency, complete blocker, severe impact | Drop everything, fix immediately | Production down, data loss, security breach |
| **High** | Critical for release, major feature broken | Address within 24 hours | Key feature not working, release blocker |
| **Medium** | Normal priority, scheduled work | Complete in current sprint | Planned features, standard bugs |
| **Low** | Nice to have, minor issue | Backlog, future sprint | Small improvements, cosmetic issues |
| **Lowest** | Future consideration, wishlist | Someday/maybe | Feature requests, minor enhancements |

### Priority Decision Framework

**Ask These Questions:**

1. **Impact:** How many users are affected?
   - All users → Higher priority
   - Subset of users → Medium priority
   - Edge case → Lower priority

2. **Severity:** What's the consequence?
   - Blocks critical work → Highest
   - Degrades experience → High/Medium
   - Minor inconvenience → Low/Lowest

3. **Urgency:** What's the timeline?
   - Must fix now → Highest
   - Needed for release → High
   - Can wait → Medium/Low

4. **Workaround:** Is there an alternative?
   - No workaround → Higher priority
   - Difficult workaround → Medium priority
   - Easy workaround → Lower priority

### Priority vs Severity (for Bugs)

Don't confuse priority with severity:

| Severity | Priority | Example |
|----------|----------|---------|
| High | Highest | Login broken in production |
| High | Low | Misspelling on rarely-visited page |
| Low | Highest | UI bug affects demo to major client |
| Low | Low | Cosmetic issue on deprecated feature |

**Remember:** Priority = Impact × Urgency

### Common Priority Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Everything is Highest | Defeats purpose of priorities | Reserve Highest for true emergencies |
| Never use Highest | Real emergencies get buried | Use Highest when truly critical |
| Priority drift | Issues sit without re-evaluation | Review priorities weekly in backlog grooming |
| Personal priorities | Individual preferences override team needs | Use objective criteria for priority |

---

## Using Labels

Labels are flexible tags for categorizing issues across projects and components. Use them for cross-cutting concerns and quick filtering.

### Label Best Practices

**Good Label Categories:**

1. **Domain/Technical Area:**
   - `security`, `performance`, `accessibility`, `compliance`
   - `database`, `api`, `frontend`, `backend`
   - `mobile`, `web`, `desktop`

2. **Priority Indicators:**
   - `quick-win` - Easy, high-value work
   - `tech-debt` - Technical debt items
   - `p0-critical` - Absolute highest priority
   - `blocked-external` - Waiting on third party

3. **Team/Ownership:**
   - `team-platform`, `team-mobile`, `team-backend`
   - `needs-design`, `needs-security-review`, `needs-approval`
   - `community-contribution`, `good-first-issue`

4. **Status Qualifiers:**
   - `needs-refinement` - Requires more details
   - `spike` - Research/investigation
   - `waiting-for-customer` - Pending external input
   - `ready-for-dev` - Fully specified and ready

5. **Release/Milestone:**
   - `v2.0`, `beta`, `mvp`
   - `Q1-2025`, `winter-release`

6. **Customer/Business:**
   - `customer-request`, `enterprise-feature`
   - `revenue-impact`, `competitive-parity`

### Label Naming Conventions

**Do:**
- Use lowercase with hyphens: `tech-debt`, `needs-review`
- Be consistent: `team-mobile` not `mobile-team`
- Use clear, descriptive names: `security` not `sec`
- Create a label taxonomy document
- Limit to 3-5 labels per issue

**Don't:**
- Use spaces (they create separate labels)
- Duplicate existing fields: `bug` (use issue type), `high-priority` (use priority field)
- Create user-specific labels: `john-to-review` (use assignee/watchers)
- Use dates: `2025-01-15` (use due date or sprint)
- Make labels too specific: `fix-button-on-login-page` (too granular)

### Label Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Alternative |
|--------------|--------------|-------------|
| Status labels: `in-progress`, `done` | Duplicates workflow status | Use workflow states |
| Issue type labels: `bug-label`, `task-label` | Duplicates issue type field | Use issue type |
| Assignment labels: `assigned-to-john` | Duplicates assignee field | Use assignee field |
| Component labels: `backend-label` | Duplicates components | Use components field |
| Priority labels: `high-priority` | Duplicates priority field | Use priority field |
| One-off labels: `discussed-tuesday` | No reusability | Use comments instead |

### Labels vs Components

| Use Labels For | Use Components For |
|----------------|-------------------|
| Cross-project categorization | Project-specific subsections |
| Temporary classifications | Permanent structural divisions |
| Flexible, ad-hoc grouping | Organized team ownership |
| Multiple overlapping categories | Single primary area assignment |
| Quick personal filtering | Formal reporting and metrics |

**Example:**
- Component: `payment-gateway` (structural area of codebase)
- Labels: `security`, `pci-compliance`, `tech-debt` (cross-cutting concerns)

---

## Using Components

Components represent architectural areas or structural divisions within a project. They're more formal and structured than labels.

### When to Use Components

**Components are ideal for:**
- Architectural modules: `api`, `frontend`, `backend`, `database`
- Product areas: `auth`, `payments`, `notifications`, `reporting`
- Platform divisions: `ios`, `android`, `web`, `desktop`
- Team ownership: `team-platform-owned`, `team-mobile-owned`
- Service boundaries: `user-service`, `order-service`, `inventory-service`

### Component Benefits

1. **Auto-Assignment:** Assign component leads automatically
2. **Filtered Reporting:** Generate component-specific reports
3. **Bug Tracking:** Track defect rates by area
4. **Team Boards:** Create boards filtered by component
5. **Release Planning:** Plan releases by component readiness
6. **Performance Metrics:** Measure velocity per component

### Component Organization Patterns

**By Architecture:**
```
- frontend
  - ui-components
  - state-management
- backend
  - api-server
  - background-jobs
- database
- infrastructure
```

**By Feature:**
```
- user-management
- billing
- reporting
- integrations
- admin-panel
```

**By Platform:**
```
- ios-app
- android-app
- web-app
- api
- shared-components
```

### Component Guidelines

**Do:**
- Keep components stable (don't rename frequently)
- Assign component leads for ownership
- Use components for reporting and dashboards
- Limit to 1-2 components per issue
- Document component purpose and scope

**Don't:**
- Create too many components (5-15 is ideal per project)
- Use components for temporary categorization (use labels)
- Overlap component boundaries excessively
- Create components without team buy-in
- Use components as status indicators

### Component Lead Assignment

Configure components to auto-assign leads:

| Component | Lead | Auto-Assign |
|-----------|------|-------------|
| frontend | jane@example.com | Yes |
| backend | john@example.com | Yes |
| database | db-team@example.com | No (multiple owners) |
| api | api-team@example.com | Yes |

---

## Custom Fields Best Practices

Custom fields extend JIRA's data model. Use them judiciously to avoid performance issues and complexity.

### Before Creating a Custom Field

**Ask These Questions:**

1. **Can I use a standard field?** Check if Summary, Description, Labels, or Components can serve the purpose.

2. **Will I query this data?** If not needed for searching or reporting, add to description instead.

3. **Is it truly custom?** Many "custom" needs are actually standard fields used differently.

4. **Is it project-specific or global?** Limit scope to avoid performance impact.

5. **Will this be used long-term?** Temporary needs don't justify custom fields.

### Custom Field Alternatives

| Need | Instead of Custom Field | Use This |
|------|------------------------|----------|
| Categorization | `Category` custom field | Components or Labels |
| Team assignment | `Team` custom field | Components with component leads |
| Status qualifier | `Status detail` custom field | Labels like `waiting-customer` |
| Free-form notes | `Notes` custom field | Comments or Description |
| Due date tracking | `Target date` custom field | Due Date (standard field) |
| Approval status | `Approved` custom field | Workflow status or Approvals feature |

### Custom Field Management

**Naming Conventions:**
- Use generic, reusable names: `Objective` not `Marketing Objective`
- Be descriptive: `Customer Impact Level` not `Impact`
- Include units where relevant: `Effort (hours)` not `Effort`
- Avoid abbreviations: `Deployment Environment` not `Dep Env`

**Context Configuration:**
- Use project-specific contexts when possible (better performance)
- Global contexts impact all projects (use sparingly)
- Configure per issue type when relevant

**Field Descriptions:**
- Write clear descriptions explaining purpose
- Include examples of valid values
- Document which projects use the field
- Note any special formatting requirements

### Custom Field Types Guide

| Field Type | Use For | Example |
|------------|---------|---------|
| **Text (single line)** | Short identifiers, codes | `PR Number`, `Build ID` |
| **Text (multi-line)** | Longer text, descriptions | `Root Cause Analysis` |
| **Number** | Numeric values, counts | `Lines of Code`, `Defect Count` |
| **Date** | Dates without time | `Target Release Date` |
| **DateTime** | Dates with time | `Deployment Timestamp` |
| **Select (single)** | One choice from list | `Deployment Environment` |
| **Select (multi)** | Multiple choices | `Affected Browsers` |
| **Checkbox** | Multiple selections | `Platforms Tested` |
| **Radio** | One choice, inline display | `Risk Level` |
| **User Picker (single)** | Assign person | `Technical Reviewer` |
| **User Picker (multi)** | Assign multiple people | `Stakeholders` |
| **URL** | Web links | `Design Mockup URL` |
| **Labels** | Tags (use standard Labels instead) | Use built-in Labels |

### Custom Field Performance Tips

1. **Limit total custom fields:** 1000+ fields can impact performance
2. **Use project/issue type contexts:** Better than global
3. **Regular audits:** Remove unused fields quarterly
4. **Avoid duplicate fields:** Consolidate similar fields
5. **Index strategically:** Only index frequently searched fields

### Custom Field Audit Checklist

Quarterly review:
- [ ] List all custom fields and their usage statistics
- [ ] Identify fields with < 5% population rate
- [ ] Find duplicate or overlapping fields
- [ ] Check for fields not used in any filters/reports
- [ ] Remove or consolidate unnecessary fields
- [ ] Update field descriptions and documentation
- [ ] Verify context configurations are optimal

---

## Issue Templates and Standardization

Templates ensure consistency, save time, and reduce errors. Standardize common workflows with reusable templates.

### Why Use Templates?

**Benefits:**
- **Consistency:** All issues follow the same structure
- **Completeness:** Required information is never forgotten
- **Efficiency:** No need to write from scratch each time
- **Quality:** Built-in best practices
- **Onboarding:** New team members have clear guidance
- **Reporting:** Structured data enables better analytics

### Template Strategy

**Create Templates For:**

1. **Bug Reports:** Ensure all bugs have reproducible steps, environment, expected vs actual behavior
2. **User Stories:** Standard "As a... I want... so that..." format with acceptance criteria
3. **Tasks:** Clear objectives, requirements, and success criteria
4. **Epics:** High-level goals, related stories, success metrics
5. **Spikes:** Investigation scope, time-box, success criteria
6. **Incidents:** Severity, impact, timeline, root cause analysis

### Bug Report Template Example

```markdown
## Environment
- **Browser/Device:**
- **Version:**
- **User Role:**

## Steps to Reproduce
1.
2.
3.

## Expected Behavior


## Actual Behavior


## Impact
- **Severity:** [Critical/High/Medium/Low]
- **Frequency:** [Always/Often/Sometimes/Rare]
- **Users Affected:**

## Screenshots/Logs
[Attach evidence]

## Workaround
[If available]
```

### User Story Template Example

```markdown
## User Story
As a [type of user]
I want [goal/desire]
So that [benefit/value]

## Acceptance Criteria
- [ ] Given [precondition], when [action], then [result]
- [ ] Given [precondition], when [action], then [result]
- [ ] Given [precondition], when [action], then [result]

## UI/UX Notes


## Technical Considerations


## Definition of Done
- [ ] Code implemented and reviewed
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] Deployed to staging
```

### Task Template Example

```markdown
## Objective
[What needs to be accomplished and why]

## Requirements
-
-
-

## Approach
[Proposed solution or implementation strategy]

## Success Criteria
- [ ]
- [ ]
- [ ]

## Dependencies
[Related issues or prerequisites]
```

### Epic Template Example

```markdown
## Vision
[High-level goal and business value]

## Scope
**In Scope:**
-
-

**Out of Scope:**
-
-

## Success Metrics
-
-

## User Stories
[Link to related stories]

## Timeline
**Target Start:**
**Target Completion:**

## Dependencies and Risks
```

### Template Implementation

**Native JIRA (Cloud):**
- Use Description Templates feature
- Configure per project and issue type
- Add default values for fields

**Using Scripts:**
- Create template JSON files in `.claude/skills/jira-issue/assets/templates/`
- Use `create_issue.py --template bug|task|story`
- Customize templates for your organization

**Automation:**
- Auto-apply templates based on issue type
- Pre-fill default values (priority, components)
- Trigger template on specific workflows

### Template Maintenance

**Best Practices:**
- Review templates quarterly
- Update based on team feedback
- Version templates for tracking changes
- Document template usage guidelines
- Train team on available templates
- Monitor template adoption rates

---

## Field Selection Strategy

Choose the right field for each piece of information to maintain clarity and enable effective searching.

### Field Selection Decision Tree

```
Is this information...

┌─ Identifying the issue?
│  └─ Use: Summary
│
├─ Explaining details?
│  └─ Use: Description
│
├─ Categorizing by area?
│  ├─ Structural/architectural → Components
│  └─ Flexible/cross-cutting → Labels
│
├─ Indicating importance?
│  └─ Use: Priority
│
├─ Tracking people?
│  ├─ Who does the work → Assignee
│  ├─ Who reported it → Reporter (auto)
│  └─ Who cares about updates → Watchers
│
├─ Organizing work?
│  ├─ Epic-level grouping → Epic Link
│  ├─ Sprint planning → Sprint
│  └─ Release planning → Fix Version
│
├─ Time-related?
│  ├─ When due → Due Date
│  ├─ How much effort → Original Estimate
│  └─ Work logged → Time Tracking
│
└─ Truly unique to your process?
   └─ Consider: Custom Field (last resort)
```

### Field Validation Rules

| Field | Required? | Format | Max Length | Validation |
|-------|-----------|--------|------------|------------|
| Summary | Yes | Text | 255 chars | Not empty |
| Description | Recommended | ADF/Markdown | Unlimited | Valid ADF |
| Issue Type | Yes | Predefined | N/A | Valid for project |
| Priority | No | Predefined | N/A | Valid priority |
| Assignee | No | User | N/A | Valid user account |
| Labels | No | Array of strings | N/A | No spaces, alphanumeric |
| Components | No | Array of objects | N/A | Valid for project |

### Field Interdependencies

Some fields affect others:

| If You Set... | Then You Should... | Because... |
|---------------|-------------------|------------|
| Epic Link | Set Story Points | Epics track points rolled up from stories |
| Sprint | Set Assignee | Sprints require assigned work |
| Original Estimate | Set Remaining Estimate | Time tracking needs both values |
| Fix Version | Set Priority | Release planning needs prioritization |
| Components | Set Assignee | Components often have default owners |

---

## Issue Lifecycle Management

Issues evolve over time. Manage them effectively throughout their lifecycle.

### Issue Creation Checklist

**Before Creating:**
- [ ] Search for existing issues (avoid duplicates)
- [ ] Determine correct issue type
- [ ] Identify appropriate project
- [ ] Gather required information

**During Creation:**
- [ ] Write clear, specific summary
- [ ] Add comprehensive description
- [ ] Set appropriate priority
- [ ] Add relevant labels and components
- [ ] Link to related issues
- [ ] Assign to appropriate person (if known)
- [ ] Set epic/sprint if applicable

**After Creation:**
- [ ] Verify all required fields populated
- [ ] Add watchers who should be notified
- [ ] Create subtasks if needed
- [ ] Notify relevant stakeholders

### Issue Update Best Practices

**When to Update:**
- Status changes (use transitions, not manual updates)
- New information discovered
- Scope changes
- Priority shifts
- Assignment changes
- Resolution approaches change

**How to Update:**
- Add comments explaining the change
- Update description to reflect current understanding
- Move obsolete information to comments
- Maintain change history
- Notify affected team members

**What NOT to Update:**
- Don't change issue type after creation (create new issue instead)
- Don't remove historical comments
- Don't overwrite original requirements (track changes)
- Don't update without explanation

### Issue Maintenance

**Weekly Grooming:**
- Review unassigned issues
- Update stale priorities
- Add missing information
- Link related issues
- Archive outdated issues

**Sprint Boundaries:**
- Close completed issues
- Move incomplete work to next sprint
- Update estimates based on actual
- Retrospect on issue quality

### Issue Deletion Guidelines

**Delete Only When:**
- True duplicate (link to original first)
- Created in error
- Spam or invalid
- Test data

**Don't Delete:**
- Resolved/closed issues (they provide history)
- Issues with logged time
- Issues linked to other work
- Issues referenced in commits/PRs

---

## Common Pitfalls

Avoid these frequent mistakes in issue management.

### Anti-Patterns

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Mega-issues** | Tracking multiple unrelated things in one issue | Split into separate, focused issues |
| **Vague summaries** | "Fix bug" or "Update code" | Be specific: "Fix login timeout on Safari" |
| **Missing acceptance criteria** | Team doesn't know when it's done | Add clear, testable criteria |
| **Over-detailed summaries** | Summary is 3 sentences long | Keep summary concise, details in description |
| **Label chaos** | 50+ labels, inconsistent naming | Create label taxonomy, enforce standards |
| **Duplicate information** | Same info in summary, description, comments | Each field has a purpose, use appropriately |
| **Zombie issues** | Open for 6+ months, no activity | Regular grooming, close or archive stale issues |
| **Meeting issues** | "Attended standup" as an issue | Don't track meetings as issues |
| **Missing links** | Related work not connected | Link related issues, epics, dependencies |
| **Priority inflation** | Everything is Highest | Use priorities objectively, reserve Highest for emergencies |
| **Incomplete bugs** | No repro steps or environment | Use bug template to ensure completeness |
| **Custom field sprawl** | 100+ custom fields | Audit regularly, use labels/components instead |

### Red Flags

**Look Out For:**

**In Issue Content:**
- Summary doesn't explain the issue
- No acceptance criteria
- Missing priority or wrong priority
- No assignee and past due
- Blocked but no explanation why

**In Backlog:**
- Issues older than 6 months with no activity
- No estimate on issues in next sprint
- Missing epic link on stories
- Duplicate issues

**In Sprint:**
- Same issue "In Progress" for 5+ days
- No comments for 3+ days on active issue
- Blocked issues with no action plan
- Scope creep (issue keeps expanding)

**In Process:**
- Team creates issues without templates
- Inconsistent labeling across project
- Component assignment ignored
- Custom fields not populated
- Time tracking not used

### Quality Metrics

**Measure Issue Quality:**

| Metric | Target | Indicates |
|--------|--------|-----------|
| Issues with acceptance criteria | 90%+ | Clarity of requirements |
| Average time to first comment | < 24 hours | Team engagement |
| Issues closed as duplicate | < 5% | Search before create |
| Issues with priority set | 100% | Proper prioritization |
| Description length | > 100 chars | Adequate detail |
| Labels per issue | 1-5 | Appropriate categorization |
| Linked issues | 30%+ | Relationship tracking |

---

## Quick Reference Card

### Issue Creation Quick Checklist

```
☐ Descriptive summary (< 80 chars, starts with verb)
☐ Detailed description (problem, context, acceptance criteria)
☐ Correct issue type (Epic/Story/Task/Bug)
☐ Appropriate priority (Highest/High/Medium/Low/Lowest)
☐ Relevant labels (1-5, consistent naming)
☐ Component(s) if applicable
☐ Epic link if part of larger initiative
☐ Assignee if known
☐ Linked to related issues
☐ Watchers added
```

### Field Quick Reference

| Field | When to Use | Example |
|-------|-------------|---------|
| **Summary** | Always | "Fix login timeout on mobile Safari" |
| **Description** | Always | "## Problem\nUsers unable to login..." |
| **Issue Type** | Always | Bug, Task, Story, Epic |
| **Priority** | Always | High (core feature broken) |
| **Assignee** | When known | john@example.com |
| **Labels** | Categorization | security, tech-debt, quick-win |
| **Components** | Area of work | frontend, backend, api |
| **Epic Link** | Part of epic | PROJ-100 |
| **Sprint** | Sprint planning | Sprint 42 |
| **Story Points** | Stories/Tasks | 5 |
| **Due Date** | Hard deadline | 2025-12-31 |
| **Fix Version** | Release planning | v2.0 |

### Summary Patterns Cheat Sheet

```
Bugs:       "Fix [problem] in [location]"
Tasks:      "[Verb] [object] for [purpose]"
Stories:    "Users can [action] [object]"
Epics:      "[High-level capability]"
```

### Priority Quick Decision

```
Highest  → System down, data loss, security breach
High     → Core feature broken, release blocker
Medium   → Standard work, planned features
Low      → Minor issues, small improvements
Lowest   → Future wishlist items
```

### Label vs Component vs Custom Field

```
Labels:       Cross-cutting, flexible, multiple per issue
              Example: security, tech-debt, needs-review

Components:   Structural areas, team ownership, reporting
              Example: api, frontend, payment-service

Custom Field: Truly unique data, need to query/report
              Example: Customer Impact Score, SLA Category
```

### Common CLI Commands

```bash
# Create a bug
python create_issue.py --project PROJ --type Bug \
  --summary "Fix login timeout" --priority High

# Create with template
python create_issue.py --project PROJ --template bug

# Get issue details
python get_issue.py PROJ-123 --detailed

# Update priority
python update_issue.py PROJ-123 --priority Critical

# Add to epic
python create_issue.py --project PROJ --type Story \
  --summary "User story" --epic PROJ-100 --story-points 5
```

---

## Additional Resources

### Official Documentation
- [JIRA REST API v3](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Atlassian Document Format](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)
- [JIRA Best Practices](https://www.atlassian.com/software/jira/guides/getting-started/best-practices)

### Referenced Best Practices
- [How to Standardize Jira Issue Descriptions with Templates](https://narva.net/blog/jira-description-template-how-to-standardize-issue-descriptions-for-better-workflow)
- [The Ultimate Guide to Efficiency: Jira Best Practices in 2025](https://unito.io/blog/jira-efficiency-best-practices/)
- [Use cases for Components, Labels & Custom fields in Jira](https://www.devsamurai.com/en/use-cases-for-components-labels-and-custom-fields-in-jira/)
- [Jira custom fields: The complete guide 2025](https://blog.isostech.com/jira-custom-fields-the-complete-guide-2025)
- [Issue Templates in Jira: Guide 2025](https://community.atlassian.com/forums/App-Central-articles/Issue-Templates-in-Jira-Guide-2025/ba-p/3034243)
- [Best Practices for Creating a Jira Issue With Templates](https://stiltsoft.com/blog/best-practices-for-creating-a-jira-issue-with-templates/)
- [Labels Component vs. Custom Field: Which One Is Best for Your Company?](https://www.atlassway.com/labels-component-or-custom-field-which-one-is-best-for-your-company/)

### Related Skills
- **jira-lifecycle**: Workflow transitions and status management
- **jira-search**: JQL queries and advanced search
- **jira-collaborate**: Comments, attachments, watchers
- **jira-agile**: Sprint planning, epics, story points
- **jira-relationships**: Issue linking and dependencies

---

*Last updated: December 2025*
