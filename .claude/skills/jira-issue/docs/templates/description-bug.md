# Bug Report Template

Use this template for reporting defects, regressions, and unexpected behavior.

## Template

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

## Example

```markdown
## Summary
Login fails with session timeout error on Safari mobile

## Environment
- **Browser/Device:** Safari 17.2 on iOS 17.1, iPhone 14
- **Version:** v2.5.1 production
- **User Role:** Standard user

## Steps to Reproduce
1. Open the app in Safari on iPhone
2. Enter valid username and password
3. Tap "Sign In" button
4. Wait for response

## Expected Behavior
User is authenticated and redirected to the main dashboard within 3 seconds.

## Actual Behavior
After 10 seconds, error message "Session Timeout: Please try again" appears.
The issue occurs consistently on Safari mobile but works on Safari desktop.

## Impact
- **Severity:** Critical - prevents mobile user login
- **Frequency:** 100% reproducible on iOS Safari
- **Users Affected:** All iOS users (~35% of user base)

## Supporting Evidence
- Console log attached showing 408 timeout from /api/auth/login
- Network trace shows request taking 12 seconds to fail
- Video recording: [link to video]

## Workaround
Users can log in via Chrome on iOS, then switch back to Safari (session persists).
```

## Severity Guide

| Severity | Definition | Examples |
|----------|------------|----------|
| Critical | System unusable, data loss, security issue | Database corruption, authentication bypass |
| High | Core feature broken, major impact, no workaround | Checkout fails, API completely down |
| Medium | Feature broken, workaround exists | Filter not working, incorrect calculation |
| Low | Minor issue, cosmetic, minimal impact | Alignment off, typo in message |

## Key Sections Explained

| Section | Purpose | Required |
|---------|---------|----------|
| Summary | One-line description | Yes |
| Environment | Where the bug occurs | Yes |
| Steps to Reproduce | How to trigger the bug | Yes |
| Expected Behavior | What should happen | Yes |
| Actual Behavior | What actually happens | Yes |
| Impact | Severity and scope | Yes |
| Supporting Evidence | Proof of the bug | Recommended |
| Workaround | Temporary solution | If available |
