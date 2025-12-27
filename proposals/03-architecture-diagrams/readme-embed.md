# README Architecture Section

Copy the content below into your main README.md to add the architecture section.

---

## Architecture

### How It Works

The JIRA Assistant routes your natural language requests through specialized skills, each optimized for specific JIRA operations.

```mermaid
flowchart TD
    U["User Request"] --> CC["Claude Code"]
    CC --> JA["jira-assistant<br/>Meta-Router"]

    JA -->|"Create bug"| JI["jira-issue"]
    JA -->|"Move to Done"| JL["jira-lifecycle"]
    JA -->|"Find issues"| JS["jira-search"]
    JA -->|"Add comment"| JC["jira-collaborate"]
    JA -->|"Link issues"| JR["jira-relationships"]
    JA -->|"Sprint planning"| JAG["jira-agile"]
    JA -->|"Log time"| JT["jira-time"]
    JA -->|"Bulk update"| JB["jira-bulk"]
    JA -->|"Git branch"| JD["jira-dev"]
    JA -->|"Service request"| JSM["jira-jsm"]
    JA -->|"Field discovery"| JF["jira-fields"]
    JA -->|"Cache warmup"| JO["jira-ops"]

    JI & JL & JS & JC & JR & JAG & JT & JB & JD & JSM & JF & JO --> SH["Shared Library"]
    SH --> API["JIRA REST API"]
    API --> JIRA[("JIRA Cloud")]

    style U fill:#e1f5fe,stroke:#01579b
    style CC fill:#f3e5f5,stroke:#7b1fa2
    style JA fill:#fff3e0,stroke:#e65100
    style SH fill:#fce4ec,stroke:#c2185b
    style API fill:#e8f5e9,stroke:#2e7d32
    style JIRA fill:#e8f5e9,stroke:#2e7d32
```

### Request Flow Example

See how a natural language request flows through the system:

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant C as Claude Code
    participant R as Router
    participant S as Skill
    participant A as JIRA API

    U->>C: "Create a high priority bug<br/>for login failing on mobile"
    Note over C: Understands intent
    C->>R: Route to jira-issue
    R->>S: create_issue.py --type Bug
    S->>A: POST /rest/api/3/issue
    A-->>S: PROJ-456 created
    S-->>C: Success + details
    C-->>U: Created PROJ-456<br/>[High Priority Bug]
```

### Skill Categories

| Category | Skills | Purpose |
|----------|--------|---------|
| **Core** | jira-issue, jira-lifecycle, jira-search | Issue CRUD, workflow transitions, JQL queries |
| **Collaboration** | jira-collaborate, jira-relationships | Comments, attachments, issue links, dependencies |
| **Agile** | jira-agile, jira-time | Sprint planning, epic management, time tracking |
| **Scale** | jira-bulk, jira-dev | Batch operations, Git branch integration |
| **Enterprise** | jira-jsm, jira-fields, jira-ops | Service management, field discovery, caching |

### Shared Infrastructure

All skills share a common library providing:

- **JIRA Client**: HTTP client with retry logic (3 attempts, exponential backoff)
- **Config Manager**: Multi-source configuration (env vars, settings files, profiles)
- **Error Handler**: HTTP status code mapping to actionable error messages
- **Validators**: Input validation for issue keys, URLs, and data formats
- **Formatters**: Table, JSON, and CSV output formatting
