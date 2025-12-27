# Command to Result Flow Visualization

This Mermaid diagram demonstrates how natural language requests transform into JIRA actions and meaningful results.

## Primary Flow Diagram

```mermaid
flowchart LR
    subgraph Input["What You Say"]
        direction TB
        Q1["Show my high<br/>priority bugs"]
        Q2["Create a story for<br/>user login redesign"]
        Q3["What's blocking<br/>the release?"]
        Q4["Move PROJ-123<br/>to In Progress"]
        Q5["Log 3 hours on<br/>yesterday's work"]
    end

    subgraph Processing["What Happens"]
        direction TB
        P1["jira-search<br/>JQL: assignee=currentUser()<br/>AND type=Bug<br/>AND priority in (High, Highest)"]
        P2["jira-issue<br/>create_issue.py<br/>--type Story<br/>--summary 'User login redesign'"]
        P3["jira-relationships<br/>get_blockers.py<br/>Traverse dependency tree"]
        P4["jira-lifecycle<br/>transition_issue.py<br/>PROJ-123 'In Progress'"]
        P5["jira-time<br/>log_work.py PROJ-123<br/>--time 3h --date yesterday"]
    end

    subgraph Output["What You Get"]
        direction TB
        R1["7 bugs listed<br/>with key, summary,<br/>priority, status"]
        R2["PROJ-456 created<br/>Ready for refinement"]
        R3["3 blockers identified<br/>with resolution path"]
        R4["PROJ-123 updated<br/>Status: In Progress"]
        R5["3 hours logged<br/>Remaining: 5h"]
    end

    Q1 --> P1 --> R1
    Q2 --> P2 --> R2
    Q3 --> P3 --> R3
    Q4 --> P4 --> R4
    Q5 --> P5 --> R5

    style Input fill:#e3f2fd,stroke:#1976d2
    style Processing fill:#fff3e0,stroke:#f57c00
    style Output fill:#e8f5e9,stroke:#388e3c
```

## Compact Version (for README)

```mermaid
flowchart LR
    subgraph Say["You Say"]
        Q1["Show my bugs"]
        Q2["Create story"]
        Q3["What's blocking?"]
    end

    subgraph Do["Claude Does"]
        P1["jira-search<br/>JQL query"]
        P2["jira-issue<br/>create_issue.py"]
        P3["jira-relationships<br/>find blockers"]
    end

    subgraph Get["You Get"]
        R1["Bug list"]
        R2["PROJ-456"]
        R3["Blocker chain"]
    end

    Q1 --> P1 --> R1
    Q2 --> P2 --> R2
    Q3 --> P3 --> R3

    style Say fill:#e3f2fd,stroke:#1976d2
    style Do fill:#fff3e0,stroke:#f57c00
    style Get fill:#e8f5e9,stroke:#388e3c
```

## Extended Examples

### Developer Workflow

```mermaid
flowchart LR
    subgraph Morning["Morning Standup"]
        M1["What did I work on<br/>yesterday?"]
        M2["What's assigned to me<br/>this sprint?"]
    end

    subgraph Skills1["Skills Used"]
        S1["jira-search +<br/>jira-time"]
        S2["jira-search +<br/>jira-agile"]
    end

    subgraph Results1["Results"]
        R1["3 issues, 6h logged"]
        R2["8 stories, 21 points"]
    end

    M1 --> S1 --> R1
    M2 --> S2 --> R2

    style Morning fill:#e3f2fd,stroke:#1976d2
    style Skills1 fill:#fff3e0,stroke:#f57c00
    style Results1 fill:#e8f5e9,stroke:#388e3c
```

### Sprint Management

```mermaid
flowchart LR
    subgraph Planning["Sprint Planning"]
        P1["Create Sprint 43"]
        P2["Move top 10 stories<br/>to sprint"]
        P3["Start the sprint"]
    end

    subgraph Skills2["Skills Used"]
        S1["jira-agile<br/>create_sprint.py"]
        S2["jira-bulk<br/>bulk_move.py"]
        S3["jira-agile<br/>manage_sprint.py"]
    end

    subgraph Results2["Results"]
        R1["Sprint 43 created"]
        R2["10 stories moved<br/>34 points planned"]
        R3["Sprint active"]
    end

    P1 --> S1 --> R1
    P2 --> S2 --> R2
    P3 --> S3 --> R3

    style Planning fill:#e3f2fd,stroke:#1976d2
    style Skills2 fill:#fff3e0,stroke:#f57c00
    style Results2 fill:#e8f5e9,stroke:#388e3c
```

## Skill Quick Reference

| Natural Language | Skill | Script |
|-----------------|-------|--------|
| "Show my bugs" | jira-search | jql_search.py |
| "Create a story" | jira-issue | create_issue.py |
| "Move to Done" | jira-lifecycle | transition_issue.py |
| "What's blocking?" | jira-relationships | get_blockers.py |
| "Log 2 hours" | jira-time | log_work.py |
| "Create sprint" | jira-agile | create_sprint.py |
| "Bulk update" | jira-bulk | bulk_transition.py |
| "Add comment" | jira-collaborate | add_comment.py |
