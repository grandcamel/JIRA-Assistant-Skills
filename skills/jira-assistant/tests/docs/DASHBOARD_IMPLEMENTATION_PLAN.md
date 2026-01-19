# Dashboard Enhancement Implementation Plan

**Document Version:** 1.0
**Date:** 2026-01-01
**Author:** Claude Code Analysis
**Status:** Draft - Pending Approval
**Related:** [DASHBOARD_GAP_ANALYSIS.md](./DASHBOARD_GAP_ANALYSIS.md)

---

## Executive Summary

This document outlines a 4-phase implementation plan to address the gaps identified in the Dashboard Gap Analysis. The plan spans approximately 12 weeks and prioritizes high-impact, cross-cutting improvements first.

**Total Estimated Effort:** 45-60 story points
**Phases:** 4
**Key Deliverables:**
- Extended OTel instrumentation (retry counts, confidence scores, token breakdown)
- Enhanced dashboards for all 4 audiences
- New Experiment Dashboard for A/B testing
- Grafana alerting rules
- Change impact correlation system

---

## Phase Overview

| Phase | Name | Duration | Focus | Key Outcomes |
|-------|------|----------|-------|--------------|
| 1 | Foundation & Critical Gaps | Week 1-2 | OTel instrumentation, SKILL.md correlation | Extended metrics, change tracking |
| 2 | High-Priority Dashboard Enhancements | Week 3-5 | HIGH priority items for all audiences | Flaky detection, API health, A/B prep |
| 3 | Medium-Priority & New Dashboards | Week 6-9 | MEDIUM priority, Experiment Dashboard | Full experiment support, cost analytics |
| 4 | Polish & Low-Priority | Week 10-12 | LOW priority, custom visualizations | AI summaries, advanced visualizations |

---

## Clarifying Questions (Blocking Phase 1)

Before starting Phase 1, answers are needed for:

### Must Answer Before Phase 1

| # | Question | Options | Default if No Answer | Impact |
|---|----------|---------|---------------------|--------|
| Q1 | What is the SLO for routing accuracy? | 80%, 85%, 90%, 95% | 85% | Affects threshold colors in all dashboards |
| Q2 | What is the daily cost budget? | $10, $25, $50, $100 | $25 | Affects cost alerting thresholds |
| Q3 | Should alerts go to Slack, PagerDuty, or email? | Slack channel, PagerDuty, Email, All | Slack | Affects alerting configuration |
| Q4 | Is there a git webhook available for SKILL.md changes? | Yes (URL), No | No (use polling) | Affects change correlation architecture |
| Q5 | What Prometheus retention period is available? | 7d, 15d, 30d, 90d | 15d | Affects historical comparison queries |

### Can Answer During Phase 1-2

| # | Question | Options | Default if No Answer |
|---|----------|---------|---------------------|
| Q6 | Do you want confidence scores from Claude? | Yes, No | No (skip implementation) |
| Q7 | Should token costs use actual pricing or estimates? | Actual API pricing, Estimated | Estimated |
| Q8 | Is there a CI/CD quality gate requirement? | Yes (details), No | No |
| Q9 | Multi-environment support needed? | Yes, No | No |
| Q10 | Historical baseline snapshots needed? | Yes, No | Yes (1 per release) |

---

## Phase 1: Foundation & Critical Gaps (Week 1-2)

### Objectives
1. Extend OTel instrumentation to capture missing data
2. Implement SKILL.md change correlation (CRITICAL gap)
3. Add retry count and API health tracking (HIGH priority for SRE)
4. Create foundation for flaky test detection

### Phase 1 Task List

#### 1.1 OTel Instrumentation Extensions

| Task ID | Task | File(s) | Effort | Dependencies |
|---------|------|---------|--------|--------------|
| P1-01 | Add retry count to span attributes | `otel_metrics.py` | 2h | None |
| P1-02 | Add API latency tracking (time between retries) | `otel_metrics.py` | 3h | P1-01 |
| P1-03 | Add 429/5xx error type breakdown in metrics | `otel_metrics.py` | 2h | None |
| P1-04 | Add token count breakdown (input/output separate) | `otel_metrics.py` | 2h | None |
| P1-05 | Add worker ID to all test spans | `otel_metrics.py`, `conftest.py` | 2h | None |
| P1-06 | Create `routing_test_retries_total` counter metric | `otel_metrics.py` | 1h | P1-01 |
| P1-07 | Create `routing_test_api_latency_seconds` histogram | `otel_metrics.py` | 2h | P1-02 |

**Subtotal: 14 hours (3-4 story points)**

#### 1.2 SKILL.md Change Correlation System (CRITICAL)

| Task ID | Task | File(s) | Effort | Dependencies |
|---------|------|---------|--------|--------------|
| P1-08 | Create `skill_change_tracker.py` module | `skill_change_tracker.py` (new) | 4h | None |
| P1-09 | Implement git diff parsing for SKILL.md files | `skill_change_tracker.py` | 3h | P1-08 |
| P1-10 | Add `skill.md.hash` attribute to spans | `otel_metrics.py` | 1h | P1-08 |
| P1-11 | Create `skill_change_events` table schema | `skill_change_tracker.py` | 2h | P1-08 |
| P1-12 | Implement change event recording on test run | `conftest.py` | 2h | P1-10, P1-11 |
| P1-13 | Create Prometheus metrics for skill changes | `skill_change_tracker.py` | 2h | P1-11 |
| P1-14 | Add "Change Impact" panel to skills-engineer-ab.json | `skills-engineer-ab.json` | 3h | P1-13 |
| P1-15 | Add "Before/After Comparison" panel | `skills-engineer-ab.json` | 2h | P1-14 |

**Subtotal: 19 hours (5 story points)**

#### 1.3 Flaky Test Detection Foundation

| Task ID | Task | File(s) | Effort | Dependencies |
|---------|------|---------|--------|--------------|
| P1-16 | Add test run sequence number to spans | `otel_metrics.py` | 1h | None |
| P1-17 | Create recording rule for test pass rate over 7d | `prometheus-rules.yaml` (new) | 2h | None |
| P1-18 | Create "Flaky Tests" table query | PromQL query | 2h | P1-17 |
| P1-19 | Add "Flaky Tests" panel to qa-test-engineer.json | `qa-test-engineer.json` | 2h | P1-18 |

**Subtotal: 7 hours (2 story points)**

#### 1.4 API Health Panels (SRE)

| Task ID | Task | File(s) | Effort | Dependencies |
|---------|------|---------|--------|--------------|
| P1-20 | Add "API Retry Rate" panel | `sre-operations.json` | 2h | P1-06 |
| P1-21 | Add "API Latency Percentiles" panel | `sre-operations.json` | 2h | P1-07 |
| P1-22 | Add "429 Error Rate" panel | `sre-operations.json` | 2h | P1-03 |
| P1-23 | Add "API Health" row grouping | `sre-operations.json` | 1h | P1-20 |

**Subtotal: 7 hours (2 story points)**

#### 1.5 Executive Trend Deltas

| Task ID | Task | File(s) | Effort | Dependencies |
|---------|------|---------|--------|--------------|
| P1-24 | Create "WoW Accuracy Delta" stat panel | `executive-summary.json` | 3h | None |
| P1-25 | Add trend arrow indicators | `executive-summary.json` | 2h | P1-24 |
| P1-26 | Create "Monthly Projected Cost" panel | `executive-summary.json` | 2h | None |

**Subtotal: 7 hours (2 story points)**

---

### Phase 1 Deliverables Checklist

```markdown
## Phase 1 Completion Criteria

### OTel Instrumentation
- [ ] P1-01: Retry count in span attributes
- [ ] P1-02: API latency tracking
- [ ] P1-03: 429/5xx error breakdown
- [ ] P1-04: Token count breakdown
- [ ] P1-05: Worker ID in spans
- [ ] P1-06: routing_test_retries_total metric
- [ ] P1-07: routing_test_api_latency_seconds histogram

### SKILL.md Change Correlation
- [ ] P1-08: skill_change_tracker.py created
- [ ] P1-09: Git diff parsing working
- [ ] P1-10: skill.md.hash in spans
- [ ] P1-11: Change events schema defined
- [ ] P1-12: Change event recording on test run
- [ ] P1-13: Prometheus metrics for changes
- [ ] P1-14: "Change Impact" panel added
- [ ] P1-15: "Before/After Comparison" panel added

### Flaky Test Detection
- [ ] P1-16: Run sequence number in spans
- [ ] P1-17: Recording rule created
- [ ] P1-18: Flaky test query working
- [ ] P1-19: "Flaky Tests" panel in QA dashboard

### API Health (SRE)
- [ ] P1-20: "API Retry Rate" panel
- [ ] P1-21: "API Latency Percentiles" panel
- [ ] P1-22: "429 Error Rate" panel
- [ ] P1-23: "API Health" row grouping

### Executive Trends
- [ ] P1-24: "WoW Accuracy Delta" panel
- [ ] P1-25: Trend arrow indicators
- [ ] P1-26: "Monthly Projected Cost" panel

### Testing & Documentation
- [ ] All new metrics visible in Prometheus
- [ ] All new panels rendering data
- [ ] Updated OTel documentation
- [ ] Phase 1 retrospective completed
```

---

### Phase 1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Test Execution Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ pytest       │───▶│ conftest.py  │───▶│ otel_metrics.py  │  │
│  │ test_routing │    │ (hooks)      │    │ (instrumentation)│  │
│  └──────────────┘    └──────────────┘    └────────┬─────────┘  │
│                             │                      │             │
│                             ▼                      ▼             │
│                   ┌──────────────────┐   ┌────────────────────┐ │
│                   │skill_change_     │   │ Extended Spans:    │ │
│                   │tracker.py (NEW)  │   │ - retry_count      │ │
│                   │                  │   │ - api_latency      │ │
│                   │ - git diff parse │   │ - token_input      │ │
│                   │ - change events  │   │ - token_output     │ │
│                   │ - skill.md.hash  │   │ - worker_id        │ │
│                   └────────┬─────────┘   │ - error_type       │ │
│                            │             └─────────┬──────────┘ │
│                            ▼                       ▼             │
│                   ┌──────────────────────────────────────────┐  │
│                   │           OTel Collector                  │  │
│                   │  ┌─────────────┐  ┌─────────────────┐    │  │
│                   │  │ Prometheus  │  │ Tempo           │    │  │
│                   │  │ (metrics)   │  │ (traces)        │    │  │
│                   │  └──────┬──────┘  └────────┬────────┘    │  │
│                   └─────────┼──────────────────┼─────────────┘  │
│                             │                  │                 │
│                             ▼                  ▼                 │
│                   ┌──────────────────────────────────────────┐  │
│                   │              Grafana                      │  │
│                   │  ┌─────────┐ ┌─────────┐ ┌─────────────┐ │  │
│                   │  │Executive│ │QA Eng   │ │Skills Eng   │ │  │
│                   │  │(trends) │ │(flaky)  │ │(change corr)│ │  │
│                   │  └─────────┘ └─────────┘ └─────────────┘ │  │
│                   └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 2: High-Priority Dashboard Enhancements (Week 3-5)

### Objectives
1. Complete HIGH priority items for all audiences
2. Add Grafana alerting rules
3. Prepare foundation for Experiment Dashboard
4. Implement worker utilization tracking

### Phase 2 Task Summary

| Category | Task Count | Effort |
|----------|------------|--------|
| QA Engineer Enhancements | 8 tasks | 16h |
| Skills Engineer A/B Prep | 6 tasks | 14h |
| SRE Worker Utilization | 5 tasks | 10h |
| Alerting Rules | 6 tasks | 8h |
| Executive Enhancements | 4 tasks | 8h |

**Phase 2 Total: ~56 hours (14-15 story points)**

### Key Deliverables
- Disambiguation validation panel (QA)
- Test stability scores (QA)
- A/B experiment isolation foundation (Skills)
- Worker utilization metrics (SRE)
- Cost and error rate alerts (SRE)
- Release comparison panel (Executive)

---

## Phase 3: Medium-Priority & New Dashboards (Week 6-9)

### Objectives
1. Build complete Experiment Dashboard
2. Implement MEDIUM priority items
3. Add semantic similarity clustering
4. Implement token economics panels

### Phase 3 Task Summary

| Category | Task Count | Effort |
|----------|------------|--------|
| Experiment Dashboard | 12 tasks | 30h |
| QA Medium Priority | 6 tasks | 14h |
| Skills Medium Priority | 5 tasks | 12h |
| SRE Medium Priority | 6 tasks | 14h |
| Executive Medium Priority | 3 tasks | 6h |

**Phase 3 Total: ~76 hours (19-20 story points)**

### Key Deliverables
- Complete Experiment Dashboard with statistical significance
- Input pattern analysis (QA)
- Skill description diff viewer (Skills)
- Token usage breakdown (SRE)
- Cost anomaly detection (SRE)
- Budget burn rate tracking (Executive)

---

## Phase 4: Polish & Low-Priority (Week 10-12)

### Objectives
1. Implement LOW priority items
2. Add custom visualizations
3. AI-generated summaries
4. Performance optimization

### Phase 4 Task Summary

| Category | Task Count | Effort |
|----------|------------|--------|
| Custom Visualizations | 4 tasks | 16h |
| AI Summaries | 3 tasks | 12h |
| Low Priority Items | 8 tasks | 16h |
| Performance & Cleanup | 4 tasks | 8h |

**Phase 4 Total: ~52 hours (13 story points)**

### Key Deliverables
- Word cloud for failed input patterns
- Response diff viewer
- AI-generated executive summaries
- Skills coverage treemap
- Collector resource monitoring
- Documentation updates

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Prometheus retention too short for trend analysis | Medium | High | Query Q5 early; adjust queries if needed |
| SKILL.md change detection misses commits | Low | High | Implement webhook fallback; manual trigger |
| Statistical significance calculations wrong | Medium | Medium | Use well-tested libraries (scipy); peer review |
| Dashboard performance degrades with more panels | Medium | Medium | Use recording rules; lazy loading |
| OTel collector overloaded | Low | High | Monitor collector metrics; scale if needed |

---

## Success Metrics

| Metric | Phase 1 Target | Phase 2 Target | Phase 4 Target |
|--------|---------------|---------------|----------------|
| Dashboard panel count | +15 panels | +30 panels | +50 panels |
| OTel attributes tracked | +7 attributes | +12 attributes | +15 attributes |
| Prometheus recording rules | 2 rules | 5 rules | 8 rules |
| Grafana alerts configured | 0 | 6 alerts | 10 alerts |
| Documentation coverage | 60% | 80% | 100% |

---

## Appendix A: File Change Summary

### New Files (Phase 1)
```
tests/
├── skill_change_tracker.py     # SKILL.md change correlation
└── prometheus-rules.yaml       # Recording rules for flaky detection
```

### Modified Files (Phase 1)
```
tests/
├── otel_metrics.py             # Extended instrumentation
├── conftest.py                 # Change tracking hooks
└── dashboards/
    ├── executive-summary.json  # Trend deltas
    ├── qa-test-engineer.json   # Flaky tests panel
    ├── skills-engineer-ab.json # Change correlation panels
    └── sre-operations.json     # API health panels
```

### New Files (Phase 3)
```
tests/
└── dashboards/
    └── experiment-dashboard.json  # New A/B testing dashboard
```

---

## Appendix B: Prometheus Recording Rules (Phase 1)

```yaml
# prometheus-rules.yaml
groups:
  - name: routing_test_rules
    interval: 1m
    rules:
      # Test pass rate over 7 days per test
      - record: routing_test:pass_rate_7d
        expr: |
          sum by (span_name) (
            increase(traces_spanmetrics_calls_total{
              service="jira-assistant-routing-tests",
              status_code="STATUS_CODE_OK",
              span_name=~"routing_test_TC.*"
            }[7d])
          ) /
          sum by (span_name) (
            increase(traces_spanmetrics_calls_total{
              service="jira-assistant-routing-tests",
              span_name=~"routing_test_TC.*"
            }[7d])
          )

      # Flaky tests (30-70% pass rate)
      - record: routing_test:flaky_tests
        expr: |
          routing_test:pass_rate_7d > 0.3
          and routing_test:pass_rate_7d < 0.7
```

---

## Appendix C: Grafana Alert Rules (Phase 2)

```yaml
# grafana-alerts.yaml (example)
groups:
  - name: routing_test_alerts
    rules:
      - alert: RoutingAccuracyBelowSLO
        expr: |
          (sum(traces_spanmetrics_calls_total{status_code="STATUS_CODE_OK"}) /
           sum(traces_spanmetrics_calls_total)) * 100 < 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Routing accuracy below 85% SLO"

      - alert: DailyCostExceeded
        expr: |
          sum(increase(routing_test_cost_usd_sum[24h])) > 25
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Daily test cost exceeded $25"

      - alert: HighAPIRetryRate
        expr: |
          sum(rate(routing_test_retries_total[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API retry rate detected"
```

---

## Approval & Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Tech Lead | | | |
| QA Lead | | | |
| SRE Lead | | | |

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-01 | Claude Code | Initial draft |
