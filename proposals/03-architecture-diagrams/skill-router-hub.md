# Skill Router Hub Diagram

## Usage

Embed this diagram in the main README to show how the JIRA Assistant routes requests to specialized skills.

## Mermaid Code

```mermaid
flowchart TD
    subgraph User["User Interface"]
        U["User Request"]
    end

    subgraph AI["AI Processing"]
        CC["Claude Code"]
        JA["jira-assistant<br/>Meta-Router"]
    end

    subgraph Core["Core Operations"]
        JI["jira-issue<br/>CRUD"]
        JL["jira-lifecycle<br/>Workflow"]
        JS["jira-search<br/>JQL & Filters"]
    end

    subgraph Collaboration["Collaboration"]
        JC["jira-collaborate<br/>Comments & Attachments"]
        JR["jira-relationships<br/>Links & Dependencies"]
    end

    subgraph Agile["Agile & Time"]
        JAG["jira-agile<br/>Sprints & Epics"]
        JT["jira-time<br/>Worklogs & Estimates"]
    end

    subgraph Scale["Scale & Automation"]
        JB["jira-bulk<br/>Batch Operations"]
        JD["jira-dev<br/>Git Integration"]
    end

    subgraph Enterprise["Enterprise"]
        JSM["jira-jsm<br/>Service Management"]
        JF["jira-fields<br/>Custom Fields"]
        JO["jira-ops<br/>Cache & Diagnostics"]
    end

    subgraph Shared["Shared Infrastructure"]
        SH["Shared Library<br/>Client, Config, Validators"]
    end

    subgraph External["External Services"]
        API["JIRA REST API"]
        JIRA[("JIRA Cloud")]
    end

    U --> CC
    CC --> JA

    JA -->|"Create bug"| JI
    JA -->|"Move to Done"| JL
    JA -->|"Find issues"| JS
    JA -->|"Add comment"| JC
    JA -->|"Link issues"| JR
    JA -->|"Sprint planning"| JAG
    JA -->|"Log time"| JT
    JA -->|"Bulk update"| JB
    JA -->|"Git branch"| JD
    JA -->|"Service request"| JSM
    JA -->|"Field discovery"| JF
    JA -->|"Cache warmup"| JO

    Core --> SH
    Collaboration --> SH
    Agile --> SH
    Scale --> SH
    Enterprise --> SH

    SH --> API
    API --> JIRA

    style U fill:#e1f5fe,stroke:#01579b
    style CC fill:#f3e5f5,stroke:#7b1fa2
    style JA fill:#fff3e0,stroke:#e65100
    style API fill:#e8f5e9,stroke:#2e7d32
    style JIRA fill:#e8f5e9,stroke:#2e7d32
    style SH fill:#fce4ec,stroke:#c2185b
```

## Compact Version (for narrow displays)

```mermaid
flowchart TD
    U["User Request"] --> CC["Claude Code"]
    CC --> JA["jira-assistant<br/>Meta-Router"]

    JA --> CORE["Core<br/>issue, lifecycle, search"]
    JA --> COLLAB["Collaboration<br/>collaborate, relationships"]
    JA --> AGILE["Agile<br/>agile, time"]
    JA --> SCALE["Scale<br/>bulk, dev"]
    JA --> ENT["Enterprise<br/>jsm, fields, ops"]

    CORE & COLLAB & AGILE & SCALE & ENT --> SH["Shared Library"]
    SH --> API["JIRA REST API"]
    API --> JIRA[("JIRA Cloud")]

    style U fill:#e1f5fe,stroke:#01579b
    style CC fill:#f3e5f5,stroke:#7b1fa2
    style JA fill:#fff3e0,stroke:#e65100
    style API fill:#e8f5e9,stroke:#2e7d32
    style JIRA fill:#e8f5e9,stroke:#2e7d32
```

## Skill Categories Reference

| Category | Skills | Purpose |
|----------|--------|---------|
| Core | jira-issue, jira-lifecycle, jira-search | Basic issue operations, workflow, queries |
| Collaboration | jira-collaborate, jira-relationships | Comments, attachments, links, dependencies |
| Agile | jira-agile, jira-time | Sprint planning, time tracking |
| Scale | jira-bulk, jira-dev | Batch operations, Git integration |
| Enterprise | jira-jsm, jira-fields, jira-ops | Service management, field discovery, caching |
