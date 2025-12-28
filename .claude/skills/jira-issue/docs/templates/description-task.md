# Task Template

Use this template for technical work, infrastructure tasks, and internal improvements.

## Template

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

## Example

```markdown
## Objective
Configure Redis caching for user session data to reduce database load and improve response times by 50%.

## Requirements
- Redis instance must be configured with TLS encryption
- Session data expires after 24 hours of inactivity
- Failover to database if Redis unavailable
- Must support horizontal scaling (multiple app instances)

## Approach
1. Provision Redis cluster in AWS ElastiCache
2. Add redis-py client to application dependencies
3. Implement SessionStore abstraction layer
4. Add circuit breaker for Redis connection failures
5. Update deployment configuration with Redis endpoints

## Success Criteria
- [ ] Redis cluster provisioned and accessible from app servers
- [ ] Session read/write operations use Redis as primary store
- [ ] Failover to database works when Redis is unreachable
- [ ] Load test shows 50% reduction in database queries
- [ ] No session data loss during Redis restart

## Dependencies
- PROJ-100: AWS permissions for ElastiCache provisioning
- VPC peering configuration (handled by DevOps)
- Redis 7.0+ required for new stream features

## Resources
- AWS ElastiCache docs: https://docs.aws.amazon.com/elasticache/
- redis-py documentation: https://redis-py.readthedocs.io/
- Architecture diagram: [link to diagram]
```

## Task Categories

| Category | Description | Example |
|----------|-------------|---------|
| Infrastructure | Server, cloud, network setup | "Provision staging environment" |
| Configuration | Settings, parameters, env setup | "Configure CI/CD pipeline" |
| Refactoring | Code improvements, no new features | "Extract payment module" |
| Performance | Optimization, caching, tuning | "Add database indexes" |
| Security | Hardening, audits, fixes | "Update dependencies for CVE" |
| Documentation | Technical docs, runbooks | "Document API rate limits" |
| Research/Spike | Investigation with time-box | "Evaluate OAuth libraries" |

## Task vs Story

Tasks are appropriate when:
- Work is technical with no direct user visibility
- Outcome is infrastructure or tooling improvement
- Deliverable is internal capability
- Work enables future stories but isn't a story itself

## Spike Tasks

For research or investigation tasks:

```markdown
## Objective
Evaluate authentication libraries for potential migration from current solution.

## Time-Box
Maximum 2 days of investigation

## Questions to Answer
1. Which libraries support OAuth 2.1 and OpenID Connect?
2. What is the migration effort for each option?
3. Which has best community support and documentation?
4. What are the licensing implications?

## Deliverables
- [ ] Comparison matrix of 3-5 libraries
- [ ] Proof of concept with top recommendation
- [ ] Migration risk assessment
- [ ] Recommendation document with rationale

## Out of Scope
- Actual migration implementation
- Performance benchmarking
- Security audit
```
