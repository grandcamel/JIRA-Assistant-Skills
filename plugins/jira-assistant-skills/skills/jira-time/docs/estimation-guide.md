# Estimation and Planning Guide

Comprehensive guidance on JIRA time fields, estimation approaches, accuracy metrics, and continuous improvement strategies.

---

## Use this guide if you...

- Need to understand JIRA's time tracking field relationships
- Want to improve estimation accuracy for your team
- Are choosing between story points, hours, or T-shirt sizing
- Need buffer guidelines for different task types
- Want to measure and improve estimate accuracy over time

For daily logging habits, see [IC Time Logging Guide](ic-time-logging.md).
For team policies, see [Team Policies](team-policies.md).

---

## Table of Contents

1. [Understanding JIRA Time Fields](#understanding-jira-time-fields)
2. [Estimation Approaches](#estimation-approaches)
3. [Setting Realistic Estimates](#setting-realistic-estimates)
4. [Estimate Adjustment Strategies](#estimate-adjustment-strategies)
5. [Measuring Accuracy](#measuring-accuracy)
6. [Continuous Improvement](#continuous-improvement)

---

## Understanding JIRA Time Fields

JIRA uses three interconnected time tracking fields:

| Field | Purpose | When to Set | Auto-Updated |
|-------|---------|-------------|--------------|
| **Original Estimate** | Initial prediction of total effort | At issue creation or planning | No |
| **Remaining Estimate** | Time left to complete work | Updated as work progresses | Optional |
| **Time Spent** | Cumulative time logged via worklogs | When logging work | Yes |

**Relationship:**
```
Progress = Time Spent / Original Estimate
Projected Total = Time Spent + Remaining Estimate
Variance = Projected Total - Original Estimate
```

**Setting estimates:**
```bash
# Set original estimate
python set_estimate.py PROJ-123 --original "2d"

# Set remaining estimate
python set_estimate.py PROJ-123 --remaining "1d 4h"

# Set both together (recommended due to JRACLOUD-67539)
python set_estimate.py PROJ-123 --original "2d" --remaining "1d 4h"
```

---

## Estimation Approaches

### 1. Bottom-Up Estimation (Recommended)

**Best for:** Detailed planning, high accuracy requirements

**Process:**
1. Break down epics into stories
2. Break down stories into subtasks
3. Estimate only subtasks (in hours)
4. Sum subtasks for story estimate
5. Sum stories for epic estimate

**Example:**
```
Epic: User Authentication (Total: 5d)
 -- Story: Login Form (2d)
 |   -- Subtask: Create UI component (4h)
 |   -- Subtask: Add validation logic (3h)
 |   -- Subtask: Write unit tests (2h)
 |   -- Subtask: Integration testing (3h)
 -- Story: Password Reset (2d)
 |   -- [Subtasks...]
 -- Story: OAuth Integration (1d)
     -- [Subtasks...]
```

**Benefits:**
- More accurate (smaller units easier to estimate)
- Clear breakdown for developers
- Easy to track progress

### 2. Story Point to Hours Conversion

**Best for:** Teams using Agile story points but needing time tracking for billing

**Common conversion factors:**
- 1 point = 2-4 hours (team dependent)
- 1 point = 0.5 days (common)
- 1 point = 1 day (conservative)

**Example:**
```bash
# If your team's velocity is 40 points/sprint (2 weeks)
# And team capacity is 200 hours/sprint (5 people x 40h)
# Then: 1 point = 5 hours

python set_estimate.py PROJ-123 --original "2d"  # For a 3-point story
```

**Important:** Track actual conversion over time and adjust based on historical data.

### 3. T-Shirt Sizing with Hours

Map relative sizes to time ranges for quick estimation:

| Size | Story Points | Time Range | Use Case |
|------|--------------|------------|----------|
| XS | 1 | 1-2h | Trivial fix, config change |
| S | 2 | 2-4h | Small bug, simple feature |
| M | 3 | 4h-1d | Standard story |
| L | 5 | 1-2d | Complex feature |
| XL | 8 | 2-3d | Very large story (consider splitting) |
| XXL | 13+ | 1w+ | Too large - must split |

---

## Setting Realistic Estimates

### Do

- Reference historical data from similar completed issues
- Include time for testing, code review, and documentation
- Account for uncertainty (add buffer for unknowns)
- Use team's past velocity for story-level estimates
- Consider team member experience level

### Don't

- Use wishful thinking ("best case scenario")
- Forget non-coding activities (meetings, email, reviews)
- Estimate based on perfect conditions
- Ignore complexity multipliers (legacy code, dependencies)
- Commit to estimates under pressure without analysis

### Buffer Guidelines

| Scenario | Buffer | Rationale |
|----------|--------|-----------|
| Known implementation | +10% | Normal variance |
| New technology/library | +30% | Learning curve, unexpected issues |
| Unclear requirements | +50% | Likely scope changes |
| Multiple dependencies | +25% | Coordination overhead |
| Legacy code refactoring | +40% | Hidden complexity |

**Example:**
```bash
# Task estimate: 8h for new feature using unfamiliar library
# Buffer: +30% for new technology
# Final estimate: 8h * 1.3 = 10.4h -> round to 1d 4h

python set_estimate.py PROJ-123 --original "1d 4h"
```

---

## Estimate Adjustment Strategies

When logging time, control how JIRA updates the remaining estimate:

| Mode | Behavior | Use When | Command |
|------|----------|----------|---------|
| `auto` | Reduces remaining by time logged | Default for most workflows | `--adjust-estimate auto` |
| `leave` | Doesn't change remaining | Logging time outside issue scope | `--adjust-estimate leave` |
| `new` | Sets remaining to new value | Re-estimating after progress review | `--adjust-estimate new --new-estimate 4h` |
| `manual` | Reduces remaining by specified amount | Custom adjustment needed | `--adjust-estimate manual --reduce-by 1h` |

**Examples:**
```bash
# Auto-adjust (default) - logged 2h, remaining decreases by 2h
python add_worklog.py PROJ-123 --time 2h

# Leave unchanged - time logged but estimate stays same
python add_worklog.py PROJ-123 --time 2h --adjust-estimate leave

# Set new remaining estimate
python add_worklog.py PROJ-123 --time 2h \
  --adjust-estimate new --new-estimate 4h

# Reduce by specific amount
python add_worklog.py PROJ-123 --time 2h \
  --adjust-estimate manual --reduce-by 1h
```

**Known Issue (JRACLOUD-67539):** JIRA Cloud has a bug where estimates may not update correctly. Workaround:
```bash
# Set both estimates together
python set_estimate.py PROJ-123 --original "2d" --remaining "1d 4h"
```

---

## Measuring Accuracy

### Variance Analysis

```bash
# Export issues with time tracking
python jql_search.py \
  "project = PROJ AND originalEstimate IS NOT EMPTY AND status = Done" \
  --output json > completed-issues.json

# Calculate variance in spreadsheet:
# Variance = (Time Spent - Original Estimate) / Original Estimate
# Accuracy = 1 - ABS(Variance)
```

**Acceptable variance ranges:**

| Task Size | Acceptable Variance |
|-----------|---------------------|
| Small tasks (<4h) | +/- 50% |
| Medium tasks (4h-2d) | +/- 30% |
| Large tasks (>2d) | +/- 20% |

### Team Accuracy Metrics

```jql
# Issues with accurate estimates (within 20%)
originalEstimate IS NOT EMPTY
AND timespent >= originalEstimate * 0.8
AND timespent <= originalEstimate * 1.2
```

**Target metrics by team maturity:**

| Team Level | Accuracy within +/-30% | Accuracy within +/-20% |
|------------|------------------------|------------------------|
| New team | 50% | 30% |
| Mature team | 70% | 50% |
| Expert team | 85% | 70% |

### Red Flags to Monitor

```jql
# Massive variance (>300%)
originalEstimate IS NOT EMPTY
AND timespent > originalEstimate * 3

# Issues with time logged but no estimate
timespent > 0 AND originalEstimate IS EMPTY

# Issues with estimate but no time logged (completed)
originalEstimate IS NOT EMPTY AND timespent IS EMPTY
AND status = Done
```

---

## Continuous Improvement

### Weekly Estimate Review

```bash
# Find issues with significant variance
python jql_search.py \
  "project = PROJ AND originalEstimate IS NOT EMPTY \
   AND (timespent > originalEstimate * 1.5 OR timespent < originalEstimate * 0.5)"
```

**Analysis questions:**
- Which types of tasks are consistently over/under estimated?
- What patterns emerge from high-variance issues?
- Are buffer guidelines adequate?

### Monthly Retrospective Questions

1. What types of tasks were most over-estimated?
2. What types were most under-estimated?
3. What interruptions/overhead were forgotten?
4. How can we improve estimate accuracy?
5. What estimation friction exists?

### Action Items Template

```markdown
# Estimation Improvements
- Add 30% buffer for tasks touching legacy code
- Create "meeting overhead" issues for all sprints
- Switch to 2-hour minimum estimates (not 30-minute)
- Pair on estimation for complex tasks
- Include testing time in development estimates
```

---

## Estimation Cheat Sheet

| Task Type | Typical Range | Example |
|-----------|---------------|---------|
| Trivial fix | 15m - 1h | Typo, config change |
| Small bug | 1h - 4h | Simple logic error |
| Medium story | 4h - 1d | Standard feature |
| Large story | 1d - 3d | Complex feature |
| Epic | 1w - 1 month | Multiple related features |

**Buffers quick reference:**
- Known work: +10%
- New technology: +30%
- Unclear requirements: +50%
- Legacy code: +40%
- External dependencies: +25%

---

## Related Guides

- [IC Time Logging Guide](ic-time-logging.md) - Daily logging habits and templates
- [Team Policies](team-policies.md) - Organizational time tracking requirements
- [Reporting Guide](reporting-guide.md) - Time-based reports and analytics
- [Quick Reference: Time Format](reference/time-format-quick-ref.md) - Time format syntax

---

**Back to:** [SKILL.md](../SKILL.md) | [Best Practices Index](BEST_PRACTICES.md)
