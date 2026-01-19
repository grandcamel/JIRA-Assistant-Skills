# JIRA Lifecycle Management Best Practices

**Use this guide when:** Looking for comprehensive lifecycle management guidance.

This content has been organized into focused guides for different audiences:

---

## Guides by Role

### For Workflow Designers and JIRA Admins

**[WORKFLOW_DESIGN.md](WORKFLOW_DESIGN.md)** - Designing and improving JIRA workflows

Topics covered:
- Design principles (simplicity, standardization)
- Status naming conventions
- Transition strategy
- Conditions, validators, and post-functions
- Workflow patterns (simple, development, service desk, incident)
- Testing and rollout strategies

### For Developers and Team Leads

**[DAILY_OPERATIONS.md](DAILY_OPERATIONS.md)** - Day-to-day lifecycle operations

Topics covered:
- Assignment best practices
- Version management
- Component organization
- WIP (Work In Progress) limits
- Resolution discipline
- Common pitfalls and red flags
- Quick reference card

---

## Quick Reference

### Essential Transition Commands

```bash
python get_transitions.py PROJ-123
python transition_issue.py PROJ-123 --name "In Progress"
python resolve_issue.py PROJ-123 --resolution "Fixed"
python reopen_issue.py PROJ-123
```

### Essential Assignment Commands

```bash
python assign_issue.py PROJ-123 --user john@example.com
python assign_issue.py PROJ-123 --self
python assign_issue.py PROJ-123 --unassign
```

### Essential Version Commands

```bash
python create_version.py PROJ --name "v2.0.0" --release-date 2025-03-31
python get_versions.py PROJ --format table
python release_version.py PROJ --name "v2.0.0" --date 2025-03-31
python archive_version.py PROJ --name "v1.0.0"
```

### Essential Component Commands

```bash
python create_component.py PROJ --name "API" --lead john@example.com
python get_components.py PROJ --format table
python delete_component.py --id 10000 --move-to 10001
```

---

## Workflow Patterns

Detailed workflow patterns are available in [references/patterns/](../references/patterns/):

| Pattern | File | Best For |
|---------|------|----------|
| Standard (3 status) | [standard_workflow.md](../references/patterns/standard_workflow.md) | Simple projects |
| Software Development | [software_dev_workflow.md](../references/patterns/software_dev_workflow.md) | Engineering teams |
| Service Request | [jsm_request_workflow.md](../references/patterns/jsm_request_workflow.md) | Customer support |
| Incident Management | [incident_workflow.md](../references/patterns/incident_workflow.md) | SRE, DevOps |

---

## Health Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| In Progress per person | 1-2 | 3-4 | 5+ |
| Time in "In Progress" | 1-3 days | 4-7 days | 8+ days |
| Unreleased versions | 2-4 | 5-10 | 10+ |
| Issues without components | <5% | 5-20% | 20%+ |
| Unassigned "In Progress" | 0% | 1-5% | 5%+ |

---

## Sources

- [Idalko: A Guide to Jira Workflow Best Practices](https://idalko.com/blog/jira-workflow-best-practices)
- [Unito: The Ultimate Guide to Efficiency: Jira Best Practices in 2025](https://unito.io/blog/jira-efficiency-best-practices/)
- [HeroCoders: Understanding Jira Issue Statuses](https://www.herocoders.com/blog/understanding-jira-issue-statuses)
- [Atlassian: Learn versions with Jira Tutorial](https://www.atlassian.com/agile/tutorials/versions)
- [Apwide: Release Management in Jira 2025](https://www.apwide.com/release-management-in-jira/)
- [DevSamurai: Version and Release Management in Jira](https://www.devsamurai.com/en/version-and-release-management-in-jira/)
- [Atlassian Support: What are Jira components?](https://support.atlassian.com/jira-software-cloud/docs/what-are-jira-components/)
- [Atlassian Community: Jira Essentials: Adding work in progress limits](https://community.atlassian.com/t5/Jira-articles/Jira-Essentials-Adding-work-in-progress-limits/ba-p/1621358)

---

*Last updated: December 2025*
