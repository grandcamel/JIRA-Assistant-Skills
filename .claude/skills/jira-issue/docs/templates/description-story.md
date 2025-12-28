# User Story Template

Use this template for user-facing features that deliver direct value.

## Template

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

## Example

```markdown
## User Story
As a registered user
I want to reset my password via email
So that I can regain access to my account when I forget my password

## Context
Currently users must contact support for password resets, causing 2-day delays.
This feature will reduce support tickets by an estimated 40% and improve user satisfaction.

## Acceptance Criteria
- [ ] Given I am on the login page, when I click "Forgot Password", then I see an email input form
- [ ] Given I enter a valid registered email, when I submit, then I receive a reset link within 2 minutes
- [ ] Given I click the reset link within 24 hours, when I enter a new valid password, then my password is updated
- [ ] Given I click an expired or used reset link, when I try to reset, then I see an error message with option to request new link
- [ ] Given I enter an unregistered email, when I submit, then I see a generic "check your email" message (no account enumeration)

## UI/UX Notes
- See Figma mockup: [link]
- Password strength meter required
- Success message should include link back to login

## Technical Considerations
- Reset tokens expire after 24 hours
- Token stored hashed in database
- Rate limit: 3 reset requests per hour per email
- Use existing email service for delivery

## Definition of Done
- [ ] Code implemented and reviewed
- [ ] Unit tests for token generation/validation
- [ ] Integration tests for full reset flow
- [ ] Security review completed
- [ ] Documentation updated
- [ ] Deployed to staging and verified
```

## Gherkin Format Reference

Acceptance criteria can use Gherkin syntax for precision:

```gherkin
Given [precondition or initial context]
When [action or event]
Then [expected outcome]
And [additional outcome]
```

## Story vs Task Decision

| Use Story When | Use Task When |
|----------------|---------------|
| User-facing functionality | Technical enabler work |
| Customer sees the result | Internal improvements |
| Direct business value | No visible user change |
| "As a user, I want..." | "Configure/Setup/Migrate..." |

## INVEST Criteria

Good stories are:
- **I**ndependent - Can be developed separately
- **N**egotiable - Details can be discussed
- **V**aluable - Delivers user/business value
- **E**stimable - Team can size it
- **S**mall - Fits in one sprint
- **T**estable - Clear acceptance criteria
