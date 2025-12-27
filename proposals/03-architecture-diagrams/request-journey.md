# Request Journey Diagram

## Usage

Embed this sequence diagram in the README to show the step-by-step flow of a user request through the system.

## Mermaid Code - Bug Creation Example

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant C as Claude Code
    participant R as jira-assistant<br/>Router
    participant S as jira-issue<br/>Skill
    participant L as Shared Library
    participant A as JIRA REST API
    participant J as JIRA Cloud

    U->>C: "Create a high priority bug<br/>for login failing on mobile"

    Note over C: Understands intent,<br/>identifies JIRA task

    C->>R: Route request

    Note over R: Matches to jira-issue<br/>based on "create" + "bug"

    R->>S: create_issue.py<br/>--type Bug --priority High

    Note over S: Validates inputs,<br/>builds request payload

    S->>L: get_jira_client()
    L-->>S: Authenticated client

    S->>A: POST /rest/api/3/issue<br/>{type: Bug, priority: High, ...}

    A->>J: Create Issue
    J-->>A: {key: "PROJ-456", id: 10042}

    A-->>S: 201 Created + Issue Data

    Note over S: Formats response<br/>for display

    S-->>C: Success: PROJ-456 created

    C-->>U: Created PROJ-456:<br/>"Login failing on mobile"<br/>[High Priority Bug]
```

## Mermaid Code - Search and Transition Example

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant C as Claude Code
    participant R as jira-assistant<br/>Router
    participant S1 as jira-search
    participant S2 as jira-lifecycle
    participant L as Shared Library
    participant A as JIRA REST API

    U->>C: "Find my open bugs and<br/>close the one about login"

    Note over C: Multi-step task detected

    C->>R: Route: search query
    R->>S1: jql_search.py<br/>"assignee=currentUser() AND type=Bug"

    S1->>L: Execute JQL
    L->>A: POST /rest/api/3/search
    A-->>L: {issues: [{key: "PROJ-123", summary: "Login bug"}, ...]}
    L-->>S1: 3 issues found
    S1-->>C: Display results

    Note over C: Identifies PROJ-123<br/>matches "login"

    C->>R: Route: transition
    R->>S2: transition_issue.py PROJ-123<br/>--name "Done"

    S2->>L: Get transitions
    L->>A: GET /rest/api/3/issue/PROJ-123/transitions
    A-->>L: [{id: 31, name: "Done"}, ...]

    S2->>L: Execute transition
    L->>A: POST /rest/api/3/issue/PROJ-123/transitions<br/>{transition: {id: 31}}
    A-->>L: 204 No Content
    L-->>S2: Transition complete

    S2-->>C: PROJ-123 moved to Done
    C-->>U: Found 3 bugs. Closed PROJ-123<br/>"Login bug" - now Done
```

## Mermaid Code - Time Logging Example

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant C as Claude Code
    participant R as jira-assistant<br/>Router
    participant S as jira-time
    participant L as Shared Library
    participant A as JIRA REST API

    U->>C: "Log 2 hours on PROJ-789<br/>for code review today"

    C->>R: Route: time tracking

    Note over R: Matches "log time"<br/>to jira-time skill

    R->>S: log_work.py PROJ-789<br/>--time "2h" --comment "Code review"

    Note over S: Parses "2h" -> 7200 seconds

    S->>L: Create worklog
    L->>A: POST /rest/api/3/issue/PROJ-789/worklog<br/>{timeSpentSeconds: 7200, started: "2025-01-15T09:00:00", comment: {...}}

    A-->>L: 201 Created + Worklog ID
    L-->>S: Worklog 54321 created

    S-->>C: Logged 2h on PROJ-789
    C-->>U: Logged 2 hours on PROJ-789<br/>Comment: "Code review"<br/>Total time: 6h (was 4h)
```

## Sequence Diagram Elements

| Element | Purpose |
|---------|---------|
| User | Natural language request |
| Claude Code | AI intent understanding |
| Router | Skill selection based on keywords |
| Skill | Python script execution |
| Shared Library | HTTP client, config, validation |
| JIRA REST API | Atlassian API endpoints |
| JIRA Cloud | Data storage and processing |
